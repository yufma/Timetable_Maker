from pathlib import Path
import sys

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import delete
from app.db.session import SessionLocal
import app.db.models as models  # ensure models are imported


if __name__ == "__main__":
    with SessionLocal() as db:
        # Delete order is safe as we have no FKs
        db.execute(delete(models.CommonSubject))
        db.execute(delete(models.DepartmentCurriculum))
        db.execute(delete(models.Subject))
        db.commit()
        print({
            "cleared": [
                "common_subjects",
                "department_curriculum",
                "subjects",
            ]
        })
