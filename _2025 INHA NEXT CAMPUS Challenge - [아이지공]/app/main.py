# app/main.py
import os
from datetime import datetime
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

from fastapi import FastAPI, Depends, Form, Request, status, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

from sqlalchemy.orm import Session as SASession
from sqlalchemy import select

from .models import User
from .auth import (
    hash_password,
    verify_password,
    login_user,
    logout_user,
    current_user_id,
)
from app.api_subjects import router as subjects_router
from app.db_bridge import get_db
from app.db.session import engine
from app.db.base import Base
from app.db.models.subject_pdf import SubjectPdf
from app.db.models.department_pdf import DepartmentPdf
from sqlmodel import SQLModel
import app.models as _models
import app.db.models  # noqa: F401 - 모든 모델을 로드하기 위해

from . import algorithm
from . import algorithm as algo  # planner 상수 로직용
from sqlmodel import Session
from app.data.majors import FACULTIES, MAJORS  # 추가
from app.utils.recommendation import recommend as ai_recommend
from app.db.models.subject_summary import SubjectSummary

get_session = get_db  # get_session Namerror 방지

# ---------------- App / Static / Templates ----------------
app = FastAPI(title="Timetable Recommender")
app.add_middleware(
    SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-secret-change")
)

app.include_router(subjects_router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Export directory for subject summaries
export_dir = Path(BASE_DIR).parent / "exports"
export_dir.mkdir(parents=True, exist_ok=True)  # 디렉토리가 없으면 자동 생성
app.mount("/exports", StaticFiles(directory=str(export_dir)), name="exports")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.globals["now"] = datetime.now
templates.env.globals["FACULTIES"] = FACULTIES  # 추가


@app.on_event("startup")
def _create_tables():
    # 모델이 로드된 상태에서 테이블 생성(이미 있으면 skip)
    # SQLModel 기반 모델 (User 등)
    SQLModel.metadata.create_all(engine)
    # SQLAlchemy Base 기반 모델 (Subject, CommonSubject, FavoriteLecture 등)
    Base.metadata.create_all(engine)


# ---------------- Helpers ----------------
def get_current_user(request: Request, db: SASession) -> Optional[User]:
    s_id = current_user_id(request)
    if not s_id:
        return None
    return db.execute(select(User).where(User.student_id == s_id)).scalars().first()


# ---------------- Pages ----------------
@app.get("/")
def home(request: Request, db: SASession = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})


# Signup
@app.get("/signup")
def signup_get(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        {"request": request, "errors": [], "FACULTIES": FACULTIES},
    )


@app.post("/signup")
def signup_post(
    request: Request,
    name: str = Form(...),
    student_id: str = Form(...),  # ✅ 문자열로 받고
    password: str = Form(...),
    confirm_password: str = Form(...),
    faculty: Optional[str] = Form(None),  # 추가
    major: Optional[str] = Form(None),  # 추가
    db: SASession = Depends(get_db),
):
    errors = []

    if len(student_id) != 8 or not student_id.isdigit():  # ✅ 길이/숫자 체크
        errors.append("올바른 학번을 입력해주세요 (숫자 8자리).")

    if password != confirm_password:
        errors.append("비밀번호가 일치하지 않습니다.")
    if len(password) < 4:
        errors.append("비밀번호는 4자 이상이어야 합니다.")

    # faculty/major 검증 추가
    if faculty is not None:
        if faculty not in FACULTIES:
            errors.append("단과대 선택이 올바르지 않습니다.")
        if major and major not in FACULTIES[faculty]:
            errors.append("전공 선택이 올바르지 않습니다.")

    exists = (
        db.execute(select(User).where(User.student_id == int(student_id)))
        .scalars()
        .first()
    )

    if exists:
        errors.append("이미 가입된 학번입니다.")

    if errors:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "errors": errors,
                "name": name,
                "student_id": student_id,
                "faculty": faculty,
                "major": major,
                "FACULTIES": FACULTIES,
            },
            status_code=400,
        )

    user = User(
        student_id=student_id,
        name=name,
        major=major,  # 추가
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()

    login_user(request, student_id)
    return RedirectResponse(url="/", status_code=303)


# Login
@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "errors": []})


@app.post("/login")
def login_post(
    request: Request,
    student_id: str = Form(...),  # ✅ 문자열로
    password: str = Form(...),
    db: SASession = Depends(get_db),
):
    errors = []
    user = (
        db.execute(select(User).where(User.student_id == student_id)).scalars().first()
    )
    if not user or not verify_password(password, user.password_hash):
        errors.append("학번 또는 비밀번호가 올바르지 않습니다.")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "errors": errors, "student_id": student_id},
            status_code=400,
        )

    login_user(request, student_id)
    return RedirectResponse(url="/", status_code=303)


# Logout
@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/", status_code=303)


