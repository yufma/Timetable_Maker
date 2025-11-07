# app/algorithm.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Iterable, Optional, Tuple

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]


# ---------- Data model ----------
@dataclass
class TimeSlot:
    """단일 수업 시간 블록(요일, 시작/끝 분 단위)."""

    day: str  # e.g. "Mon"
    start_min: int  # 분 단위 (09:00 -> 540)
    end_min: int  # 분 단위 (10:15 -> 615)

    def overlaps(self, other: "TimeSlot") -> bool:
        if self.day != other.day:
            return False
        return not (self.end_min <= other.start_min or other.end_min <= self.start_min)


@dataclass
class Section:
    """분반(교수/시간/강의실 등)."""

    section_id: str  # e.g. "A01"
    instructor: str
    times: List[TimeSlot]
    room: str = ""
    tags: set = field(default_factory=set)  # {"dept-only"} 등

    def conflicts_with(self, other: "Section") -> bool:
        return any(t.overlaps(u) for t in self.times for u in other.times)


@dataclass
class Course:
    """과목 (여러 분반을 가질 수 있음)."""

    code: str  # 학수번호
    name: str
    credits: int
    category: (
        str  # "major-required", "major-elective", "lib-basic", "lib-core", "lib-gen"
    )
    semester: str  # "1-1", "1-2", "2-1", ...
    sections: List[Section]


# ---------- Utilities ----------
def hm_to_min(hhmm: str) -> int:
    hh, mm = map(int, hhmm.split(":"))
    return hh * 60 + mm


def make_slot(day: str, start: str, end: str) -> TimeSlot:
    return TimeSlot(day, hm_to_min(start), hm_to_min(end))


def pick_best_section(
    course: Course,
    prefer_instructors: Optional[Iterable[str]] = None,
    prefer_dept_only: bool = False,
) -> List[Section]:
    """분반을 '좋은 순서'로 정렬해 반환 (선호 교수/학과 전용 우선 등)."""
    prefer = set(prefer_instructors or [])

    def score(sec: Section) -> Tuple[int, int, str]:
        # 더 큰 점수가 앞에 오도록 (정렬에서 reverse=True)
        by_instructor = 1 if sec.instructor in prefer else 0
        by_dept = 1 if (prefer_dept_only and "dept-only" in sec.tags) else 0
        # tie-break: section_id 사전순
        return (by_instructor, by_dept, sec.section_id)

    return sorted(course.sections, key=score, reverse=True)


def no_conflict(sections: List[Section], candidate: Section) -> bool:
    return all(not s.conflicts_with(candidate) for s in sections)


# ---------- Greedy recommender (데모용) ----------
@dataclass
class RecommendInput:
    target_credits: int
    major_required: List[str]  # 필수 과목 code 목록
    selected_courses: Dict[str, List[str]] = field(default_factory=dict)
    # 예: {"major-elective": ["AI200", "CS250"], "lib-core": ["CORE101", ...]}
    prefer_instructors: List[str] = field(default_factory=list)
    prefer_dept_only: bool = False


@dataclass
class RecommendResult:
    picked: List[Tuple[Course, Section]]
    total_credits: int
    reason: str


def greedy_recommend(catalog: List[Course], req: RecommendInput) -> RecommendResult:
    """아주 단순한 데모 알고리즘:
    1) 전공 필수는 무조건 먼저 배치(가능한 분반 중 선호 규칙 반영)
    2) 남은 크레딧을 채우기 위해 선택 과목들을 카테고리 별로 탐색
    3) 시간 충돌이 없도록 가능한 것부터 채움
    """
    by_code = {c.code: c for c in catalog}
    picked: List[Tuple[Course, Section]] = []
    cur_credits = 0
    reason_log = []

    # 1) 전공 필수
    for code in req.major_required:
        course = by_code.get(code)
        if not course:
            reason_log.append(f"[SKIP] 필수 '{code}'가 카탈로그에 없음")
            continue
        for sec in pick_best_section(
            course, req.prefer_instructors, req.prefer_dept_only
        ):
            if no_conflict([s for _, s in picked], sec):
                picked.append((course, sec))
                cur_credits += course.credits
                reason_log.append(f"[ADD] 필수 {course.name} ({sec.section_id})")
                break
        else:
            reason_log.append(f"[FAIL] 필수 '{course.name}' 시간 충돌로 미배치")

    # 2) 선택 과목(카테고리 우선 순서를 주고 싶으면 여기서 정렬/가중치 추가)
    remain_codes: List[str] = []
    for _, codes in req.selected_courses.items():
        for code in codes:
            if code not in req.major_required:
                remain_codes.append(code)

    # 중복 제거, 존재하는 것만
    remain_codes = [c for c in dict.fromkeys(remain_codes) if c in by_code]

    for code in remain_codes:
        if cur_credits >= req.target_credits:
            break
        course = by_code[code]
        for sec in pick_best_section(
            course, req.prefer_instructors, req.prefer_dept_only
        ):
            if no_conflict([s for _, s in picked], sec):
                picked.append((course, sec))
                cur_credits += course.credits
                reason_log.append(f"[ADD] 선택 {course.name} ({sec.section_id})")
                break

    return RecommendResult(
        picked=picked,
        total_credits=cur_credits,
        reason="\n".join(reason_log),
    )


