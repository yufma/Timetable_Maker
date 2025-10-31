from pathlib import Path
import sys

# Ensure project root is on sys.path so `app` package is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.config import (
    COMMON_SUBJECTS_DIR,
    DEPARTMENT_CURRICULUM_DIR,
    SUBJECTS_DIR,
)
from app.db.seed.load_json import (
    load_common_subjects,
    load_department_curriculum,
    load_subjects,
)
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as db:
        c1 = load_common_subjects(db, COMMON_SUBJECTS_DIR)
        c2 = load_department_curriculum(db, DEPARTMENT_CURRICULUM_DIR)
        c3 = load_subjects(db, SUBJECTS_DIR)
        print(
            {
                "common_subjects": c1,
                "department_curriculum": c2,
                "subjects": c3,
            }
        )


if __name__ == "__main__":
    main()
