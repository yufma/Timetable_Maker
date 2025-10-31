from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DepartmentCurriculum(Base):
    __tablename__ = "department_curriculum"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 예: 학년/학기, 영역(전공필수/선택 등), 비고 등
    year_term: Mapped[str] = mapped_column(String(50), index=True)
    track: Mapped[str] = mapped_column(String(100), index=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
