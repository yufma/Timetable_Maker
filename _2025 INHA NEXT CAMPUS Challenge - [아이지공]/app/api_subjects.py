# app/api_subjects.py
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.db.models.subject import Subject
from app.db.models.subject_summary import SubjectSummary
from app.db.models.common_subject import CommonSubject
from app.db.models.department_curriculum import DepartmentCurriculum
from app.db.models.subject_pdf import SubjectPdf
from app.db.models.department_pdf import DepartmentPdf
from app.db.models.favorite import FavoriteLecture, FavoriteProfessor
from app.db_bridge import get_db
from app.auth import current_user_id
from datetime import datetime

router = APIRouter(prefix="/api", tags=["subjects"])

@router.get("/subjects")
def list_subjects(q: str | None = Query(None), db: Session = Depends(get_db)):
    stmt = select(Subject)
    if q:
        stmt = stmt.where(Subject.name.ilike(f"%{q}%"))
    result = db.execute(stmt).scalars().all()
    return [{"code": s.code, "name": s.name, "category": s.category} for s in result]

@router.get("/common-subjects")
def list_common_subjects(db: Session = Depends(get_db)):
    result = db.execute(select(CommonSubject)).scalars().all()
    return [{"code": c.code, "name": c.name, "area": c.area, "credit": c.credit} for c in result]

@router.get("/curriculum")
def list_curriculum(db: Session = Depends(get_db)):
    result = db.execute(select(DepartmentCurriculum)).scalars().all()
    return [{"code": c.code, "name": c.name, "year_term": c.year_term, "credit": c.credit} for c in result]

# 강의 검색 API
@router.get("/lectures")
def list_lectures(db: Session = Depends(get_db)):
    """전체 강의 목록 조회 (SubjectSummary 기준)"""
    results = db.execute(select(SubjectSummary)).scalars().all()

    # PDF 존재 여부 일괄 조회 (기본 학수번호로 매칭)
    pdf_codes = {
        row.subject_code for row in db.execute(select(SubjectPdf)).scalars().all()
    }

    lectures = []
    for ss in results:
        # subject_code에서 기본 학수번호 추출 (예: PHY1902.013 -> PHY1902)
        base_code = (
            ss.subject_code.split(".")[0] if "." in ss.subject_code else ss.subject_code
        )
        # 전체 코드와 기본 코드 모두 확인 (PDF가 PHY1902.013.pdf 형식이거나 PHY1902.pdf 형식일 수 있음)
        has_pdf = ss.subject_code in pdf_codes or base_code in pdf_codes

        lecture = {
            "code": ss.subject_code,
            "name": ss.lecture_name or "",
            "professor": ss.professor or "",
            "credit": ss.credit or "",
            "schedule_time": ss.schedule_time or "",
            "evaluation_method": ss.evaluation_method or "",
            "has_pdf": has_pdf,
        }
        lectures.append(lecture)
    return lectures


