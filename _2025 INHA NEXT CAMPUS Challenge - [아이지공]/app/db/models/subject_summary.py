
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SubjectSummary(Base):
    __tablename__ = "subject_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 과목 코드로 연결 (subject 테이블과 연결)
    subject_code: Mapped[str] = mapped_column(String(50), index=True, unique=True)

    # 강의계획서 상세 정보
    lecture_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # 강의명
    professor: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 교수명
    credit: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 학점 (예: "3.0")
    schedule_time: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # 강의시간
    evaluation_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 평가방식

    # 평가 비율
    midterm: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 중간고사 (%)
    final: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 기말고사 (%)
    attendance: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 출석 (%)
    assignment: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 과제 (%)
    quiz: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 퀴즈 (%)
    discussion: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 토론 (%)
    etc: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 기타 (%)