# ---------------- Mypage ----------------
@app.get("/me")
def mypage_get(request: Request, db: SASession = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("mypage.html", {"request": request, "user": user, "msg": request.session.pop("flash_msg", None), "err": request.session.pop("flash_err", None)})


###### account edit ####
@app.get("/me/edit")
def mypage_edit_get(request: Request, db: SASession = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    current_faculty = next(
        (f for f, majors in FACULTIES.items() if user.major in majors), ""
    )
    return templates.TemplateResponse(
        "account_edit.html",
        {
            "request": request,
            "user": user,
            "faculty": current_faculty,
            "FACULTIES": FACULTIES,
            "msg": request.session.pop("flash_msg", None),
            "err": request.session.pop("flash_err", None),
        },
    )


@app.post("/me/edit")
def mypage_edit_post(
    request: Request,
    name: str = Form(...),
    faculty: Optional[str] = Form(None),
    major: Optional[str] = Form(None),
    current_password: str = Form(...),  # 현재 비밀번호
    new_password: str = Form(""),  # 새 비밀번호 (택)
    db: SASession = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    errors = []

    # 현재 비밀번호 확인
    if not verify_password(current_password, user.password_hash):
        errors.append("현재 비밀번호가 올바르지 않습니다.")

    if new_password and len(new_password) < 4:
        errors.append("새 비밀번호는 4자 이상이어야 합니다.")

    # faculty/major가 넘어온 경우에만 검증 및 반영
    if faculty is not None or major is not None:
        # 둘 다 온 경우 일치성 검증
        if faculty is not None and major is not None:
            if faculty not in FACULTIES or major not in FACULTIES[faculty]:
                errors.append("단과대/전공 선택이 올바르지 않습니다.")
        # major만 온 경우: 존재하는 전공인지 확인
        if faculty is None and major is not None:
            if not any(major in majors for majors in FACULTIES.values()):
                errors.append("전공 선택이 올바르지 않습니다.")

    if errors:
        current_faculty = next(
            (f for f, majors in FACULTIES.items() if user.major in majors), ""
        )
        return templates.TemplateResponse(
            "account_edit.html",
            {
                "request": request,
                "user": user,
                "faculty": faculty
                or current_faculty,
                "FACULTIES": FACULTIES,
                "err": " / ".join(errors),
            },
            status_code=400,
        )

    # 업데이트
    user.name = name.strip()
    user.major = major
    if new_password:
        user.password_hash = hash_password(new_password)

    db.add(user)
    db.commit()

    request.session["flash_msg"] = "프로필이 성공적으로 수정되었습니다."
    return RedirectResponse(url="/me", status_code=303)


## 회원탈퇴
@app.post("/me/delete")
def delete_account(
    request: Request,
    delete_password: str = Form(...),
    db: SASession = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # 비밀번호 검증
    if not verify_password(delete_password, user.password_hash):
        request.session["flash_err"] = "현재 비밀번호가 올바르지 않습니다."
        return RedirectResponse(url="/me", status_code=303)

    # TODO: 다른 테이블이 이 사용자와 FK로 연결되어 있으면
    #       (예: 시간표, 찜 목록 등) 먼저 삭제하거나 ON DELETE CASCADE 설정 필요.
    db.delete(user)
    db.commit()

    # 세션 종료
    logout_user(request)
    # 완료 메시지(원하면 홈에서 노출)
    request.session["flash_msg"] = "회원탈퇴가 완료되었습니다."
    return RedirectResponse(url="/", status_code=303)


# --- recommend page ---
# planner 상수의 복잡한 추천 로직 (세션 관리 + 필터링)


def _ensure_session_state(request: Request):
    s = request.session.get("recommend") or {}
    s.setdefault("target_credits", 16)
    s.setdefault("core_credits", None)
    s.setdefault(
        "selected_sections", {"p1": [], "p2": [], "p3": [], "p4": [], "p5": []}
    )
    s.setdefault(
        "filters", {"eval": "전체", "assign": "전체", "quiz": "전체", "sort": "기본순"}
    )
    request.session["recommend"] = s
    return s


def _semester_options():
    return [f"{y}-{t}" for y in range(1, 5) for t in (1, 2)]


def _filters_are_default(f: dict) -> bool:
    return (
        f.get("eval", "전체") == "전체"
        and f.get("assign", "전체") == "전체"
        and f.get("quiz", "전체") == "전체"
        and f.get("sort", "기본순") == "기본순"
    )


def _courses_for_step_and_semester(step: int, semester_token: str):
    if step == 2:
        return algo.list_major_required(semester_token)
    if step == 3:
        return algo.list_major_elective(semester_token)
    if step == 4:
        return algo.list_basic_focus(semester_token)
    return []


def _semester_options_filtered(step: int, filters: dict):
    # Return only semesters that have at least one course with sections
    # (필터 적용 여부와 관계없이 강의 데이터가 있는 학기만 반환)
    out = []
    try:
        for sem in _semester_options():
            courses = _courses_for_step_and_semester(step, sem)
            if not courses:
                continue
            has_any = False
            for d in courses:
                if not isinstance(d, dict):
                    continue
                cid = str(d.get("학수번호") or "").strip()
                if not cid:
                    continue
                try:
                    sections = algo.sections_for_course(cid)
                    # 강의 데이터가 있는지만 확인 (필터 적용하지 않음)
                    if sections:
                        has_any = True
                        break
                except Exception:
                    continue
            if has_any:
                out.append(sem)
    except Exception as e:
        import traceback

        traceback.print_exc()
        # 오류 발생 시 빈 리스트 반환 (기본 학기 옵션 사용)
        return []
    return out


@app.get("/recommend", name="recommend_page")
def recommend_get(
    request: Request,
    step: int = 1,
    semester: str = "1-1",
    db: SASession = Depends(get_db),
):
    """planner 상수의 복잡한 추천 로직 (세션 관리 + 필터링)"""
    # 로그인 체크
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # 페이지 나갔다 들어오면 초기화 (referrer가 /recommend가 아니거나 없을 때)
    # 단, step 간 이동(/recommend/step POST)은 유지
    referrer = request.headers.get("referer", "")
    # referrer가 없거나 /recommend가 포함되지 않으면 초기화 (새로고침 또는 다른 페이지에서 들어옴)
    if not referrer or "/recommend" not in referrer:
        if "recommend" in request.session:
            request.session.pop("recommend", None)

    _ensure_session_state(request)
    s = request.session["recommend"]
    ctx = {
        "request": request,
        "user": user,
        "step": step,
        "semester": semester,
        "semesters": _semester_options(),
        "state": s,
    }

    # Filter semester options for steps 2/3/4 - always filter to show only semesters with courses
    if step in (2, 3, 4):
        try:
            sems = _semester_options_filtered(step, s.get("filters", {}))
            if sems:
                ctx["semesters"] = sems
                if semester not in sems:
                    semester = sems[0] if sems else "1-1"
                    ctx["semester"] = semester
            else:
                # 강의 데이터가 있는 학기가 없으면 기본값 사용
                ctx["semesters"] = ["1-1"]
                ctx["semester"] = "1-1"
        except Exception as e:
            # 오류 발생 시 기본 학기 옵션 사용
            import traceback

            traceback.print_exc()
            ctx["semesters"] = _semester_options()
            if semester not in ctx["semesters"]:
                ctx["semester"] = "1-1"

    # 오류 메시지 처리
    error_message = request.session.pop("error_message", None)
    if error_message:
        ctx["error_message"] = error_message

    # 각 step에서 선택한 과목 리스트 추가
    ctx["selected_courses_by_step"] = {}
    sel = s["selected_sections"]
    for pkey, step_name in [
        ("p1", "전공필수"),
        ("p2", "전공선택"),
        ("p3", "기초/중점 교양"),
        ("p4", "핵심교양"),
        ("p5", "일반교양"),
    ]:
        courses = []
        for fid in sel.get(pkey, []):
            p = algo.SUBJECT_DIR / fid
            if p.exists():
                sec = algo.load_section(p)
                if sec:
                    courses.append(
                        {
                            "file_id": fid,  # file_id 추가 (정확한 매칭을 위해)
                            "course_id": sec.course_id,
                            "course_name": sec.course_name,
                            "prof": sec.prof,
                            "credit": sec.credit,
                        }
                    )
        ctx["selected_courses_by_step"][step_name] = courses

    if step == 1:
        pass
    elif step == 2:
        ctx["courses"] = algo.list_major_required(semester)
    elif step == 3:
        ctx["courses"] = algo.list_major_elective(semester)
    elif step == 4:
        ctx["courses"] = algo.list_basic_focus(semester)
    elif step == 5:
        ctx["courses"] = algo.list_core_common()
        m = algo.core_category_map()
        ctx["core_map"] = {str(k): v for k, v in m.items()}
    elif step == 6:
        ctx["courses"] = algo.list_general_common()
    elif step == 7:
        sel = s["selected_sections"]
        byp = {}
        # 카테고리별 파일 ID 매핑 (각 시간표의 카테고리별 학점 계산용)
        category_fid_map = {}
        total_selected_credits = 0

        for pkey, pnum in [("p1", 1), ("p2", 2), ("p3", 3), ("p4", 4), ("p5", 5)]:
            sections = []
            fids = []
            for fid in sel.get(pkey, []):
                p = algo.SUBJECT_DIR / fid
                if p.exists():
                    sec = algo.load_section(p)
                    if sec:
                        sections.append(sec)
                        fids.append(fid)
                        total_selected_credits += sec.credit
            byp[pnum] = sections
            category_fid_map[pnum] = set(fids)

        # 디버깅 정보 출력
        print(f"[DEBUG] Step 7 - Selected sections by priority:")
        for pnum, secs in byp.items():
            print(
                f"  Priority {pnum}: {len(secs)} sections, total credits: {sum(s.credit for s in secs)}"
            )
        print(f"[DEBUG] Total selected credits: {total_selected_credits}")
        print(f"[DEBUG] Target credits: {s.get('target_credits', 16)}")
        print(f"[DEBUG] Core credits target: {s.get('core_credits')}")

        # 핵교 학점 검증 (Step 7에서도)
        if s.get("core_credits") is not None and s["core_credits"] > 0:
            core_credits_target = s["core_credits"]
            total_core_credits = sum(sec.credit for sec in byp.get(4, []))
            print(
                f"[DEBUG] Core credits check: target={core_credits_target}, actual={total_core_credits}"
            )
            if total_core_credits < core_credits_target:
                ctx["error_message"] = (
                    f"저장한 학점({core_credits_target}학점) 이상의 핵심교양 과목을 선택해야 합니다. 현재 선택한 핵심교양 학점: {total_core_credits}학점"
                )
                ctx["schedules"] = []
                print(f"[DEBUG] Core credits validation failed")
            else:
                print(
                    f"[DEBUG] Calling generate_schedules with byp={byp}, target={s.get('target_credits', 16)}, core={s.get('core_credits')}"
                )
                try:
                    schedules = algo.generate_schedules(
                        byp, s.get("target_credits", 16), s.get("core_credits")
                    )
                    print(
                        f"[DEBUG] generate_schedules returned {len(schedules)} schedules"
                    )
                except Exception as e:
                    import traceback

                    print(f"[ERROR] generate_schedules failed:")
                    traceback.print_exc()
                    schedules = []
                    ctx["error_message"] = (
                        f"시간표 생성 중 오류가 발생했습니다: {str(e)}"
                    )

                # 각 시간표의 카테고리별 학점 계산
                schedules_with_credits = []
                for schedule in schedules:
                    try:
                        credits_by_cat = {
                            "전공필수": 0,
                            "전공선택": 0,
                            "기초/중점 교양": 0,
                            "핵심교양": 0,
                            "일반교양": 0,
                        }
                        for sec in schedule.sections:
                            # 각 섹션의 file_id를 확인하여 카테고리 결정
                            for pnum, fids_set in category_fid_map.items():
                                if sec.file_id in fids_set:
                                    category_names = {
                                        1: "전공필수",
                                        2: "전공선택",
                                        3: "기초/중점 교양",
                                        4: "핵심교양",
                                        5: "일반교양",
                                    }
                                    credits_by_cat[category_names[pnum]] += sec.credit
                                    break
                        # dataclass에 동적 속성 추가 (안전하게)
                        schedule.__dict__["credits_by_category"] = credits_by_cat
                        schedules_with_credits.append(schedule)
                    except Exception as e:
                        import traceback

                        print(f"[ERROR] Error processing schedule:")
                        traceback.print_exc()
                        # 오류 발생 시 기본값 설정
                        schedule.__dict__["credits_by_category"] = {
                            "전공필수": 0,
                            "전공선택": 0,
                            "기초/중점 교양": 0,
                            "핵심교양": 0,
                            "일반교양": 0,
                        }
                        schedules_with_credits.append(schedule)
                ctx["schedules"] = schedules_with_credits
                print(f"[DEBUG] Final schedules count: {len(schedules_with_credits)}")
        else:
            print(f"[DEBUG] No core credits target, calling generate_schedules")
            try:
                schedules = algo.generate_schedules(
                    byp, s.get("target_credits", 16), s.get("core_credits")
                )
                print(f"[DEBUG] generate_schedules returned {len(schedules)} schedules")
            except Exception as e:
                import traceback

                print(f"[ERROR] generate_schedules failed:")
                traceback.print_exc()
                schedules = []
                ctx["error_message"] = f"시간표 생성 중 오류가 발생했습니다: {str(e)}"

            # 각 시간표의 카테고리별 학점 계산
            schedules_with_credits = []
            for schedule in schedules:
                try:
                    credits_by_cat = {
                        "전공필수": 0,
                        "전공선택": 0,
                        "기초/중점 교양": 0,
                        "핵심교양": 0,
                        "일반교양": 0,
                    }
                    for sec in schedule.sections:
                        # 각 섹션의 file_id를 확인하여 카테고리 결정
                        for pnum, fids_set in category_fid_map.items():
                            if sec.file_id in fids_set:
                                category_names = {
                                    1: "전공필수",
                                    2: "전공선택",
                                    3: "기초/중점 교양",
                                    4: "핵심교양",
                                    5: "일반교양",
                                }
                                credits_by_cat[category_names[pnum]] += sec.credit
                                break
                    # dataclass에 동적 속성 추가 (안전하게)
                    schedule.__dict__["credits_by_category"] = credits_by_cat
                    schedules_with_credits.append(schedule)
                except Exception as e:
                    import traceback

                    print(f"[ERROR] Error processing schedule:")
                    traceback.print_exc()
                    # 오류 발생 시 기본값 설정
                    schedule.__dict__["credits_by_category"] = {
                        "전공필수": 0,
                        "전공선택": 0,
                        "기초/중점 교양": 0,
                        "핵심교양": 0,
                        "일반교양": 0,
                    }
                    schedules_with_credits.append(schedule)
            ctx["schedules"] = schedules_with_credits
            print(f"[DEBUG] Final schedules count: {len(schedules_with_credits)}")
        
        # ============ AI 추천 시간표 생성 ============
        # Step 7에서는 기본 시간표만 표시하고, AI 추천은 사용자가 요청할 때만 생성
        # (자동 생성 제거 - 사용자가 피드백 입력 후 버튼을 눌렀을 때만 생성)
        # 명시적으로 빈 리스트로 설정하여 자동 생성 방지
        # ⚠️ 중요: _generate_ai_schedules 함수를 호출하지 않음!
        ctx["ai_schedules"] = []
        print(f"[DEBUG] Step 7: AI 추천 자동 생성 비활성화 (사용자 요청 시에만 생성)")
        print(f"[DEBUG] Step 7: ctx['ai_schedules'] = {ctx['ai_schedules']}")

    return templates.TemplateResponse("recommend.html", ctx)


def _generate_ai_schedules(request: Request, db: SASession, s: dict, user: Optional[User], user_feedback: Optional[str] = None) -> list:
    """AI 추천 시간표 생성 함수 (피드백 지원)"""
    try:
        # 1. 사용자 이전 수강 내역 로드
        previous_courses = []
        if user:
            course_histories = db.query(CourseHistory).filter(
                CourseHistory.student_id == user.student_id
            ).all()
    
            for ch in course_histories:
                # RE(재수강) 제외
                if ch.grade and ch.grade.upper() == "RE":
                    continue
                
                # SubjectSummary에서 시간 정보 가져오기
                summary = db.query(SubjectSummary).filter(
                    SubjectSummary.subject_code == ch.course_code
                ).first()
                
                time_raw = summary.schedule_time if summary and summary.schedule_time else ""
                
                previous_courses.append({
                    "course_id": ch.course_code,
                    "course_name": ch.course_name,
                    "time_raw": time_raw,
                    "credit": int(ch.credit) if ch.credit else 0
                })
        
        print(f"[AI 추천] 이전 수강 내역: {len(previous_courses)}개")
        
        # 2. 사용자가 선택한 과목만 수집 (우선순위별로 구분)
        target_credits = s.get("target_credits", 16)
        core_credits_target = s.get("core_credits", 0)  # 핵심교양 목표 학점
        course_to_priority = {}  # 학수번호 -> 우선순위 매핑
        course_to_category = {}  # 학수번호 -> 핵심교양 카테고리 ID 매핑
        
        # 사용자가 선택한 섹션들
        sel = s["selected_sections"]
        
        # 우선순위별 정의: (우선순위, 카테고리명, pkey)
        priority_config = [
            (1, "전공필수", "p1"),
            (2, "전공선택", "p2"),
            (3, "기초/중점 교양", "p3"),
            (4, "핵심교양", "p4"),
            (5, "일반교양", "p5"),
        ]
        
        # 전공필수와 전공선택은 무조건 포함 (자동 선택)
        # 학수번호 기준으로 중복 제거 (같은 학수번호의 다른 분반은 하나만 선택)
        mandatory_sections = []  # 전공필수 + 전공선택 섹션들 (학수번호별로 하나만)
        mandatory_course_codes = set()  # 이미 포함된 학수번호 추적
        mandatory_credits = 0  # 전공필수 + 전공선택 학점 합계 (학수번호 기준)
        
        # AI가 선택할 나머지 과목들 (기초/중점 교양, 핵심교양, 일반교양)
        # AI에게 전달할 때도 학수번호별로 중복 제거
        ai_available_courses = []  # 학수번호별로 하나씩만 저장
        ai_available_course_codes = set()  # 이미 추가된 학수번호 추적
        core_category_map = algo.core_category_map()  # 핵심교양 카테고리 맵
        
        for priority, category_name, pkey in priority_config:
            selected_fids = sel.get(pkey, [])
            if not selected_fids:
                continue
            
            print(f"[AI 추천] 우선순위 {priority} ({category_name}) 사용자 선택 {len(selected_fids)}개 파일 수집 중...")
            
            # 핵심교양의 경우 카테고리 매핑도 저장
            if priority == 4:
                for fid in selected_fids:
                    course_code = fid.split(".")[0] if "." in fid else fid.replace(".json", "")
                    if course_code:
                        # 어느 카테고리에 속하는지 찾기
                        for cat_id in range(1, 7):
                            if course_code in core_category_map.get(cat_id, []):
                                course_to_category[course_code] = cat_id
                                break
            
            # 선택된 파일들의 모든 섹션 가져오기
            for fid in selected_fids:
                p = algo.SUBJECT_DIR / fid
                if not p.exists():
                    continue
                
                sec = algo.load_section(p)
                if not sec:
                    continue
                
                course_code = sec.course_id
                course_to_priority[course_code] = priority
                
                # 웹강의 여부 확인
                is_web = sec.is_web or (sec.time_raw and ("웹강의" in sec.time_raw or "온라인" in sec.time_raw or "온라" in sec.time_raw))
                
                course_info = {
                    "course_id": sec.course_id,
                    "course_name": sec.course_name,
                    "time_raw": sec.time_raw,
                    "credit": sec.credit,
                    "priority": priority,
                    "category": category_name,
                    "core_category_id": course_to_category.get(course_code) if priority == 4 else None,
                    "is_web": is_web,
                    "section": sec  # SectionFromFile 객체도 저장
                }
                
                # 전공필수(1)와 전공선택(2)는 무조건 포함 (학수번호별로 하나만)
                if priority == 1 or priority == 2:
                    # 같은 학수번호가 이미 포함되지 않았을 때만 추가
                    if course_code not in mandatory_course_codes:
                        mandatory_sections.append(sec)
                        mandatory_course_codes.add(course_code)
                        mandatory_credits += sec.credit
                        print(f"[AI 추천] 필수 포함: {sec.course_id} {sec.course_name} ({sec.credit}학점)")
                    else:
                        print(f"[AI 추천] 필수 포함 스킵 (중복 학수번호): {sec.course_id} {sec.course_name}")
                else:
                    # 나머지 우선순위는 AI가 선택하도록 추가 (학수번호별로 하나만)
                    if course_code not in ai_available_course_codes:
                        ai_available_courses.append(course_info)
                        ai_available_course_codes.add(course_code)
        
        print(f"[AI 추천] 필수 포함: 전공필수+전공선택 {len(mandatory_sections)}개 과목 (학수번호 기준), {mandatory_credits}학점")
        print(f"[AI 추천] AI 선택 대상: {len(ai_available_courses)}개 과목 (학수번호 기준) 수집 완료")
        
        # 목표 학점에서 전공필수+전공선택 학점 제외
        remaining_target_credits = max(0, target_credits - mandatory_credits)
        print(f"[AI 추천] 목표 학점: {target_credits}학점 → AI 선택 목표: {remaining_target_credits}학점 (전공필수+전공선택 {mandatory_credits}학점 제외)")
                
        # 3. AI 추천 호출 (나머지 우선순위만)
        ai_input = {
            "previous_courses": previous_courses,
            "available_courses": ai_available_courses,
            "target_credits": remaining_target_credits,
            "max_web_credits": 9,  # 웹강의 최대 9학점
            "core_credits_target": core_credits_target if core_credits_target > 0 else None,  # 핵심교양 목표 학점
            "priority_order": [3, 4, 5],  # 기초/중점 교양, 핵심교양, 일반교양만
            "core_category_constraint": True,  # 핵심교양 카테고리별 최대 1개
            "user_feedback": user_feedback  # 사용자 피드백 추가
        }
                
        ai_result = ai_recommend(
            ai_input,
            enable_logging=True,
            max_retries=3  # 한 번에 처리하므로 재시도 횟수 증가
        )
        
        # 추천 결과 처리
        ai_selected_courses = []
        ai_selected_codes = set()
        ai_suggestion = ai_result.get("suggestion", "")  # AI 제안 추출
        
        if ai_result.get("validation", {}).get("is_valid"):
            recommended = ai_result["validation"]["recommended_courses"]
            for rec_course in recommended:
                course_code = rec_course.get("학수번호", "")
                if course_code and course_code not in ai_selected_codes:
                    sections = algo.sections_for_course(course_code)
                    for sec in sections:
                        if sec.time_raw == rec_course.get("시간", ""):
                            ai_selected_courses.append({
                                "course_id": sec.course_id,
                                "course_name": sec.course_name,
                                "time_raw": sec.time_raw,
                                "credit": sec.credit
                            })
                            ai_selected_codes.add(course_code)
                            break
            
            print(f"[AI 추천] {len(ai_selected_courses)}개 과목 (학수번호 기준) 추천 완료")
            if ai_suggestion:
                print(f"[AI 추천] 제안: {ai_suggestion[:100]}...")
        else:
            print(f"[AI 추천] 검증 실패")
            ai_selected_courses = []
        
        # 4. 전공필수+전공선택 + AI 추천 결과 합치기 (학수번호 기준 중복 제거)
        all_final_sections = []  # 최종 섹션 목록 (학수번호별로 하나만)
        final_course_codes = set()  # 이미 포함된 학수번호 추적
        
        # 전공필수+전공선택 추가 (이미 학수번호 기준으로 중복 제거됨)
        for sec in mandatory_sections:
            if sec.course_id not in final_course_codes:
                all_final_sections.append(sec)
                final_course_codes.add(sec.course_id)
        
        # AI 추천 결과를 섹션으로 변환 (학수번호 기준 중복 제거)
        for course in ai_selected_courses:
            course_code = course["course_id"]
            # 이미 포함된 학수번호는 스킵 (안전장치)
            if course_code in final_course_codes:
                print(f"[AI 추천] 최종 합산 스킵 (중복 학수번호): {course_code}")
                continue
            
            sections = algo.sections_for_course(course_code)
            # 시간이 일치하는 섹션 찾기
            for sec in sections:
                if sec.time_raw == course.get("time_raw", ""):
                    all_final_sections.append(sec)
                    final_course_codes.add(course_code)
                    break
        
        if all_final_sections:
            # ScheduleFromFile 생성
            total_credits = sum(sec.credit for sec in all_final_sections)
            ai_schedule = algo.ScheduleFromFile(
                sections=all_final_sections,
                total_credits=total_credits
            )
            
            # 카테고리별 학점 계산 (학수번호 기준 - 이미 중복 제거되었으므로 정상 계산됨)
            credits_by_cat = {
                "전공필수": 0,
                "전공선택": 0,
                "기초/중점 교양": 0,
                "핵심교양": 0,
                "일반교양": 0,
            }
            
            # 각 섹션의 학수번호로 카테고리 판단 (course_to_priority 사용)
            category_names = {
                1: "전공필수",
                2: "전공선택",
                3: "기초/중점 교양",
                4: "핵심교양",
                5: "일반교양",
            }
            
            # 학수번호 기준으로 집계 (같은 학수번호가 여러 번 들어가지 않았는지 확인)
            seen_codes_for_credits = set()
            for sec in all_final_sections:
                # 학수번호 기준으로 한 번만 계산
                if sec.course_id not in seen_codes_for_credits:
                    priority = course_to_priority.get(sec.course_id, 5)  # 기본값: 일반교양
                    category = category_names.get(priority, "일반교양")
                    credits_by_cat[category] += sec.credit
                    seen_codes_for_credits.add(sec.course_id)
            
            ai_schedule.__dict__["credits_by_category"] = credits_by_cat
            ai_schedule.__dict__["ai_suggestion"] = ai_suggestion  # AI 제안 추가
            print(f"[AI 추천] 최종 시간표 생성 완료: 전공필수+전공선택 {len(mandatory_sections)}개 (학수번호 기준) + AI 추천 {len(ai_selected_courses)}개 (학수번호 기준) = 총 {len(all_final_sections)}개 과목 (학수번호 기준), {total_credits}학점")
            return [ai_schedule]
        else:
            print(f"[AI 추천] 최종 섹션 없음")
            return []
            
    except Exception as e:
        import traceback
        print(f"[AI 추천] 전체 오류: {e}")
        traceback.print_exc()
        return []


class AIRecommendRequest(BaseModel):
    feedback: Optional[str] = None

@app.post("/api/ai-recommend/refresh")
async def refresh_ai_recommend(
    request: Request,
    body: AIRecommendRequest,
    db: SASession = Depends(get_db),
):
    """피드백을 받아서 AI 추천 시간표를 다시 생성"""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다."}
        )
    
    _ensure_session_state(request)
    s = request.session["recommend"]
    
    try:
        # AI 추천 시간표 생성 (피드백 포함)
        ai_schedules = _generate_ai_schedules(request, db, s, user, user_feedback=body.feedback)
        
        # 결과를 JSON 형식으로 변환
        result = []
        for schedule in ai_schedules:
            schedule_dict = {
                "total_credits": schedule.total_credits,
                "credits_by_category": schedule.credits_by_category,
                "ai_suggestion": getattr(schedule, "ai_suggestion", ""),
                "sections": [
                    {
                        "course_id": sec.course_id,
                        "course_name": sec.course_name,
                        "time_raw": sec.time_raw,
                        "credit": sec.credit,
                        "prof": sec.prof,
                        "meetings": sec.meetings,
                        "is_web": sec.is_web
                    }
                    for sec in schedule.sections
                ]
            }
            result.append(schedule_dict)
        
        return JSONResponse(content={
            "success": True,
            "schedules": result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"오류가 발생했습니다: {str(e)}"}
        )


@app.post("/recommend/step")
async def recommend_post(
    request: Request,
    step: int = Form(...),
    action: str = Form("next"),
    semester: Optional[str] = Form("1-1"),
    target_credits: Optional[int] = Form(None),
    core_credits: Optional[int] = Form(None),
    eval_choice: Optional[str] = Form(None),
    assign_choice: Optional[str] = Form(None),
    quiz_choice: Optional[str] = Form(None),
    credit_choice: Optional[str] = Form(None),
    web_choice: Optional[str] = Form(None),
    sort_choice: Optional[str] = Form(None),
    selected_fids: Optional[str] = Form(None),
    db: SASession = Depends(get_db),
):
    """추천 단계 처리"""
    # 로그인 체크
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # 초기값 설정 (에러 발생 시에도 사용)
    s = None
    try:
        s = _ensure_session_state(request)

        # step 유효성 검사
        if step < 1 or step > 7:
            step = 1

        # action 유효성 검사
        if action not in ["prev", "next", "save"]:
            action = "next"

        # semester 기본값 설정
        if not semester:
            semester = "1-1"

        # 기본값 설정 (None이거나 빈 문자열이면 기본값 사용)
        eval_choice = eval_choice if eval_choice else "전체"
        assign_choice = assign_choice if assign_choice else "전체"
        quiz_choice = quiz_choice if quiz_choice else "전체"
        credit_choice = credit_choice if credit_choice else "전체"
        web_choice = web_choice if web_choice else "전체"
        sort_choice = sort_choice if sort_choice else "기본순"

        if step == 1 and target_credits:
            try:
                val = int(target_credits)
                if val < 16 or val > 21:
                    request.session["recommend"] = s
                    request.session["error_message"] = (
                        "학점은 16~21 사이의 값만 입력 가능합니다."
                    )
                    return RedirectResponse(
                        url=f"/recommend?step=1&semester={semester}",
                        status_code=303,
                    )
                s["target_credits"] = val
            except (ValueError, TypeError):
                request.session["recommend"] = s
                request.session["error_message"] = (
                    "학점은 16~21 사이의 값만 입력 가능합니다."
                )
                return RedirectResponse(
                    url=f"/recommend?step=1&semester={semester}",
                    status_code=303,
                )

        if step in (2, 3, 4, 5, 6):
            s["filters"] = {
                "eval": eval_choice,
                "assign": assign_choice,
                "quiz": quiz_choice,
                "credit": credit_choice,
                "sort": sort_choice,
            }
            if step in (5, 6):
                s["filters"]["web"] = web_choice
            # selected_fids가 제공되면 업데이트
            key = {2: "p1", 3: "p2", 4: "p3", 5: "p4", 6: "p5"}[step]
            if selected_fids is not None:
                if selected_fids.strip():
                    ids = [x for x in selected_fids.split(",") if x.strip()]
                    # Step 2, 3, 4의 경우: 학기 변경 시에도 선택 내역 누적 유지
                    if step in (2, 3, 4) and action == "save":
                        # 학기 변경 시 저장 액션: 기존 선택 내역과 병합 (중복 제거)
                        existing = set(s["selected_sections"].get(key, []))
                        new_ids = set(ids)
                        # 기존 선택 내역과 새로운 선택 내역 병합
                        merged = list(existing | new_ids)
                        s["selected_sections"][key] = merged
                    else:
                        # 일반적인 경우: 전달된 선택 내역으로 교체
                        s["selected_sections"][key] = ids
                else:
                    # 빈 문자열이면 선택 초기화 (빈 배열로 설정)
                    # Step 2, 3, 4의 경우: 선택 초기화는 현재 학기만 초기화해야 하지만,
                    # 현재 구조에서는 모든 학기를 초기화함
                    # 사용자가 "선택 초기화" 버튼을 누르면 현재 학기만 초기화해야 함
                    # 하지만 클라이언트에서 모든 선택 내역을 전달하므로, 여기서는 전체 초기화
                    s["selected_sections"][key] = []
            # selected_fids가 None이면 기존 선택 유지 (업데이트하지 않음)

        if step == 5:
            # 핵심교양 학점 저장 시 처리
            if action == "save":
                # 핵심교양 학점이 비어있을 때만 경고 (0은 허용)
                if (
                    core_credits is None
                    or (isinstance(core_credits, str) and not core_credits.strip())
                ):
                    request.session["recommend"] = s
                    request.session["error_message"] = "핵심교양 학점을 입력해주세요."
                    return RedirectResponse(
                        url=f"/recommend?step=5&semester={semester}", status_code=303
                    )
                try:
                    val = int(core_credits)
                    if val < 0 or val > 9:
                        request.session["recommend"] = s
                        request.session["error_message"] = (
                            "핵심교양 학점은 0~9 사이의 값이어야 합니다."
                        )
                        return RedirectResponse(
                            url=f"/recommend?step=5&semester={semester}",
                            status_code=303,
                        )
                    s["core_credits"] = val
                except (ValueError, TypeError):
                    request.session["recommend"] = s
                    request.session["error_message"] = (
                        "핵심교양 학점을 올바르게 입력해주세요."
                    )
                    return RedirectResponse(
                        url=f"/recommend?step=5&semester={semester}", status_code=303
                    )
                request.session["recommend"] = s
                return RedirectResponse(
                    url=f"/recommend?step=5&semester={semester}", status_code=303
                )
            # core_credits가 전달된 경우 업데이트 (저장 액션이 아닐 때)
            elif core_credits is not None and str(core_credits).strip() != "":
                try:
                    s["core_credits"] = int(core_credits)
                except Exception:
                    s["core_credits"] = None

            # Step 5에서 핵교 학점 검증 (다음 단계로 넘어갈 때만)
            if step == 5 and action == "next":
                # 다음 버튼 누를 때 전달된 core_credits 값을 먼저 저장
                if core_credits is not None and str(core_credits).strip() != "":
                    try:
                        s["core_credits"] = int(core_credits)
                    except Exception:
                        pass
                
                # 핵심교양 학점이 설정되지 않았을 때 오류 메시지 (0은 허용)
                if s.get("core_credits") is None:
                    request.session["recommend"] = s
                    request.session["error_message"] = "핵심교양 학점을 설정해주세요."
                    return RedirectResponse(
                        url=f"/recommend?step=5&semester={semester}",
                        status_code=303,
                    )
                # 핵심교양 학점이 설정되었을 때 선택한 과목 검증
                if s.get("core_credits") is not None and s["core_credits"] > 0:
                    key = {2: "p1", 3: "p2", 4: "p3", 5: "p4", 6: "p5"}[step]
                    ids = s["selected_sections"].get(key, [])
                    core_credits_target = s["core_credits"]
                    total_core_credits = 0
                    for fid in ids:
                        p = algo.SUBJECT_DIR / fid
                        if p.exists():
                            sec = algo.load_section(p)
                            if sec:
                                total_core_credits += sec.credit
                    if total_core_credits < core_credits_target:
                        request.session["recommend"] = s

                        # 오류 메시지를 세션에 저장하고 리다이렉트
                        request.session["error_message"] = (
                            f"저장한 학점({core_credits_target}학점) 이상의 핵심교양 과목을 선택해야 합니다. 현재 선택한 핵심교양 학점: {total_core_credits}학점"
                        )
                        return RedirectResponse(
                            url=f"/recommend?step=5&semester={semester}",
                            status_code=303,
                        )

        if action == "prev":
            step = max(1, step - 1)
        elif action == "next":
            step = min(7, step + 1)

        request.session["recommend"] = s
        return RedirectResponse(
            url=f"/recommend?step={step}&semester={semester}", status_code=303
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        # 에러 발생 시에도 세션 저장
        try:
            if s is None:
                s = _ensure_session_state(request)
            request.session["recommend"] = s
        except Exception as session_error:
            print(f"세션 저장 오류: {session_error}")
        request.session["error_message"] = f"오류가 발생했습니다: {str(e)}"
        # step이 유효한 범위인지 확인
        try:
            safe_step = max(1, min(7, int(step)))
        except:
            safe_step = 1
        return RedirectResponse(
            url=f"/recommend?step={safe_step}&semester={semester}", status_code=303
        )


@app.post("/recommend/sections")
async def recommend_sections(
    request: Request,
    course_ids: str = Form(...),
    eval_choice: str = Form("전체"),
    assign_choice: str = Form("전체"),
    quiz_choice: str = Form("전체"),
    credit_choice: str = Form("전체"),
    web_choice: str = Form("전체"),
    sort_choice: str = Form("기본순"),
):
    """섹션 목록 제공 (AJAX)"""
    ids = [x.strip() for x in course_ids.split(",") if x.strip()]
    all_sections = []
    for cid in ids:
        secs = algo.sections_for_course(cid)
        all_sections.extend(secs)
    filtered = algo.filter_and_sort_sections(
        all_sections,
        eval_choice,
        assign_choice,
        quiz_choice,
        credit_choice,
        sort_choice,
        web_choice,
    )
    from fastapi.responses import JSONResponse

    def sec_to_dict(s: algo.SectionFromFile):
        return {
            "file_id": s.file_id,
            "course_id": s.course_id,
            "course_name": s.course_name,
            "prof": s.prof,
            "credit": s.credit,
            "eval_type": s.eval_type,
            "assign_pct": s.assign_pct,
            "quiz_pct": s.quiz_pct,
            "mid_pct": s.mid_pct,
            "final_pct": s.final_pct,
            "attend_pct": s.attend_pct,
            "discuss_pct": s.discuss_pct,
            "etc_pct": s.etc_pct,
            "time_raw": s.time_raw,
            "is_web": s.is_web,
            "meetings": s.meetings,
        }

    return JSONResponse({"sections": [sec_to_dict(s) for s in filtered]})


# --- lecture search page ---
@app.get("/curriculum")
def curriculum(request: Request, db: SASession = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(
        "curriculum.html", {"request": request, "user": user}
    )


@app.get("/favorites")
def favorites(request: Request, db: SASession = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # 찜 목록 데이터 조회
    from app.db.models.favorite import (
        FavoriteLecture,
        FavoriteProfessor,
        FavoriteSchedule,
    )
    from app.db.models.subject_summary import SubjectSummary

    favorite_lectures_raw = (
        db.execute(
            select(FavoriteLecture).where(FavoriteLecture.student_id == user.student_id)
        )
        .scalars()
        .all()
    )

    # 강의명과 분반 정보를 포함하여 favorite_lectures 구성
    favorite_lectures = []
    for fav in favorite_lectures_raw:
        # SubjectSummary에서 강의 정보 조회
        summary = (
            db.execute(
                select(SubjectSummary).where(
                    SubjectSummary.subject_code == fav.subject_code
                )
            )
            .scalars()
            .first()
        )

        # 분반 추출 (예: "AIE1002.001" -> "001")
        section = ""
        if "." in fav.subject_code:
            section = fav.subject_code.split(".")[1]

        # 강의명 추출
        lecture_name = summary.lecture_name if summary and summary.lecture_name else ""

        # 강의명-분반 형식 문자열 생성
        display_name = ""
        if lecture_name:
            if section:
                display_name = f"{lecture_name}-{section}분반"
            else:
                display_name = lecture_name
        else:
            # 강의명이 없으면 학수번호만 표시
            display_name = fav.subject_code

        # 딕셔너리로 변환하여 추가 정보 포함
        fav_dict = {
            "id": fav.id,
            "subject_code": fav.subject_code,
            "lecture_name": lecture_name,
            "section": section,
            "display_name": display_name,
            "created_at": fav.created_at,
        }
        favorite_lectures.append(fav_dict)

    favorite_professors = (
        db.execute(
            select(FavoriteProfessor).where(
                FavoriteProfessor.student_id == user.student_id
            )
        )
        .scalars()
        .all()
    )

    favorite_schedules = (
        db.execute(
            select(FavoriteSchedule).where(
                FavoriteSchedule.student_id == user.student_id
            )
        )
        .scalars()
        .all()
    )

    return templates.TemplateResponse(
        "favorites.html",
        {
            "request": request,
            "user": user,
            "favorite_lectures": favorite_lectures,
            "favorite_professors": favorite_professors,
            "favorite_schedules": favorite_schedules,
        },
    )


@app.get("/lecture-search")
def lecture_search_page(request: Request, db: SASession = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(
        "lecture_search.html", {"request": request, "user": user}
    )


@app.get("/lecture-search/view-summary")
def view_summary_page(request: Request, from_page: Optional[str] = None):
    """요약본 보기 페이지"""
    user = None  # 필요시 현재 유저 가져오기
    # from=recommend 파라미터가 있으면 세션 초기화하지 않음
    return templates.TemplateResponse(
        "view_summary.html", {"request": request, "user": user, "from_page": from_page}
    )


# --- PDF serving endpoints ---
@app.get("/api/pdf/subject/{subject_code}")
def serve_subject_pdf(subject_code: str, db: SASession = Depends(get_db)):
    """과목 PDF 제공"""
    # 기본 학수번호 추출 (예: PHY1902.013 -> PHY1902)
    # lecture_search.html에서 이미 .split('.')[0]을 사용하지만, 혹시 모를 경우를 대비
    base_code = subject_code.split(".")[0] if "." in subject_code else subject_code

    # 1. 먼저 정확히 일치하는 코드로 조회 (예: PHY1902.013 -> PHY1902.013)
    pdf_record = db.execute(
        select(SubjectPdf).where(SubjectPdf.subject_code == subject_code)
    ).scalar_one_or_none()

    # 2. 기본 코드로 정확히 일치하는 경우 (예: PHY1902 -> PHY1902)
    if not pdf_record:
        pdf_record = db.execute(
            select(SubjectPdf).where(SubjectPdf.subject_code == base_code)
        ).scalar_one_or_none()

    # 3. 기본 코드로 시작하는 첫 번째 PDF 찾기 (예: PHY1902 -> PHY1902.001, PHY1902.002 등)
    if not pdf_record:
        pdf_record = db.execute(
            select(SubjectPdf)
            .where(SubjectPdf.subject_code.like(f"{base_code}.%"))
            .order_by(SubjectPdf.subject_code)
            .limit(1)
        ).scalar_one_or_none()

    # 4. 파일 경로가 없거나 존재하지 않으면 파일 시스템에서 직접 찾기
    if (
        not pdf_record
        or not pdf_record.file_path
        or not Path(pdf_record.file_path).exists()
    ):
        # SUBJECT_PDF_DIR에서 직접 파일 찾기
        from app.db.config import SUBJECT_PDF_DIR

        pdf_dir = Path(SUBJECT_PDF_DIR)

        # 정확한 파일명 찾기
        exact_file = pdf_dir / f"{subject_code}.pdf"
        if exact_file.exists():
            return FileResponse(
                str(exact_file),
                media_type="application/pdf",
                filename=f"{subject_code}.pdf",
            )

        # 기본 코드로 시작하는 첫 번째 파일 찾기
        base_file = pdf_dir / f"{base_code}.pdf"
        if base_file.exists():
            return FileResponse(
                str(base_file),
                media_type="application/pdf",
                filename=f"{base_code}.pdf",
            )

        # 패턴 매칭 (예: PHY1902.001.pdf, PHY1902.002.pdf 등)
        pattern_files = list(pdf_dir.glob(f"{base_code}.*.pdf"))
        if pattern_files:
            # 첫 번째 파일 반환
            first_file = sorted(pattern_files)[0]
            return FileResponse(
                str(first_file),
                media_type="application/pdf",
                filename=first_file.name,
            )

    # 5. 데이터베이스에서 찾은 레코드가 있으면 반환
    if pdf_record and pdf_record.file_path and Path(pdf_record.file_path).exists():
        return FileResponse(
            pdf_record.file_path,
            media_type="application/pdf",
            filename=pdf_record.filename or f"{subject_code}.pdf",
        )

    # 모든 시도가 실패한 경우
    raise HTTPException(status_code=404, detail="PDF not found")


@app.get("/api/pdf/department/{department_name}")
def serve_department_pdf(
    department_name: str, id: int | None = None, db: SASession = Depends(get_db)
):
    """학과 PDF 제공"""
    if id:
        # 특정 ID로 조회
        pdf_record = db.execute(
            select(DepartmentPdf).where(DepartmentPdf.id == id)
        ).scalar_one_or_none()
    else:
        # 학과명으로 조회 (첫 번째 결과)
        pdf_record = db.execute(
            select(DepartmentPdf).where(
                DepartmentPdf.department_name == department_name
            )
        ).scalar_one_or_none()

    if not pdf_record:
        raise HTTPException(status_code=404, detail="PDF not found")

    if pdf_record.file_path and Path(pdf_record.file_path).exists():
        # 파일명 형식: 인공지능공학과_교과과정표(2025학년도).pdf
        year_suffix = f"({pdf_record.year}학년도)" if pdf_record.year else ""
        filename = f"{department_name}_교과과정표{year_suffix}.pdf"

        return FileResponse(
            pdf_record.file_path, media_type="application/pdf", filename=filename
        )
    else:
        raise HTTPException(status_code=404, detail="PDF file not found on disk")


# ============ 성적표 업로드 및 조회 API ============
from app.db.models.transcript import Transcript, CourseHistory
from app.utils.pdf_parser import extract_text_from_pdf, parse_transcript_flexible


@app.post("/api/transcript/upload")
async def upload_transcript(
    request: Request,
    file: UploadFile = File(...),
    db: SASession = Depends(get_db)
):
    """성적표 PDF 업로드 및 파싱"""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다."}
        )
    
    # PDF 파일 확인
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "PDF 파일만 업로드 가능합니다."}
        )
    
    try:
        # PDF 읽기
        pdf_content = await file.read()
        
        # 텍스트 추출
        raw_text = extract_text_from_pdf(pdf_content)
        if not raw_text:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "PDF에서 텍스트를 추출할 수 없습니다."}
            )
        
        # 텍스트 파싱
        parsed_data = parse_transcript_flexible(raw_text)
        
        # 기존 성적표가 있으면 삭제
        existing = db.query(Transcript).filter(
            Transcript.student_id == user.student_id
        ).first()
        if existing:
            # 관련 수강 이력도 삭제
            db.query(CourseHistory).filter(
                CourseHistory.transcript_id == existing.id
            ).delete()
            db.delete(existing)
            db.commit()
        
        # 새 성적표 저장
        # PDF 하단부에서 파싱된 값 우선 사용
        final_major_credits = parsed_data.get("major_credits", 0.0)
        final_total_credits = parsed_data.get("total_credits", 0.0)
        
        transcript = Transcript(
            student_id=user.student_id,
            original_filename=file.filename,
            raw_text=raw_text,
            courses_data=parsed_data,  # major_credits도 포함됨
            total_credits=final_total_credits,
            gpa=parsed_data.get("gpa", 0.0)
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        # PDF 하단부에서 파싱된 학점 사용
        # 주전공(필/선) 학점과 취득학점(B) 우선 사용
        major_credits_from_pdf = parsed_data.get("major_credits", 0.0)
        total_credits_from_pdf = parsed_data.get("total_credits", 0.0)
        
        # 개별 수강 이력 저장 (PDF에서 파싱된 course_type 사용)
        major_credits_calculated = 0.0  # 전공필수 + 전공선택 (계산값)
        total_credits_calculated = 0.0  # 전체 학점 (RE 제외, 계산값)
        
        for course in parsed_data.get("courses", []):
            # PDF에서 파싱된 course_type 사용 (전공필수, 전공선택, 교양)
            course_type = course.get("course_type", "교양")
            
            # RE(재수강) 표시가 있으면 제외 (이미 파서에서 필터링되지만 추가 확인)
            if course.get("grade", "").upper() == "RE":
                continue
            
            credit = course.get("credit", 0.0)
            total_credits_calculated += credit
            
            if course_type in ["전공필수", "전공선택"]:
                major_credits_calculated += credit
            
            history = CourseHistory(
                transcript_id=transcript.id,
                student_id=user.student_id,
                year=course.get("year", ""),
                semester=course.get("semester", ""),
                course_code=course.get("course_code", ""),
                course_name=course.get("course_name", ""),
                credit=credit,
                grade=course.get("grade", ""),
                professor=course.get("professor", ""),
                is_major=course_type  # PDF에서 파싱된 타입 사용
            )
            db.add(history)
        db.commit()
        
        # PDF 하단부에서 파싱된 값이 있으면 우선 사용, 없으면 계산값 사용
        # 파싱된 값이 0이 아니면 (즉, 파싱 성공) 우선 사용
        final_major_credits = major_credits_from_pdf if major_credits_from_pdf > 0.0 else major_credits_calculated
        final_total_credits = total_credits_from_pdf if total_credits_from_pdf > 0.0 else total_credits_calculated
        
        # 디버깅: 파싱이 실패했는지 확인
        if major_credits_from_pdf == 0.0 and major_credits_calculated > 0.0:
            print(f"[WARNING] 주전공(필/선) 파싱 실패 - 계산값 사용: {major_credits_calculated}")
        if total_credits_from_pdf == 0.0 and total_credits_calculated > 0.0:
            print(f"[WARNING] 취득학점(B) 파싱 실패 - 계산값 사용: {total_credits_calculated}")
        
        # 파싱된 하단부 값을 courses_data에 저장 (나중에 조회 시 사용)
        parsed_data["major_credits"] = final_major_credits
        parsed_data["total_credits"] = final_total_credits
        
        # Transcript 모델의 courses_data와 total_credits 업데이트
        transcript.courses_data = parsed_data
        transcript.total_credits = final_total_credits
        db.commit()
        
        print(f"[DEBUG] 업로드 완료 - 전공학점: {final_major_credits}, 전체학점: {final_total_credits}")
        print(f"[DEBUG] PDF에서 파싱된 값 - 전공: {major_credits_from_pdf}, 전체: {total_credits_from_pdf}")
        print(f"[DEBUG] 계산된 값 - 전공: {major_credits_calculated}, 전체: {total_credits_calculated}")
        
        return JSONResponse(content={
            "success": True,
            "message": "성적표가 성공적으로 업로드되었습니다.",
            "data": {
                "total_courses": len([c for c in parsed_data.get("courses", []) if c.get("grade", "").upper() != "RE"]),
                "total_credits": final_total_credits,
                "major_credits": final_major_credits,
                "gpa": parsed_data.get("gpa", 0.0)
            }
        })
    
    except Exception as e:
        print(f"성적표 업로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"업로드 중 오류가 발생했습니다: {str(e)}"}
        )


@app.get("/api/transcript")
def get_transcript(request: Request, db: SASession = Depends(get_db)):
    """현재 사용자의 성적표 조회"""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다."}
        )
    
    transcript = db.query(Transcript).filter(
        Transcript.student_id == user.student_id
    ).first()
    
    if not transcript:
        return JSONResponse(content={
            "success": True,
            "data": None
        })
    
    # PDF 하단부에서 파싱된 학점 우선 사용
    major_credits_from_pdf = 0.0
    total_credits_from_pdf = 0.0
    
    if transcript.courses_data:
        # courses_data에 저장된 하단부 값 사용
        major_credits_from_pdf = transcript.courses_data.get("major_credits", 0.0)
        total_credits_from_pdf = transcript.courses_data.get("total_credits", 0.0)
    
    # PDF 하단부 값이 없거나 0이면 개별 과목에서 계산 (하지만 하단부 값이 우선)
    if major_credits_from_pdf == 0.0 or total_credits_from_pdf == 0.0:
        course_histories = db.query(CourseHistory).filter(
            CourseHistory.student_id == user.student_id
        ).all()
        
        major_credits_calc = 0.0  # 전공필수 + 전공선택
        total_credits_calc = 0.0  # 전체 학점
        
        for ch in course_histories:
            # RE(재수강)이면 제외
            if ch.grade and ch.grade.upper() == "RE":
                continue
            
            total_credits_calc += ch.credit
            if ch.is_major in ["전공필수", "전공선택"]:
                major_credits_calc += ch.credit
        
        # 계산값으로 업데이트 (하단부 값이 없을 때만)
        if major_credits_from_pdf == 0.0:
            major_credits_from_pdf = major_credits_calc
        if total_credits_from_pdf == 0.0:
            total_credits_from_pdf = total_credits_calc
    
    print(f"[DEBUG] 조회 시 - 전공학점: {major_credits_from_pdf}, 전체학점: {total_credits_from_pdf}")
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "upload_date": str(transcript.upload_date) if transcript.upload_date else None,
            "filename": transcript.original_filename,
            "total_credits": total_credits_from_pdf,  # 취득학점(B) 또는 계산값
            "gpa": transcript.gpa,
            "major_credits": major_credits_from_pdf,  # 주전공(필/선) 또는 계산값
            "courses": transcript.courses_data.get("courses", []) if transcript.courses_data else []
        }
    })


@app.delete("/api/transcript")
def delete_transcript(request: Request, db: SASession = Depends(get_db)):
    """성적표 삭제"""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다."}
        )
    
    transcript = db.query(Transcript).filter(
        Transcript.student_id == user.student_id
    ).first()
    
    if transcript:
        # 관련 수강 이력도 삭제
        db.query(CourseHistory).filter(
            CourseHistory.transcript_id == transcript.id
        ).delete()
        db.delete(transcript)
        db.commit()
    
    return JSONResponse(content={
        "success": True,
        "message": "성적표가 삭제되었습니다."
    })