@router.get("/curriculum-pdfs")
def list_curriculum_pdfs(
    department: str | None = Query(None),
    year: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """교과과정표 PDF 목록 조회 (학과별, 연도별 필터링 지원)"""
    stmt = select(DepartmentPdf)

    if department:
        stmt = stmt.where(DepartmentPdf.department_name == department)
    if year:
        stmt = stmt.where(DepartmentPdf.year == year)

    results = db.execute(stmt).scalars().all()

    curriculum_pdfs = []
    for pdf in results:
        curriculum_pdf = {
            "id": pdf.id,
            "department_name": pdf.department_name,
            "year": pdf.year,
            "curriculum_name": pdf.curriculum_name,
            "filename": pdf.filename,
        }
        curriculum_pdfs.append(curriculum_pdf)

    return curriculum_pdfs


@router.get("/lectures/search")
def search_lectures(q: str = Query(...), db: Session = Depends(get_db)):
    """강의명/학수번호로 검색"""
    stmt = select(SubjectSummary)
    stmt = stmt.where(
        or_(
            SubjectSummary.subject_code.ilike(f"%{q}%"),
            SubjectSummary.lecture_name.ilike(f"%{q}%"),
        )
    )
    results = db.execute(stmt).scalars().all()

    # PDF 존재 여부 일괄 조회 (기본 학수번호로 매칭)
    pdf_codes = {
        row.subject_code for row in db.execute(select(SubjectPdf)).scalars().all()
    }

    lectures = []
    for ss in results:
        # subject_code에서 기본 학수번호 추출 (예: PHY1902.013 -> PHY1902)
        base_code = (
            ss.subject_code.split(".")[0] if "." in ss.subject_code else ss.subject_code
        )
        # 전체 코드와 기본 코드 모두 확인 (PDF가 PHY1902.013.pdf 형식이거나 PHY1902.pdf 형식일 수 있음)
        has_pdf = ss.subject_code in pdf_codes or base_code in pdf_codes
        lecture = {
            "code": ss.subject_code,
            "name": ss.lecture_name or "",
            "professor": ss.professor or "",
            "credit": ss.credit or "",
            "schedule_time": ss.schedule_time or "",
            "evaluation_method": ss.evaluation_method or "",
            "has_pdf": has_pdf,
        }
        lectures.append(lecture)
    return lectures


@router.get("/lectures/search-by-professor")
def search_by_professor(professor: str = Query(...), db: Session = Depends(get_db)):
    """교수명으로 검색"""
    stmt = select(SubjectSummary)
    stmt = stmt.where(SubjectSummary.professor.ilike(f"%{professor}%"))
    results = db.execute(stmt).scalars().all()

    # PDF 존재 여부 일괄 조회 (기본 학수번호로 매칭)
    pdf_codes = {
        row.subject_code for row in db.execute(select(SubjectPdf)).scalars().all()
    }

    lectures = []
    for ss in results:
        # subject_code에서 기본 학수번호 추출 (예: PHY1902.013 -> PHY1902)
        base_code = (
            ss.subject_code.split(".")[0] if "." in ss.subject_code else ss.subject_code
        )
        # 전체 코드와 기본 코드 모두 확인 (PDF가 PHY1902.013.pdf 형식이거나 PHY1902.pdf 형식일 수 있음)
        has_pdf = ss.subject_code in pdf_codes or base_code in pdf_codes
        lecture = {
            "code": ss.subject_code,
            "name": ss.lecture_name or "",
            "professor": ss.professor or "",
            "credit": ss.credit or "",
            "schedule_time": ss.schedule_time or "",
            "evaluation_method": ss.evaluation_method or "",
            "has_pdf": has_pdf,
        }
        lectures.append(lecture)
    return lectures


@router.get("/lectures/search-advanced")
def search_advanced(
    q: str = Query(...), professor: str = Query(...), db: Session = Depends(get_db)
):
    """강의명/학수번호 + 교수명 동시 검색 (AND 조건)"""
    stmt = select(SubjectSummary)
    stmt = stmt.where(
        or_(
            SubjectSummary.subject_code.ilike(f"%{q}%"),
            SubjectSummary.lecture_name.ilike(f"%{q}%"),
        )
    ).where(SubjectSummary.professor.ilike(f"%{professor}%"))
    results = db.execute(stmt).scalars().all()

    # PDF 존재 여부 일괄 조회 (기본 학수번호로 매칭)
    pdf_codes = {
        row.subject_code for row in db.execute(select(SubjectPdf)).scalars().all()
    }

    lectures = []
    for ss in results:
        # subject_code에서 기본 학수번호 추출 (예: PHY1902.013 -> PHY1902)
        base_code = (
            ss.subject_code.split(".")[0] if "." in ss.subject_code else ss.subject_code
        )
        # 전체 코드와 기본 코드 모두 확인 (PDF가 PHY1902.013.pdf 형식이거나 PHY1902.pdf 형식일 수 있음)
        has_pdf = ss.subject_code in pdf_codes or base_code in pdf_codes
        lecture = {
            "code": ss.subject_code,
            "name": ss.lecture_name or "",
            "professor": ss.professor or "",
            "credit": ss.credit or "",
            "schedule_time": ss.schedule_time or "",
            "evaluation_method": ss.evaluation_method or "",
            "has_pdf": has_pdf,
        }
        lectures.append(lecture)
    return lectures


# 찜 관련 API
@router.post("/favorites/lecture/{subject_code}")
def add_favorite_lecture(
    subject_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """강의 찜 추가"""
    student_id = current_user_id(request)
    if not student_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    # 이미 찜한 강의인지 확인
    existing = (
        db.execute(
            select(FavoriteLecture).where(
                FavoriteLecture.student_id == student_id,
                FavoriteLecture.subject_code == subject_code,
            )
        )
        .scalars()
        .first()
    )

    if existing:
        return {"success": True, "message": "이미 찜한 강의입니다.", "is_favorite": True}

    # 찜 추가
    favorite = FavoriteLecture(
        student_id=student_id,
        subject_code=subject_code,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {"success": True, "message": "찜 목록에 추가되었습니다.", "is_favorite": True}


@router.delete("/favorites/lecture/{subject_code}")
def remove_favorite_lecture(
    subject_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """강의 찜 취소"""
    student_id = current_user_id(request)
    if not student_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    favorite = (
        db.execute(
            select(FavoriteLecture).where(
                FavoriteLecture.student_id == student_id,
                FavoriteLecture.subject_code == subject_code,
            )
        )
        .scalars()
        .first()
    )

    if not favorite:
        return {"success": True, "message": "찜 목록에 없는 강의입니다.", "is_favorite": False}

    db.delete(favorite)
    db.commit()

    return {"success": True, "message": "찜 목록에서 제거되었습니다.", "is_favorite": False}


@router.get("/favorites/lecture/status/{subject_code}")
def get_favorite_lecture_status(
    subject_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """강의 찜 상태 확인"""
    student_id = current_user_id(request)
    if not student_id:
        return {"is_favorite": False}

    favorite = (
        db.execute(
            select(FavoriteLecture).where(
                FavoriteLecture.student_id == student_id,
                FavoriteLecture.subject_code == subject_code,
            )
        )
        .scalars()
        .first()
    )

    return {"is_favorite": favorite is not None}


@router.post("/favorites/professor/{professor_name}")
def add_favorite_professor(
    professor_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """교수 찜 추가"""
    student_id = current_user_id(request)
    if not student_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    # 이미 찜한 교수인지 확인
    existing = (
        db.execute(
            select(FavoriteProfessor).where(
                FavoriteProfessor.student_id == student_id,
                FavoriteProfessor.professor_name == professor_name,
            )
        )
        .scalars()
        .first()
    )

    if existing:
        return {"success": True, "message": "이미 찜한 교수님입니다.", "is_favorite": True}

    # 찜 추가
    favorite = FavoriteProfessor(
        student_id=student_id,
        professor_name=professor_name,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {"success": True, "message": "찜 목록에 추가되었습니다.", "is_favorite": True}


@router.delete("/favorites/professor/{professor_name}")
def remove_favorite_professor(
    professor_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """교수 찜 취소"""
    student_id = current_user_id(request)
    if not student_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    favorite = (
        db.execute(
            select(FavoriteProfessor).where(
                FavoriteProfessor.student_id == student_id,
                FavoriteProfessor.professor_name == professor_name,
            )
        )
        .scalars()
        .first()
    )

    if not favorite:
        return {"success": True, "message": "찜 목록에 없는 교수님입니다.", "is_favorite": False}

    db.delete(favorite)
    db.commit()

    return {"success": True, "message": "찜 목록에서 제거되었습니다.", "is_favorite": False}


@router.get("/favorites/professor/status/{professor_name}")
def get_favorite_professor_status(
    professor_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """교수 찜 상태 확인"""
    student_id = current_user_id(request)
    if not student_id:
        return {"is_favorite": False}

    favorite = (
        db.execute(
            select(FavoriteProfessor).where(
                FavoriteProfessor.student_id == student_id,
                FavoriteProfessor.professor_name == professor_name,
            )
        )
        .scalars()
        .first()
    )

    return {"is_favorite": favorite is not None}


@router.delete("/favorites/lecture/by-id/{favorite_id}")
def remove_favorite_lecture_by_id(
    favorite_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """ID로 강의 찜 취소 (찜 목록 페이지용)"""
    student_id = current_user_id(request)
    if not student_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    favorite = (
        db.execute(
            select(FavoriteLecture).where(
                FavoriteLecture.id == favorite_id,
                FavoriteLecture.student_id == student_id,
            )
        )
        .scalars()
        .first()
    )

    if not favorite:
        raise HTTPException(status_code=404, detail="찜한 강의를 찾을 수 없습니다.")

    db.delete(favorite)
    db.commit()

    return {"success": True, "message": "찜 목록에서 제거되었습니다."}


@router.delete("/favorites/professor/by-id/{favorite_id}")
def remove_favorite_professor_by_id(
    favorite_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """ID로 교수 찜 취소 (찜 목록 페이지용)"""
    student_id = current_user_id(request)
    if not student_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    favorite = (
        db.execute(
            select(FavoriteProfessor).where(
                FavoriteProfessor.id == favorite_id,
                FavoriteProfessor.student_id == student_id,
            )
        )
        .scalars()
        .first()
    )

    if not favorite:
        raise HTTPException(status_code=404, detail="찜한 교수님을 찾을 수 없습니다.")

    db.delete(favorite)
    db.commit()

    return {"success": True, "message": "찜 목록에서 제거되었습니다."}


@router.post("/favorites/batch-status")
def get_favorites_batch_status(
    request: Request,
    subject_codes: list[str] = Form([]),
    professor_names: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    """여러 강의와 교수명의 찜 상태를 한 번에 조회"""
    student_id = current_user_id(request)
    if not student_id:
        # 로그인하지 않았으면 모두 False 반환
        return {
            "lectures": {code: False for code in subject_codes},
            "professors": {name: False for name in professor_names},
        }

    result = {
        "lectures": {},
        "professors": {},
    }

    # 강의 찜 상태 일괄 조회
    if subject_codes:
        favorites_lectures = (
            db.execute(
                select(FavoriteLecture).where(
                    FavoriteLecture.student_id == student_id,
                    FavoriteLecture.subject_code.in_(subject_codes),
                )
            )
            .scalars()
            .all()
        )
        favorited_lecture_codes = {fav.subject_code for fav in favorites_lectures}
        result["lectures"] = {
            code: code in favorited_lecture_codes for code in subject_codes
        }
    else:
        result["lectures"] = {}

    # 교수 찜 상태 일괄 조회
    if professor_names:
        favorites_professors = (
            db.execute(
                select(FavoriteProfessor).where(
                    FavoriteProfessor.student_id == student_id,
                    FavoriteProfessor.professor_name.in_(professor_names),
                )
            )
            .scalars()
            .all()
        )
        favorited_professor_names = {fav.professor_name for fav in favorites_professors}
        result["professors"] = {
            name: name in favorited_professor_names for name in professor_names
        }
    else:
        result["professors"] = {}

    return result