# ---------- For template (시간표 그리기용) ----------
def to_calendar_blocks(
    sections: List[Section],
) -> Dict[str, List[Tuple[int, int, str]]]:
    """템플릿에서 쉽게 사용하도록 요일별 블록으로 변환."""
    out: Dict[str, List[Tuple[int, int, str]]] = {d: [] for d in DAYS}
    for sec in sections:
        label = sec.instructor
        for t in sec.times:
            out[t.day].append((t.start_min, t.end_min, label))
    for d in out:
        out[d].sort()
    return out


# ---------- Demo catalog ----------
def demo_catalog() -> List[Course]:
    """실제 DB 없을 때 보여줄 더미 데이터."""

    def sec(_id, inst, *slots, dept=False):
        s = Section(_id, inst, [make_slot(*sl) for sl in slots])
        if dept:
            s.tags.add("dept-only")
        return s

    return [
        Course(
            code="AI101",
            name="인공지능개론",
            credits=3,
            category="major-required",
            semester="2-1",
            sections=[
                sec(
                    "A01",
                    "Kim",
                    ("Mon", "09:00", "10:15"),
                    ("Wed", "09:00", "10:15"),
                    dept=True,
                ),
                sec("A02", "Lee", ("Tue", "10:30", "11:45"), ("Thu", "10:30", "11:45")),
            ],
        ),
        Course(
            code="CS120",
            name="자료구조",
            credits=3,
            category="major-required",
            semester="2-1",
            sections=[
                sec(
                    "B01", "Park", ("Mon", "10:30", "11:45"), ("Wed", "10:30", "11:45")
                ),
                sec(
                    "B02",
                    "Choi",
                    ("Tue", "13:00", "14:15"),
                    ("Thu", "13:00", "14:15"),
                    dept=True,
                ),
            ],
        ),
        Course(
            code="AI200",
            name="머신러닝",
            credits=3,
            category="major-elective",
            semester="2-2",
            sections=[
                sec("C01", "Kim", ("Tue", "09:00", "10:15"), ("Thu", "09:00", "10:15")),
                sec("C02", "Yun", ("Mon", "13:00", "14:15"), ("Wed", "13:00", "14:15")),
            ],
        ),
        Course(
            code="CS250",
            name="운영체제",
            credits=3,
            category="major-elective",
            semester="3-1",
            sections=[
                sec("D01", "Ryu", ("Tue", "15:00", "16:15"), ("Thu", "15:00", "16:15")),
            ],
        ),
        Course(
            code="CORE101",
            name="핵심교양: 글쓰기",
            credits=2,
            category="lib-core",
            semester="1-1",
            sections=[
                sec("E01", "Han", ("Fri", "09:00", "10:50")),
                sec("E02", "Han", ("Fri", "11:00", "12:50")),
            ],
        ),
        Course(
            code="BASIC110",
            name="기초교양: 미분적분",
            credits=3,
            category="lib-basic",
            semester="1-1",
            sections=[
                sec(
                    "F01", "Jang", ("Mon", "15:00", "16:15"), ("Wed", "15:00", "16:15")
                ),
            ],
        ),
        Course(
            code="GEN200",
            name="일반교양: 심리학의이해",
            credits=3,
            category="lib-gen",
            semester="2-1",
            sections=[
                sec("G01", "Kang", ("Thu", "11:00", "12:15")),
            ],
        ),
    ]


# ---------- Quick demo ----------
def demo_run(target: int = 16) -> Dict:
    """UI에서 받은 목표 학점(기본 16)을 반영해 데모 추천을 생성."""
    # 안전 범위(16~19)로 클램프 — 백엔드/프론트 모두에서 보정하지만 한 번 더 방어
    target = max(16, min(19, int(target)))

    cat = demo_catalog()
    req = RecommendInput(
        target_credits=target,
        major_required=["AI101", "CS120"],
        selected_courses={
            "major-elective": ["AI200", "CS250"],
            "lib-core": ["CORE101"],
            "lib-basic": ["BASIC110"],
            "lib-gen": ["GEN200"],
        },
        prefer_instructors=["Kim"],  # 선호 교수 예시
        prefer_dept_only=True,
    )
    result = greedy_recommend(cat, req)

    sections = [sec for _, sec in result.picked]
    grid = to_calendar_blocks(sections)

    # 템플릿으로 넘기기 좋은 형태
    return {
        "total_credits": result.total_credits,
        "picked": [
            {
                "code": c.code,
                "name": c.name,
                "credits": c.credits,
                "section": s.section_id,
                "instructor": s.instructor,
                "times": [
                    {"day": t.day, "start": t.start_min, "end": t.end_min}
                    for t in s.times
                ],
            }
            for c, s in result.picked
        ],
        "grid": grid,
        "log": result.reason,
    }


if __name__ == "__main__":
    # 로컬 테스트 용
    import json

    print(json.dumps(demo_run(), ensure_ascii=False, indent=2))


# ====== [AUTO-ADDED] Data-driven loaders using real JSON datasets ======
# This block does NOT modify existing classes/logic above. It only adds helpers
# to read from `data/depart_json`, `data/common_subjects_json`, `data/subject_json`.

import os as _os, json as _json, re as _re, glob as _glob
from typing import Any as _Any, Dict as _Dict, List as _List, Tuple as _Tuple

