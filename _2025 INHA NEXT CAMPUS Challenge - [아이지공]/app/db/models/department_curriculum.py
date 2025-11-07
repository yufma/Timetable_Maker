from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DepartmentCurriculum(Base):
    __tablename__ = "department_curriculum"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 종 별: 교양필수/전공필수/전공선택 등
    type: Mapped[str] = mapped_column(String(50), index=True)
    # 세부구분: 학과(부)교양필수, 기초교양, NaN 등
    sub_category: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    # 이수시기: 예: 1학년(1학기), 전체 등
    year_term: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    # 학수번호
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    # 교과목명
    name: Mapped[str] = mapped_column(String(200), index=True)
    # 학점
    credit: Mapped[str | None] = mapped_column(String(20), nullable=True)
