from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FavoriteLecture(Base):
    """찜한 강의"""
    __tablename__ = "favorite_lectures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 외래키 제약조건 제거 (SQLModel과 호환성 문제)
    subject_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    # 추가 정보 (JSON 형태로 저장 가능)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


class FavoriteProfessor(Base):
    """찜한 교수님"""
    __tablename__ = "favorite_professors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 외래키 제약조건 제거 (SQLModel과 호환성 문제)
    professor_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


class FavoriteSchedule(Base):
    """찜한 시간표"""
    __tablename__ = "favorite_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 외래키 제약조건 제거 (SQLModel과 호환성 문제)
    schedule_name: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 사용자가 지정한 시간표 이름
    schedule_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 형태로 시간표 데이터 저장
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