# Semester label mapping used by depart_json
_SEM_LABEL = {
    "1-1": "1학년(1학기)",
    "1-2": "1학년(2학기)",
    "2-1": "2학년(1학기)",
    "2-2": "2학년(2학기)",
    "3-1": "3학년(1학기)",
    "3-2": "3학년(2학기)",
    "4-1": "4학년(1학기)",
    "4-2": "4학년(2학기)",
}

SEMESTER_OPTIONS: _List[str] = [f"{y}-{s}" for y in range(1, 5) for s in (1, 2)]

_DATA_ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), "..", "data"))
_DEPART = _os.path.join(_DATA_ROOT, "depart_json", "인공지능공학과.json")
_COMMON_DIR = _os.path.join(_DATA_ROOT, "common_subjects_json")
_SUBJECT_DIR = _os.path.join(_DATA_ROOT, "subject_json")


def _load_json(path: str):
    if not _os.path.exists(path):
        return None
    s = open(path, "r", encoding="utf-8").read()
    s = _re.sub(r":\s*NaN", ": null", s)
    try:
        return _json.loads(s)
    except Exception:
        return None


def _to_int_credit(x) -> int | str:
    try:
        f = float(str(x))
        return int(f)
    except Exception:
        return str(x)


def _kday_to_en(k: str) -> str:
    return {
        "월": "Mon",
        "화": "Tue",
        "수": "Wed",
        "목": "Thu",
        "금": "Fri",
        "토": "Sat",
        "일": "Sun",
    }.get(k, "Mon")


_time_tok_re = _re.compile(r"([월화수목금토일])([0-9,]+)")


def _parse_timestr(timestr: str) -> _List[_Dict[str, _Any]]:
    """Parse subject_json '강의시간' string into day-periods blocks.
    Returns [{"day":"Mon","periods":[13,14,...]}, ...].
    '웹강의' -> empty list (no fixed time)."""
    timestr = (timestr or "").strip()
    if not timestr or "웹강의" in timestr:
        return []
    blocks = []
    for day, nums in _time_tok_re.findall(timestr):
        try:
            periods = [int(x) for x in nums.split(",") if x.strip().isdigit()]
        except Exception:
            periods = []
        blocks.append({"day": _kday_to_en(day), "periods": periods})
    return blocks


def _one_line(name: str, code: str, credit: int | str, **extras) -> str:
    credit_part = (
        f"{credit}학점"
        if (isinstance(credit, int) or str(credit).isdigit())
        else f"{credit}"
    )
    line = f"{name} ({code}) {credit_part}"
    extra_keys = ("section", "prof", "time")
    vals = [str(extras[k]) for k in extra_keys if extras.get(k)]
    if vals:
        line += " — " + " • ".join(vals)
    return line


def _expand_sections_for_code(base_code: str) -> _List[_Dict[str, _Any]]:
    """Find all sections for a base code from subject_json. Returns list of dicts:
    {"code":base_code, "section":"001", "name":..., "prof":..., "credit":int|str, "time_str":..., "times": [...] }
    """
    pattern = _os.path.join(_SUBJECT_DIR, f"{base_code}*.json")
    matches = sorted(_glob.glob(pattern))
    out: _List[_Dict[str, _Any]] = []
    for p in matches:
        d = _load_json(p) or {}
        fname = _os.path.basename(p)
        sec = "001"
        if "." in fname:
            seg = fname.split(".")[1]
            if seg.isdigit():
                sec = seg
        name = (d.get("강의명") or "").strip()
        prof = (d.get("교수명") or "").strip()
        credit = _to_int_credit(d.get("학점"))
        tstr = (d.get("강의시간") or "").strip()
        out.append(
            {
                "code": base_code,
                "section": sec,
                "name": name,
                "prof": prof,
                "credit": credit,
                "time_str": tstr,
                "times": _parse_timestr(tstr),
                "one_line": _one_line(
                    name or "미정 과목",
                    base_code,
                    credit,
                    section=sec,
                    prof=prof,
                    time=tstr,
                ),
            }
        )
    return out


def _load_depart_rows() -> _List[_Dict[str, _Any]]:
    data = _load_json(_DEPART) or []
    return data if isinstance(data, list) else []


def get_major_by_semester(semester: str, kind: str) -> _List[_Dict[str, _Any]]:
    """kind in {'전공필수', '전공선택'}"""
    label = _SEM_LABEL.get(semester)
    if not label:
        return []
    rows = [
        r
        for r in _load_depart_rows()
        if (r.get("종 별") == kind and (r.get("이수시기") or "").strip() == label)
    ]
    # Expand to sections using subject_json
    items: _List[_Dict[str, _Any]] = []
    for r in rows:
        code = (r.get("학수번호") or "").strip()
        name = (r.get("교과목명") or "").strip()
        credit = _to_int_credit(r.get("학점"))
        if not code:
            continue
        secs = _expand_sections_for_code(code) or [
            {
                "code": code,
                "section": "001",
                "name": name,
                "prof": "",
                "credit": credit,
                "time_str": "",
                "times": [],
                "one_line": _one_line(name, code, credit, section="001"),
            }
        ]
        # attach base info
        for s in secs:
            s["base_name"] = name or s.get("name") or ""
            s["base_credit"] = credit if credit != "-" else s.get("credit")
            s["priority"] = 1 if kind == "전공필수" else 2
        items.extend(secs)
    return items


