# app.models.py
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):  # table 있으면, DB table로 생성
    __tablename__ = "users"  # DB table name

    student_id: int = Field(primary_key=True, index=True, description="학번")
    name: str = Field(nullable=False, description="이름")
    major: Optional[str] = Field(default=None, description="전공")  # 추가
    password_hash: str = Field(nullable=False, description="비밀번호 해시")


# class Course(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     professor: str
#     day_of_week: str
#     start_time: str
#     end_time: str
#     credit: int
#     major_required: bool
