import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Default to SQLite file in project root
DEFAULT_SQLITE_URL = "sqlite:///" + str((Path(__file__).resolve().parents[2] / "app.db"))

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# Input directories (optional; used by seed scripts)
COMMON_SUBJECTS_DIR = os.getenv("COMMON_SUBJECTS_DIR")
DEPARTMENT_CURRICULUM_DIR = os.getenv("DEPARTMENT_CURRICULUM_DIR")
SUBJECTS_DIR = os.getenv("SUBJECTS_DIR")