def _list_common_files(prefix: str) -> _List[str]:
    if not _os.path.isdir(_COMMON_DIR):
        return []
    return [
        _os.path.join(_COMMON_DIR, f)
        for f in _os.listdir(_COMMON_DIR)
        if f.startswith(prefix) and f.endswith(".json")
    ]


def get_core_liberal() -> _List[_Dict[str, _Any]]:
    """핵심교양: load from common_subjects_json files starting with '핵심교양-'"""
    files = _list_common_files("핵심교양-")
    items: _List[_Dict[str, _Any]] = []
    for path in files:
        data = _load_json(path) or []
        for r in data:
            code = (r.get("학수번호") or "").strip()
            name = (r.get("교과목명") or "").strip()
            credit = _to_int_credit(r.get("학점"))
            if not code:
                continue
            for s in _expand_sections_for_code(code) or [
                {
                    "code": code,
                    "section": "001",
                    "name": name,
                    "prof": "",
                    "credit": credit,
                    "time_str": "",
                    "times": [],
                }
            ]:
                s["base_name"] = name or s.get("name") or ""
                s["base_credit"] = credit if credit != "-" else s.get("credit")
                s["priority"] = 4
                s["one_line"] = _one_line(
                    s["name"],
                    code,
                    s["credit"],
                    section=s["section"],
                    prof=s.get("prof", ""),
                    time=s.get("time_str", ""),
                )
                items.append(s)
    return items


def get_general_liberal() -> _List[_Dict[str, _Any]]:
    """일반교양: load from files starting with '일반교양-'"""
    files = _list_common_files("일반교양-")
    items: _List[_Dict[str, _Any]] = []
    for path in files:
        data = _load_json(path) or []
        for r in data:
            code = (r.get("학수번호") or "").strip()
            name = (r.get("교과목명") or "").strip()
            credit = _to_int_credit(r.get("학점"))
            if not code:
                continue
            for s in _expand_sections_for_code(code) or [
                {
                    "code": code,
                    "section": "001",
                    "name": name,
                    "prof": "",
                    "credit": credit,
                    "time_str": "",
                    "times": [],
                }
            ]:
                s["base_name"] = name or s.get("name") or ""
                s["base_credit"] = credit if credit != "-" else s.get("credit")
                s["priority"] = 5
                s["one_line"] = _one_line(
                    s["name"],
                    code,
                    s["credit"],
                    section=s["section"],
                    prof=s.get("prof", ""),
                    time=s.get("time_str", ""),
                )
                items.append(s)
    return items


def get_basic_focus_liberal() -> _List[_Dict[str, _Any]]:
    """교양필수(기초/중점) — 데이터 부재 시 '창의' 파일을 대체로 사용.
    가능한 경우 subject_json과 연결하여 분반 확장."""
    # Try to find files explicitly named for basic/focus (not present currently).
    files = (
        [_os.path.join(_COMMON_DIR, "창의.json")]
        if _os.path.exists(_os.path.join(_COMMON_DIR, "창의.json"))
        else []
    )
    items: _List[_Dict[str, _Any]] = []
    for path in files:
        data = _load_json(path) or []
        for r in data:
            code = (r.get("학수번호") or "").strip()
            name = (r.get("교과목명") or "").strip()
            credit = _to_int_credit(r.get("학점"))
            if not code:
                continue
            for s in _expand_sections_for_code(code) or [
                {
                    "code": code,
                    "section": "001",
                    "name": name,
                    "prof": "",
                    "credit": credit,
                    "time_str": "",
                    "times": [],
                }
            ]:
                s["base_name"] = name or s.get("name") or ""
                s["base_credit"] = credit if credit != "-" else s.get("credit")
                s["priority"] = 3
                s["one_line"] = _one_line(
                    s["name"],
                    code,
                    s["credit"],
                    section=s["section"],
                    prof=s.get("prof", ""),
                    time=s.get("time_str", ""),
                )
                items.append(s)
    return items


def package_for_template(items: _List[_Dict[str, _Any]]) -> _List[_Dict[str, _Any]]:
    """Reduce fields and ensure safe strings for Jinja/JS."""
    out = []
    for s in items:
        out.append(
            {
                "name": s.get("name") or s.get("base_name") or "미정 과목",
                "code": s["code"],
                "section": s.get("section", "001"),
                "credit": s.get("credit") or s.get("base_credit") or "-",
                "prof": s.get("prof", ""),
                "time_str": s.get("time_str", ""),
                "times": s.get("times", []),
                "priority": s.get("priority", 5),
                "one_line": s.get("one_line")
                or _one_line(
                    s.get("name") or s.get("base_name") or "미정 과목",
                    s["code"],
                    s.get("credit") or s.get("base_credit") or "-",
                    section=s.get("section", "001"),
                    prof=s.get("prof", ""),
                    time=s.get("time_str", ""),
                ),
            }
        )
    return out


# ====== [END AUTO-ADDED] ======

# ====== planner 상수에서 추가된 함수들 ======
# planner 상수의 복잡한 추천 로직을 위한 함수들
import json as _json_module
from pathlib import Path as _Path_module
import re as _re_module
from typing import Any, Set

