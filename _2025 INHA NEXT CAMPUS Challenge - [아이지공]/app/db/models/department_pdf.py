from sqlalchemy import String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DepartmentPdf(Base):
    __tablename__ = "department_pdfs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 학과명
    department_name: Mapped[str] = mapped_column(String(100), index=True)

    # 연도 (예: 2025)
    year: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    # 교과과정표 정보
    curriculum_name: Mapped[str] = mapped_column(
        String(200), nullable=True
    )  # 교과과정표 이름

    # PDF 파일 데이터
    filename: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # 원본 파일명
    pdf_data: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )  # PDF 바이너리 데이터
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # 파일 시스템 경로
