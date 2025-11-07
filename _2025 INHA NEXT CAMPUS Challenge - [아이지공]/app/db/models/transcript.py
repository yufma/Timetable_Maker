# app/db/models/transcript.py
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Transcript(Base):
    """학생의 성적표 정보 (PDF 업로드 시 저장)"""
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False, index=True)  # users 테이블 참조 (FK 제약 없음)
    
    # PDF 메타데이터
    original_filename = Column(String, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # 추출된 텍스트
    raw_text = Column(Text, nullable=True)
    
    # 파싱된 수강 내역 (JSON)
    courses_data = Column(JSON, nullable=True)
    """
    JSON 구조 예시:
    {
        "total_credits": 120,
        "gpa": 3.8,
        "courses": [
            {
                "year": "2023",
                "semester": "1학기",
                "course_code": "AIE1001",
                "course_name": "인공지능의 이해",
                "credit": 3,
                "grade": "A+",
                "professor": "홍길동"
            },
            ...
        ]
    }
    """
    
    # 통계 정보
    total_credits = Column(Float, nullable=True)
    gpa = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CourseHistory(Base):
    """수강 이력 (Transcript에서 파싱된 개별 과목)"""
    __tablename__ = "course_history"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)  # users 테이블 참조 (FK 제약 없음)
    
    # 과목 정보
    year = Column(String, nullable=False)  # "2023"
    semester = Column(String, nullable=False)  # "1학기", "2학기", "여름학기", "겨울학기"
    course_code = Column(String, nullable=False, index=True)  # "AIE1001"
    course_name = Column(String, nullable=False)
    credit = Column(Float, nullable=False)
    grade = Column(String, nullable=True)  # "A+", "A0", "B+", etc.
    professor = Column(String, nullable=True)
    
    # 추가 정보
    is_major = Column(String, nullable=True)  # "전공필수", "전공선택", "교양", etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