# 경로 상수 (planner 상수 방식)
_DATA_DIR = _Path_module(__file__).resolve().parents[1] / "data"
_SUBJECT_DIR_PLANNER = _DATA_DIR / "subject_json"
_DEPART_PATH_PLANNER = _DATA_DIR / "depart_json" / "인공지능공학과.json"
_COMMON_DIR_PLANNER = _DATA_DIR / "common_subjects_json"


# planner 상수 방식의 Section 클래스 (기존 Section과 구분)
@dataclass
class SectionFromFile:
    """planner 상수 방식의 Section 클래스 (JSON 파일에서 로드)"""

    file_id: str
    course_id: str
    course_name: str
    prof: str
    credit: int
    eval_type: str
    assign_pct: float
    quiz_pct: float
    mid_pct: float
    final_pct: float
    attend_pct: float
    discuss_pct: float
    etc_pct: float
    time_raw: str
    is_web: bool
    meetings: List[Tuple[int, int, int, str]] = field(
        default_factory=list
    )  # (day, start_slot, end_slot, room)


# planner 상수 방식의 DAY_MAP
_DAY_MAP = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5}
_SLOT_START_HOUR = 9  # 1=09:00-09:30
_SLOT_MIN = 30  # minutes per slot


def _safe_float_planner(x: Any) -> float:
    """planner 상수 방식의 safe_float"""
    try:
        if isinstance(x, str):
            x = x.strip().replace("%", "").replace(" ", "")
        return float(x)
    except Exception:
        return 0.0


def _safe_int_credits_planner(x: Any) -> int:
    """planner 상수 방식의 safe_int_credits"""
    try:
        if isinstance(x, str):
            x = x.strip()
            if x.endswith(".0"):
                x = x[:-2]
        return int(float(x))
    except Exception:
        return 0


def _iter_subject_files_for_planner(course_id: str) -> List[_Path_module]:
    """planner 상수 방식의 파일 반복"""
    return sorted(_SUBJECT_DIR_PLANNER.glob(f"{course_id}*.json"))


def _parse_time_slots_planner(
    time_text: str,
) -> Tuple[bool, List[Tuple[int, int, int, str]]]:
    """
    planner 상수 방식의 시간 파싱
    Return (is_web, meetings). meetings are tuples (day_idx, start_slot, end_slot, room).
    Slot 1 = 09:00-09:30
    """
    if not time_text or "웹강의" in time_text:
        return True, []

    text = str(time_text)
    meetings: List[Tuple[int, int, int, str]] = []

    tokens = text.split(":")
    current_room = None
    for tok in tokens:
        tok = tok.strip()
        if tok and tok[0] in _DAY_MAP:
            # e.g. "월13,14,15,수16,17"
            for m in _re_module.finditer(r"([월화수목금토])([0-9,]+)", tok):
                day_char = m.group(1)
                nums = m.group(2)
                slots = [int(x) for x in nums.split(",") if x]
                if not slots:
                    continue
                slots.sort()
                start = slots[0]
                prev = start
                for s in slots[1:] + [None]:
                    if s is None or s != prev + 1:
                        meetings.append(
                            (_DAY_MAP[day_char], start, prev + 1, current_room or "")
                        )
                        if s is None:
                            break
                        start = s
                    prev = s
        else:
            current_room = tok if tok else current_room

    return False, meetings


def load_section(file_path: _Path_module) -> Optional[SectionFromFile]:
    """planner 상수 방식의 load_section"""
    try:
        d = _json_module.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    course_name = d.get("강의명", "")
    prof = d.get("교수명", "")
    credit = _safe_int_credits_planner(d.get("학점", 0))
    time_raw = d.get("강의시간", "") or ""
    eval_type = d.get("평가방식", "전체")

    mid = _safe_float_planner(d.get("중간고사", 0))
    final = _safe_float_planner(d.get("기말고사", 0))
    attend = _safe_float_planner(d.get("출석", 0))
    assign = _safe_float_planner(d.get("과제", 0))
    quiz = _safe_float_planner(d.get("퀴즈", 0))
    discuss = _safe_float_planner(d.get("토론", 0))
    etc = _safe_float_planner(d.get("기타", 0))

    is_web, meetings = _parse_time_slots_planner(time_raw)
    course_id = file_path.name.split(".")[0]

    return SectionFromFile(
        file_id=file_path.name,
        course_id=course_id,
        course_name=course_name,
        prof=prof,
        credit=credit,
        eval_type=eval_type,
        assign_pct=assign,
        quiz_pct=quiz,
        mid_pct=mid,
        final_pct=final,
        attend_pct=attend,
        discuss_pct=discuss,
        etc_pct=etc,
        time_raw=time_raw,
        is_web=is_web,
        meetings=meetings,
    )


def sections_for_course(course_id: str) -> List[SectionFromFile]:
    """planner 상수 방식의 sections_for_course"""
    out: List[SectionFromFile] = []
    for p in _iter_subject_files_for_planner(course_id):
        s = load_section(p)
        if s:
            out.append(s)
    return sorted(out, key=lambda x: x.file_id)


def load_depart() -> List[dict]:
    """학과 커리큘럼 로드"""
    try:
        return _json_module.loads(_DEPART_PATH_PLANNER.read_text(encoding="utf-8"))
    except Exception:
        return []


