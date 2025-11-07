from pathlib import Path
import sys

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models.common_subject import CommonSubject
from app.db.models.department_curriculum import DepartmentCurriculum
from app.db.models.subject import Subject
from app.db.models.subject_summary import SubjectSummary


def print_count_and_samples(session, model, name: str, sample: int = 3) -> None:
    total = session.scalar(select(func.count()).select_from(model))
    print(f"{name}: {total} rows")
    rows = session.execute(select(model).limit(sample)).scalars().all()
    for i, r in enumerate(rows, start=1):
        print(f"  {i}. {r.__dict__}")


if __name__ == "__main__":
    from sqlalchemy import func

    with SessionLocal() as db:
        print_count_and_samples(db, CommonSubject, "common_subjects")
        print_count_and_samples(db, DepartmentCurriculum, "department_curriculum")
        print_count_and_samples(db, Subject, "subjects")
        print_count_and_samples(db, SubjectSummary, "subject_summaries")




