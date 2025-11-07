from pathlib import Path
import sys
import json
from typing import Iterable, Optional

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models.subject import Subject
from app.db.models.common_subject import CommonSubject
from app.db.models.department_curriculum import DepartmentCurriculum
from app.db.config import SUBJECTS_DIR

EXPORT_DIR = PROJECT_ROOT / "exports"
SUBJECT_DIR = EXPORT_DIR / "subjects"


def ensure_dirs() -> None:
    SUBJECT_DIR.mkdir(parents=True, exist_ok=True)


def get_curriculum_map(session) -> dict[str, list[DepartmentCurriculum]]:
    result: dict[str, list[DepartmentCurriculum]] = {}
    rows = session.execute(select(DepartmentCurriculum)).scalars().all()
    for r in rows:
        result.setdefault(r.code or "", []).append(r)
    return result


def get_common_map(session) -> dict[str, list[CommonSubject]]:
    result: dict[str, list[CommonSubject]] = {}
    rows = session.execute(select(CommonSubject)).scalars().all()
    for r in rows:
        result.setdefault(r.code, []).append(r)
    return result


def find_subject_json_path(code: str) -> Optional[Path]:
    # 여러 경로를 시도 (환경변수 → 일반 경로)
    search_roots = []
    if SUBJECTS_DIR:
        search_roots.append(Path(SUBJECTS_DIR))
    # 기본 경로 추가 (fallback)
    search_roots.append(
        Path("/Users/choeseong-yong/Downloads/common_subjects_pdf/subject_json")
    )

    for root in search_roots:
        if not root.exists():
            continue
        # 파일명은 보통 <코드>.json 형식. 일부는 점(.) 대신 대시(-)를 사용할 수 있음.
        candidates = [
            root / f"{code}.json",
            root / f"{code.replace('.', '-')}.json",
        ]
        for p in candidates:
            if p.exists():
                return p
        # fallback: 접두어 매칭 (예: "AIE1002"로 시작하는 파일 찾기)
        base_code = code.split(".")[0] if "." in code else code
        globs = list(root.glob(f"{base_code}*.json"))
        if globs:
            # 정확히 일치하는 것을 우선
            exact_match = next((g for g in globs if g.stem == code), None)
            if exact_match:
                return exact_match
            # 없으면 첫 번째
            return globs[0]
    return None


def read_subject_json(code: str) -> dict:
    path = find_subject_json_path(code)
    if not path:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_details_list(raw: dict) -> list[tuple[str, str]]:
    def g(k: str) -> str:
        v = raw.get(k)
        return str(v) if v is not None else ""

    return [
        ("강의명", g("강의명")),
        ("교수명", g("교수명")),
        ("학점", g("학점")),
        ("강의시간", g("강의시간")),
        ("평가방식", g("평가방식")),
        ("중간고사", g("중간고사")),
        ("기말고사", g("기말고사")),
        ("출석", g("출석")),
        ("과제", g("과제")),
        ("퀴즈", g("퀴즈")),
        ("토론", g("토론")),
        ("기타", g("기타")),
    ]


def subject_markdown(
    s: Subject, commons: list[CommonSubject], curris: list[DepartmentCurriculum]
) -> str:
    raw = read_subject_json(s.code)
    lines = []
    lines.append(f"# {s.name} ({s.code})")
    lines.append("")

    # 상세(원본 JSON에서 수집)
    if raw:
        fields = build_details_list(raw)
        for k, v in fields:
            if v:
                lines.append(f"- {k}: {v}")
    else:
        lines.append("> 원본 subject_json을 찾지 못했습니다.")

    return "\n".join(lines)


