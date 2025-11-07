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
    from sqlalchemy.exc import OperationalError
    
    with SessionLocal() as db:
        cleared = []
        tables_to_clear = [
            (models.CommonSubject, "common_subjects"),
            (models.DepartmentCurriculum, "department_curriculum"),
            (models.Subject, "subjects"),
            (models.SubjectSummary, "subject_summaries"),
        ]
        
        for model, name in tables_to_clear:
            try:
                db.execute(delete(model))
                cleared.append(name)
            except OperationalError as e:
                # 테이블이 없으면 무시 (아직 생성되지 않은 경우)
                if "no such table" in str(e):
                    pass
                else:
                    raise
        
        db.commit()
        print({
            "cleared": cleared,
            "skipped": [name for _, name in tables_to_clear if name not in cleared],
        })




