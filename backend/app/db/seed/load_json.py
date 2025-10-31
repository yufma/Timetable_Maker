import json
import os
import math
from pathlib import Path
from typing import Iterable, Any

from sqlalchemy.orm import Session

from ..models.common_subject import CommonSubject
from ..models.department_curriculum import DepartmentCurriculum
from ..models.subject import Subject


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
    stem = path.stem
    if "-" in stem:
        category, area = stem.split("-", 1)
        return category, area
    return None, None


def extract_code_from_subject_row(row: dict, filename_stem: str) -> str | None:
    code = first_of(row, ["code", "과목코드", "학수번호", "id"])  
    if code:
        return str(code)
    if filename_stem:
        return filename_stem
    text = row.get("학점")
    if isinstance(text, str) and " " in text:
        token = text.split(" ")[0]
        if any(c.isalpha() for c in token) and any(c.isdigit() for c in token):
            return token
    return None


def load_common_subjects(db: Session, directory: str | None) -> int:
    count = 0
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
            if not (category and area and code and name):
                continue
            db.add(CommonSubject(category=category, area=area, code=str(code), name=str(name)))
            count += 1
    db.commit()
    return count


def load_department_curriculum(db: Session, directory: str | None) -> int:
    count = 0
    for path in iter_json_files(directory):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in as_items(data):
            year_term = first_of(row, ["year_term", "학년학기", "학년/학기", "이수시기"]) 
            track = first_of(row, ["track", "영역", "과정", "종 별", "세부구분"]) 
            code = first_of(row, ["code", "과목코드", "학수번호", "id"]) 
            name = first_of(row, ["name", "과목명", "교과목명", "title"]) 
            if not (track and name):
                continue
            db.add(
                DepartmentCurriculum(
                    year_term=str(year_term) if year_term else "",
                    track=str(track),
                    code=str(code) if code is not None else "",
                    name=str(name),
                )
            )
            count += 1
    db.commit()
    return count


def load_subjects(db: Session, directory: str | None) -> int:
    count = 0
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
            db.add(Subject(category=str(category), code=str(code), name=str(name)))
            count += 1
    db.commit()
    return count