def _normalize_text_planner(x: Any) -> str:
    """텍스트 정규화 (NaN, None, 빈 값 처리)"""
    if x is None:
        return ""
    # NaN 처리
    try:
        import math

        if isinstance(x, float) and math.isnan(x):
            return ""
    except Exception:
        pass
    s = str(x).strip().lower()
    # 'nan' 문자열도 제거
    if s in ("nan", "none", "null", ""):
        return ""
    return str(x).strip()


def _match_isusigi(semester_token: str, isusigi: Any) -> bool:
    """
    semester_token: '1-1' .. '4-2'
    isusigi examples:
      - '1학년(1학기)'
      - '4학년(1,2학기)'
      - '4학년'   -> both terms
      - '전체'     -> all semesters
    """
    txt = _normalize_text_planner(isusigi)
    if not txt:
        return False
    if txt == "전체":
        return True

    m = _re_module.search(r"(\d)\s*학년(?:\s*\(([^)]*)\))?", txt)
    if not m:
        return False
    year = int(m.group(1))
    terms_raw = (m.group(2) or "").strip()

    y, t = semester_token.split("-")
    want_year = int(y)
    want_term = int(t)

    if year != want_year:
        return False

    if not terms_raw:
        return True  # '4학년' -> both terms allowed

    terms = [int(n) for n in _re_module.findall(r"\d", terms_raw)]
    if not terms:
        return False
    return want_term in terms


def list_major_required(semester_token: str) -> List[dict]:
    """전공필수 목록"""
    lst = []
    for d in load_depart():
        if _normalize_text_planner(d.get("종 별")) == "전공필수" and _match_isusigi(
            semester_token, d.get("이수시기")
        ):
            if _normalize_text_planner(d.get("학수번호")):
                lst.append(d)
    return lst


def list_major_elective(semester_token: str) -> List[dict]:
    """전공선택 목록"""
    lst = []
    for d in load_depart():
        if _normalize_text_planner(d.get("종 별")) == "전공선택" and _match_isusigi(
            semester_token, d.get("이수시기")
        ):
            if _normalize_text_planner(d.get("학수번호")):
                lst.append(d)
    return lst


def list_basic_focus(semester_token: str) -> List[dict]:
    """기초/중점 교양 목록"""
    lst = []
    for d in load_depart():
        if d.get("세부구분") in ("기초교양", "중점교양") and _match_isusigi(
            semester_token, d.get("이수시기")
        ):
            if _normalize_text_planner(d.get("학수번호")):
                lst.append(d)
    return lst


def core_category_map() -> Dict[Any, List[str]]:
    """핵심교양 카테고리 맵핑"""
    mapping: Dict[Any, List[str]] = {i: [] for i in range(1, 7)}

    # 핵심교양 1~6
    import unicodedata as _unicodedata

    try:
        for p in _COMMON_DIR_PLANNER.glob("*.json"):
            filename = p.name
            # 유니코드 정규화 후 비교 (NFC)
            filename_nfc = _unicodedata.normalize("NFC", filename)
            # "핵심교양"이 포함되어 있고 공학인증이 아닌 경우
            if "핵심교양" not in filename_nfc or "공학인증" in filename_nfc:
                continue
            name = filename_nfc
            # 정규식으로 카테고리 번호 추출 (핵심교양-1, 핵심교양-2 등)
            mm = _re_module.search(r"핵심교양[^\d]*(\d)", name)
            if not mm:
                continue
            cat = int(mm.group(1))
            try:
                arr = _json_module.loads(p.read_text(encoding="utf-8"))
                for d in arr:
                    code = _normalize_text_planner(
                        d.get("학수번호") or d.get("code") or d.get("course_code")
                    )
                    if code:
                        mapping[cat].append(code)
            except Exception:
                continue
    except Exception:
        pass

    # 창의.json -> '창의'
    creative_file = _COMMON_DIR_PLANNER / "창의.json"
    if creative_file.exists():
        try:
            arr = _json_module.loads(creative_file.read_text(encoding="utf-8"))
            mapping.setdefault("창의", [])
            for d in arr:
                code = str(
                    d.get("학수번호") or d.get("code") or d.get("course_code") or ""
                ).strip()
                if code:
                    mapping["창의"].append(code)
        except Exception:
            pass

    # 일반교양-7.SW·AI.json -> 'SW.AI'
    import unicodedata as _unicodedata_swai

    try:
        for p in _COMMON_DIR_PLANNER.glob("*.json"):
            filename = p.name
            # 유니코드 정규화 후 비교
            filename_nfc = _unicodedata_swai.normalize("NFC", filename)
            # "일반교양-7"이 포함되고 "SW"와 "AI"가 모두 포함된 경우
            if "일반교양-7" in filename_nfc or (
                "일반교양" in filename_nfc
                and "7" in filename_nfc
                and "SW" in filename_nfc
                and "AI" in filename_nfc
            ):
                try:
                    arr = _json_module.loads(p.read_text(encoding="utf-8"))
                    mapping.setdefault("SW.AI", [])
                    for d in arr:
                        code = _normalize_text_planner(
                            d.get("학수번호") or d.get("code") or d.get("course_code")
                        )
                        if code:
                            mapping["SW.AI"].append(code)
                except Exception:
                    continue
    except Exception:
        pass

    # Deduplicate preserving order for all keys
    for k in list(mapping.keys()):
        seen = set()
        uniq = []
        for c in mapping[k]:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        mapping[k] = uniq

    return mapping