def subject_html(
    s: Subject, commons: list[CommonSubject], curris: list[DepartmentCurriculum]
) -> str:
    raw = read_subject_json(s.code)

    detail_rows = ""
    if raw:
        fields = build_details_list(raw)
        for k, v in fields:
            if v:
                detail_rows += f"<tr><th>{k}</th><td>{v}</td></tr>\n"
    else:
        detail_rows = (
            "<tr><td colspan='2'>&gt; 원본 subject_json을 찾지 못했습니다.</td></tr>"
        )

    return f"""
<!doctype html>
<meta charset='utf-8'>
<title>{s.name} ({s.code})</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:16px;}}
.container{{max-width:900px;margin:0 auto;}}
h1{{margin-bottom:16px;}}
.table{{border-collapse:collapse;width:100%;}}
.table th,.table td{{border:1px solid #ddd;padding:8px;text-align:left;}}
.table th{{background:#f7f7f7;width:180px;}}
.a{{color:#0366d6;text-decoration:none;margin-bottom:16px;display:inline-block;}}
</style>
<div class='container'>
  <a class='a' href='../index.html'>&larr; 목록으로</a>
  <h1>{s.name} <small>({s.code})</small></h1>
  <table class='table'>
    {detail_rows}
  </table>
</div>
"""


def subject_html_table_row(
    s: Subject, commons: list[CommonSubject], curris: list[DepartmentCurriculum]
) -> str:
    common_txt = (
        ", ".join(sorted({f"{c.category}/{c.area}" for c in commons}))
        if commons
        else ""
    )
    curri_txt = (
        ", ".join(
            sorted(
                {
                    f"{c.type}{(' ('+c.year_term+')') if c.year_term else ''}"
                    for c in curris
                }
            )
        )
        if curris
        else ""
    )
    html_path = f"subjects/{s.code}.html"
    return f"<tr><td><a href='{html_path}'>{s.code}</a></td><td>{s.name}</td><td>{s.category}</td><td>{common_txt}</td><td>{curri_txt}</td></tr>"


def main() -> None:
    ensure_dirs()
    with SessionLocal() as db:
        commons_map = get_common_map(db)
        curri_map = get_curriculum_map(db)
        subjects = db.execute(select(Subject).order_by(Subject.code)).scalars().all()

        # Per-subject markdown + html
        for s in subjects:
            md = subject_markdown(
                s, commons_map.get(s.code, []), curri_map.get(s.code, [])
            )
            (SUBJECT_DIR / f"{s.code}.md").write_text(md, encoding="utf-8")

            html = subject_html(
                s, commons_map.get(s.code, []), curri_map.get(s.code, [])
            )
            (SUBJECT_DIR / f"{s.code}.html").write_text(html, encoding="utf-8")

        # Index HTML
        rows: list[str] = []
        for s in subjects:
            rows.append(
                subject_html_table_row(
                    s, commons_map.get(s.code, []), curri_map.get(s.code, [])
                )
            )
        html = """
<!doctype html>
<meta charset='utf-8'>
<title>강의계획서 요약 인덱스</title>
<style>
body { font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; padding: 16px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; }
th { background: #f7f7f7; text-align: left; }
tr:nth-child(even) { background: #fafafa; }
code { background: #f2f2f2; padding: 2px 4px; border-radius: 4px; }
</style>
<h1>강의계획서 요약 인덱스</h1>
<p>각 과목의 기본 정보와 교양/교과과정 연계 정보를 제공합니다. 과목 코드를 클릭하면 상세 페이지로 이동합니다.</p>
<table>
  <thead>
    <tr>
      <th>코드</th>
      <th>과목명</th>
      <th>분류</th>
      <th>교양 연계</th>
      <th>교과과정 연계</th>
    </tr>
  </thead>
  <tbody>
    ROWS_PLACEHOLDER
  </tbody>
</table>
""".replace(
            "ROWS_PLACEHOLDER", "\n".join(rows)
        )
        (EXPORT_DIR / "index.html").write_text(html, encoding="utf-8")
        print({"subjects": len(subjects), "export_dir": str(EXPORT_DIR)})


if __name__ == "__main__":
    main()
