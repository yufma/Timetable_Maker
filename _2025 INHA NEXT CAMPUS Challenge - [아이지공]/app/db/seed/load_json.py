import json
import math
from pathlib import Path
from typing import Iterable, Any

from sqlalchemy.orm import Session

from ..models.common_subject import CommonSubject
from ..models.department_curriculum import DepartmentCurriculum
from ..models.subject import Subject
from ..models.subject_summary import SubjectSummary


def iter_json_files(directory: str | None) -> Iterable[Path]:
    if not directory:
        return []
    root = Path(directory)
    if not root.exists():
        return []
    return (p for p in root.glob("*.json") if p.is_file())


def as_items(data: Any) -> list[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def first_of(d: dict, keys: list[str]) -> Any:
    for k in keys:
        if k in d:
            val = d[k]
            # treat NaN as empty
            if isinstance(val, float) and math.isnan(val):
                continue
            if val not in (None, ""):
                return val
    return None


def split_category_area_from_filename(path: Path) -> tuple[str | None, str | None]:
    """파일명에서 category와 area 추출
    예: "일반교양-1.인문 · 예술.json" -> ("일반교양", "1.인문 · 예술")
    예: "창의.json" -> ("창의", None)
    """
    stem = path.stem
    if "-" in stem:
        category, area = stem.split("-", 1)
        return category, area
    # "-"가 없으면 파일명 자체를 category로 사용 (예: "창의.json")
    return stem, None


def extract_code_from_subject_row(row: dict, filename_stem: str) -> str | None:
    code = first_of(row, ["code", "과목코드", "학수번호", "id"])  
    if code:
        return str(code)
    if filename_stem:
        # 섹션 번호 제거 (예: "AIE1002.001" -> "AIE1002")
        if "." in filename_stem:
            # 마지막 마침표 앞까지가 코드
            parts = filename_stem.rsplit(".", 1)
            if parts[1].isdigit():
                return parts[0]
        return filename_stem
    text = row.get("학점")
    if isinstance(text, str) and " " in text:
        token = text.split(" ")[0]
        if any(c.isalpha() for c in token) and any(c.isdigit() for c in token):
            return token
    return None


def load_common_subjects(db: Session, directory: str | None) -> int:
    count = 0
    skipped = 0
    for path in iter_json_files(directory):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        inferred_category, inferred_area = split_category_area_from_filename(path)
        for row in as_items(data):
            category = first_of(row, ["category", "구분", "type"]) or inferred_category
            area = first_of(row, ["area", "영역", "group"]) or inferred_area
            code = first_of(row, ["code", "과목코드", "학수번호", "id"]) 
            name = first_of(row, ["name", "과목명", "교과목명", "title"]) 
            # 새 필드: 주관학과(전공), 학점, 인정 종별
            department = first_of(row, ["department", "주관학과(전공)", "주관학과", "전공"])
            credit = first_of(row, ["credit", "학점"])
            recognition_type = first_of(row, ["recognition_type", "인정 종별", "인정종별"])
            
            if not (category and code and name):
                continue
            
            # area가 None이면 빈 문자열로 처리 (창의.json 같은 경우)
            if not area:
                area = ""
            
            # 중복 체크: code 기반
            existing = (
                db.query(CommonSubject)
                .filter(CommonSubject.code == str(code))
                .first()
            )
            if existing:
                skipped += 1
                continue
            
            db.add(
                CommonSubject(
                    category=category,
                    area=area,
                    code=str(code),
                    name=str(name),
                    department=department,
                    credit=credit,
                    recognition_type=recognition_type,
                )
            )
            count += 1
    db.commit()
    if skipped > 0:
        print(f"  ⚠️  {skipped}개 중복 항목 건너뜀")
    return count


def load_department_curriculum(db: Session, directory: str | None) -> int:
    count = 0
    skipped = 0
    for path in iter_json_files(directory):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in as_items(data):
            # 새 버전 매핑: 종 별, 세부구분, 이수시기, 학수번호, 교과목명, 학점
            type = first_of(row, ["종 별", "type", "track"])
            sub_category = first_of(row, ["세부구분", "sub_category", "track_detail"])
            year_term = first_of(row, ["이수시기", "year_term", "학년학기", "학년/학기"]) 
            code = first_of(row, ["학수번호", "code", "과목코드", "id"]) 
            name = first_of(row, ["교과목명", "name", "과목명", "title"]) 
            credit = first_of(row, ["학점", "credit"])
            
            # NaN 처리
            if code and isinstance(code, float) and math.isnan(code):
                code = None
            if sub_category and isinstance(sub_category, float) and math.isnan(sub_category):
                sub_category = None
            
            if not (type and name):
                continue
            
            # 중복 체크: (type, name) 조합 기반 (code가 NaN일 수 있으므로)
            existing = (
                db.query(DepartmentCurriculum)
                .filter(
                    DepartmentCurriculum.type == type,
                    DepartmentCurriculum.name == name
                )
                .first()
            )
            if existing:
                skipped += 1
                continue
            
            db.add(
                DepartmentCurriculum(
                    type=type,
                    sub_category=sub_category,
                    year_term=year_term,
                    code=code,
                    name=name,
                    credit=credit,
                )
            )
            count += 1
    db.commit()
    if skipped > 0:
        print(f"  ⚠️  {skipped}개 중복 항목 건너뜀")
    return count


def load_subjects(db: Session, directory: str | None) -> int:
    count = 0
    skipped = 0
    seen_codes = set()  # 메모리 내 중복 추적
    for path in iter_json_files(directory):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        filename_stem = path.stem
        for row in as_items(data):
            category = first_of(row, ["category", "구분", "type"]) or "미분류"
            code = extract_code_from_subject_row(row, filename_stem)
            name = first_of(row, ["name", "과목명", "교과목명", "강의명", "title"]) 
            if not (code and name):
                continue
            
            # 코드를 문자열로 변환
            code_str = str(code)
            
            # 이미 본 코드는 건너뜀 (메모리 내 체크)
            if code_str in seen_codes:
                skipped += 1
                continue
            seen_codes.add(code_str)
            
            # DB 중복 체크: code 기반
            existing = (
                db.query(Subject)
                .filter(Subject.code == code_str)
                .first()
            )
            if existing:
                skipped += 1
                continue
            
            db.add(Subject(category=str(category), code=code_str, name=str(name)))
            count += 1
    db.commit()
    if skipped > 0:
        print(f"  ⚠️  {skipped}개 중복 항목 건너뜀")
    return count


def load_subject_summaries(db: Session, directory: str | None) -> int:
    """subject_json 디렉토리에서 강의계획서 상세를 읽어 SubjectSummary에 저장"""
    count = 0
    for path in iter_json_files(directory):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        
        filename_stem = path.stem  # 예: "AIE1002.001"
        
        # 단일 객체든 리스트든 처리
        items = as_items(data)
        for row in items:
            # 코드 추출
            code = (
                first_of(row, ["code", "과목코드", "학수번호", "id"])
                or filename_stem
            )
            if not code:
                continue

            def get_field(k: str) -> str | None:
                """JSON에서 필드 추출 및 NaN 처리"""
                v = row.get(k)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    return None
                return str(v).strip() if v else None

            # 이미 존재하면 스킵 (중복 방지)
            existing = (
                db.query(SubjectSummary)
                .filter(SubjectSummary.subject_code == str(code))
                .first()
            )
            if existing:
                continue

            summary = SubjectSummary(
                subject_code=str(code),
                lecture_name=get_field("강의명"),
                professor=get_field("교수명"),
                credit=get_field("학점"),
                schedule_time=get_field("강의시간"),
                evaluation_method=get_field("평가방식"),
                midterm=get_field("중간고사"),
                final=get_field("기말고사"),
                attendance=get_field("출석"),
                assignment=get_field("과제"),
                quiz=get_field("퀴즈"),
                discussion=get_field("토론"),
                etc=get_field("기타"),
            )
            db.add(summary)
            count += 1

    db.commit()
    return count