def list_core_common() -> List[dict]:
    """핵심교양 목록"""
    out: List[dict] = []
    # 모든 JSON 파일을 검사하여 핵심교양 파일 찾기
    import unicodedata as _unicodedata

    try:
        for p in _COMMON_DIR_PLANNER.glob("*.json"):
            filename = p.name
            # 유니코드 정규화 후 비교 (NFC)
            filename_nfc = _unicodedata.normalize("NFC", filename)
            # "핵심교양"이 포함되어 있고 공학인증이 아닌 경우
            if "핵심교양" in filename_nfc and "공학인증" not in filename_nfc:
                try:
                    arr = _json_module.loads(p.read_text(encoding="utf-8"))
                    for d in arr:
                        # 학수번호가 유효한 항목만 포함
                        code = _normalize_text_planner(
                            d.get("학수번호") or d.get("code") or d.get("course_code")
                        )
                        if not code:
                            continue
                        d["_source_file"] = filename
                        out.append(d)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def list_general_common() -> List[dict]:
    """일반교양 목록"""
    out: List[dict] = []
    # 모든 JSON 파일을 검사하여 일반교양 파일 찾기
    import unicodedata as _unicodedata

    try:
        for p in _COMMON_DIR_PLANNER.glob("*.json"):
            filename = p.name
            # 유니코드 정규화 후 비교 (NFC)
            filename_nfc = _unicodedata.normalize("NFC", filename)
            # "일반교양"이 포함된 경우
            if "일반교양" in filename_nfc:
                try:
                    arr = _json_module.loads(p.read_text(encoding="utf-8"))
                    for d in arr:
                        # 학수번호가 유효한 항목만 포함
                        code = _normalize_text_planner(
                            d.get("학수번호") or d.get("code") or d.get("course_code")
                        )
                        if not code:
                            continue
                        d["_source_file"] = filename
                        out.append(d)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def normalize_eval_filters(eval_choice: str, assign_choice: str, quiz_choice: str):
    """평가 필터 정규화"""
    return eval_choice or "전체", assign_choice or "전체", quiz_choice or "전체"


def filter_and_sort_sections(
    sections: List[SectionFromFile],
    eval_choice: str,
    assign_choice: str,
    quiz_choice: str,
    credit_choice: str,
    sort_choice: str,
    web_choice: str = "전체",
) -> List[SectionFromFile]:
    """섹션 필터링 및 정렬"""
    e, a, q = normalize_eval_filters(eval_choice, assign_choice, quiz_choice)

    def keep(s: SectionFromFile) -> bool:
        if e != "전체" and s.eval_type != e:
            return False
        if a != "전체":
            has = s.assign_pct > 0
            if (a == "유" and not has) or (a == "무" and has):
                return False
        if q != "전체":
            has = s.quiz_pct > 0
            if (q == "유" and not has) or (q == "무" and has):
                return False
        if credit_choice != "전체":
            try:
                credit_val = int(credit_choice)
                if s.credit != credit_val:
                    return False
            except (ValueError, TypeError):
                pass
        if web_choice != "전체":
            if web_choice == "웹강" and not s.is_web:
                return False
            if web_choice == "일반" and s.is_web:
                return False
        return True

    out = [s for s in sections if keep(s)]
    if sort_choice == "과제 적은순":
        out.sort(key=lambda s: (s.assign_pct, s.file_id))
    elif sort_choice == "퀴즈 적은순":
        out.sort(key=lambda s: (s.quiz_pct, s.file_id))
    else:
        out.sort(key=lambda s: (s.course_id, s.file_id))
    return out


# 시간표 생성
def _conflicts_planner(a: SectionFromFile, b: SectionFromFile) -> bool:
    """시간 충돌 확인"""
    if a.is_web or b.is_web:
        return False
    for d1, s1, e1, _ in a.meetings:
        for d2, s2, e2, _ in b.meetings:
            if d1 != d2:
                continue
            if not (e1 <= s2 or e2 <= s1):
                return True
    return False


def _can_place_planner(current: List[SectionFromFile], cand: SectionFromFile) -> bool:
    """배치 가능 여부 확인"""
    return all(not _conflicts_planner(cand, x) for x in current)


def _group_by_course_planner(
    sections: List[SectionFromFile],
) -> Dict[str, List[SectionFromFile]]:
    """과목별 그룹화"""
    groups: Dict[str, List[SectionFromFile]] = {}
    for s in sections:
        groups.setdefault(s.course_id, []).append(s)
    for cid in list(groups.keys()):
        groups[cid].sort(key=lambda z: z.file_id)
    return groups


@dataclass
class ScheduleFromFile:
    """시간표 스케줄"""

    sections: List[SectionFromFile]
    total_credits: int


