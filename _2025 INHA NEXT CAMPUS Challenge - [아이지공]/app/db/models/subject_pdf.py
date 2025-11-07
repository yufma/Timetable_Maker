from sqlalchemy import String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SubjectPdf(Base):
    __tablename__ = "subject_pdfs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 과목 코드로 연결 (subject 테이블과 연결)
    subject_code: Mapped[str] = mapped_column(String(50), index=True, unique=True)

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





