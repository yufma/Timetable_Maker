import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Default to SQLite file in project root
DEFAULT_SQLITE_URL = "sqlite:///" + str(
    (Path(__file__).resolve().parents[2] / "app.db")
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# Input directories (optional; used by seed scripts)
# 환경변수가 없으면 프로젝트 내부 data/ 디렉토리 사용
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA_ROOT = _PROJECT_ROOT / "data"

COMMON_SUBJECTS_DIR = os.getenv("COMMON_SUBJECTS_DIR") or str(
    _DATA_ROOT / "common_subjects_json"
)
DEPARTMENT_CURRICULUM_DIR = os.getenv("DEPARTMENT_CURRICULUM_DIR") or str(
    _DATA_ROOT / "depart_json"
)
SUBJECTS_DIR = os.getenv("SUBJECTS_DIR") or str(_DATA_ROOT / "subject_json")

# PDF 파일 저장 디렉토리
SUBJECT_PDF_DIR = os.getenv("SUBJECT_PDF_DIR") or str(_DATA_ROOT / "subject_pdf")
DEPARTMENT_PDF_DIR = os.getenv("DEPARTMENT_PDF_DIR") or str(_DATA_ROOT / "department_pdf")