def generate_schedules(
    by_priority: Dict[int, List[SectionFromFile]],
    target_credits: int,
    core_credit_target: Optional[int] = None,
    limit: int = 30,
) -> List[ScheduleFromFile]:
    """시간표 생성"""
    # 빈 priority 제거 (효율성 향상)
    by_priority = {p: secs for p, secs in by_priority.items() if secs}
    if not by_priority:
        return []

    grouped = {p: _group_by_course_planner(secs) for p, secs in by_priority.items()}
    priorities = sorted(grouped.keys())
    best: List[ScheduleFromFile] = []

    # 디버깅: 입력 데이터 확인
    print(f"[DEBUG generate_schedules] Priorities: {priorities}")
    print(
        f"[DEBUG generate_schedules] Target credits: {target_credits}, Core target: {core_credit_target}"
    )
    for p in priorities:
        print(f"[DEBUG generate_schedules] Priority {p}: {len(grouped[p])} courses")

    def dfs(
        pi_idx: int,
        current: List[SectionFromFile],
        taken_courses: Set[str],
        total_credits: int,
        core_credits: int,
    ):
        nonlocal best
        if len(best) >= limit:
            return
        # 목표 학점을 초과하는 경우는 제외 (하지만 아직 priority를 다 처리하지 않았으면 계속 탐색 가능)
        # 단, 이미 너무 많이 초과했으면 제외 (목표 학점 + 3학점 이내는 허용)
        if total_credits > target_credits + 3:
            return
        if pi_idx >= len(priorities):
            # 현재 선택된 핵심교양 강의의 학점 합계 계산 (priority 4)
            current_core_credits = 0
            for s in current:
                for p, secs in by_priority.items():
                    if p == 4 and s in secs:
                        current_core_credits += s.credit
                        break

            # 핵심교양 학점 조건 확인: 설정된 경우 정확히 목표 학점이어야 함
            if core_credit_target is not None and core_credit_target > 0:
                if current_core_credits != core_credit_target:
                    print(
                        f"[DEBUG] Rejected: core credits {current_core_credits} != target {core_credit_target}, total_credits={total_credits}"
                    )
                    return

            # 총 학점 조건 확인: 정확히 목표 학점이어야 함
            if total_credits != target_credits:
                print(
                    f"[DEBUG] Rejected: total_credits {total_credits} != target {target_credits}, core_credits={current_core_credits}"
                )
                return

            # 모든 조건을 만족하면 시간표 추가
            print(
                f"[DEBUG] Accepted schedule: total_credits={total_credits}, core_credits={current_core_credits}"
            )
            best.append(
                ScheduleFromFile(sections=list(current), total_credits=total_credits)
            )
            return

        p = priorities[pi_idx]
        courses = list(grouped[p].items())  # (course_id, [sections])

        def backtrack_course(
            idx: int,
            curr: List[SectionFromFile],
            taken: Set[str],
            credits: int,
            core_cr: int,
        ):
            if len(best) >= limit:
                return
            # 목표 학점을 초과하는 경우는 제외 (하지만 아직 course를 다 처리하지 않았으면 계속 탐색 가능)
            # 단, 이미 너무 많이 초과했으면 제외 (목표 학점 + 3학점 이내는 허용)
            if credits > target_credits + 3:
                return
            if idx >= len(courses):
                dfs(pi_idx + 1, curr, taken, credits, core_cr)
                return

            course_id, sec_list = courses[idx]

            picked_any = False
            for s in sec_list:
                if course_id in taken:
                    continue
                if not _can_place_planner(curr, s):
                    continue
                new_core = core_cr + (s.credit if p == 4 else 0)
                # 핵심교양 학점 제한: 설정된 학점을 초과하지 않도록 (탐색 중에는 여유 허용)
                # 목표: 핵심교양이 정확히 목표 학점이어야 함
                if (
                    (p == 4)
                    and (core_credit_target is not None)
                    and (new_core > core_credit_target)
                ):
                    continue

                curr.append(s)
                taken.add(course_id)
                picked_any = True
                backtrack_course(idx + 1, curr, taken, credits + s.credit, new_core)
                taken.remove(course_id)
                curr.pop()

            # skip this course
            backtrack_course(idx + 1, curr, taken, credits, core_cr)

        backtrack_course(0, current, taken_courses, total_credits, core_credits)

    dfs(0, [], set(), 0, 0)

    print(f"[DEBUG generate_schedules] Found {len(best)} candidate schedules")
    if len(best) == 0:
        print(f"[DEBUG generate_schedules] No schedules found. Possible reasons:")
        print(f"  - Cannot find combination that sums to {target_credits} credits")
        if core_credit_target:
            print(
                f"  - Cannot find combination with exactly {core_credit_target} core credits"
            )
        print(f"  - Time conflicts prevent valid combinations")

    def priority_counts(schedule: ScheduleFromFile) -> Tuple[int, int, int, int, int]:
        counts = [0, 0, 0, 0, 0]
        for s in schedule.sections:
            for p, secs in by_priority.items():
                if s in secs:
                    counts[p - 1] += 1
                    break
        return tuple(counts)

    # Sort by priority counts (desc), then total credits (desc)
    best.sort(key=lambda sc: (priority_counts(sc), sc.total_credits), reverse=True)
    return best


def half_slot_to_time(slot_idx: int) -> Tuple[int, int]:
    """슬롯 인덱스를 시간으로 변환"""
    start_minutes = (_SLOT_START_HOUR * 60) + (slot_idx - 1) * _SLOT_MIN
    h = start_minutes // 60
    m = start_minutes % 60
    return h, m


# SUBJECT_DIR을 main.py에서 사용할 수 있도록 export
SUBJECT_DIR = _SUBJECT_DIR_PLANNER
