from pathlib import Path
import sys

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.db.models.common_subject import CommonSubject
from app.db.models.department_curriculum import DepartmentCurriculum
from app.db.models.subject import Subject
from app.db.models.subject_summary import SubjectSummary


def print_table_summary(db, model, name: str, sample: int = 5):
    """테이블 통계와 샘플 출력"""
    total = db.scalar(select(func.count()).select_from(model))
    print(f"\n{'='*80}")
    print(f"📊 {name}: 총 {total}개")
    print('='*80)
    
    rows = db.execute(select(model).limit(sample)).scalars().all()
    for i, row in enumerate(rows, start=1):
        print(f"\n{i}. {row.__dict__}")


def print_common_subjects(db):
    """CommonSubject 상세 정보"""
    print("\n" + "="*80)
    print("📚 CommonSubject (교양 과목)")
    print("="*80)
    
    # 카테고리별 통계
    categories = db.execute(
        select(CommonSubject.category, func.count()).group_by(CommonSubject.category)
    ).all()
    
    print("\n카테고리별 통계:")
    for cat, count in categories:
        print(f"  - {cat}: {count}개")
    
    # 샘플 5개
    print("\n샘플 5개:")
    samples = db.execute(select(CommonSubject).limit(5)).scalars().all()
    for i, cs in enumerate(samples, 1):
        print(f"\n  {i}. {cs.code} - {cs.name}")
        print(f"     구분: {cs.category} | 영역: {cs.area}")
        print(f"     주관학과: {cs.department}")
        print(f"     학점: {cs.credit} | 인정종별: {cs.recognition_type}")


def print_department_curriculum(db):
    """DepartmentCurriculum 상세 정보"""
    print("\n" + "="*80)
    print("📋 DepartmentCurriculum (교과과정표)")
    print("="*80)
    
    # 종별별 통계
    types = db.execute(
        select(DepartmentCurriculum.type, func.count()).group_by(DepartmentCurriculum.type)
    ).all()
    
    print("\n종별별 통계:")
    for t, count in types:
        print(f"  - {t}: {count}개")
    
    # 샘플 5개
    print("\n샘플 5개:")
    samples = db.execute(select(DepartmentCurriculum).limit(5)).scalars().all()
    for i, dc in enumerate(samples, 1):
        print(f"\n  {i}. {dc.name}")
        print(f"     종별: {dc.type} | 세부구분: {dc.sub_category}")
        print(f"     학수번호: {dc.code} | 이수시기: {dc.year_term}")
        print(f"     학점: {dc.credit}")


def print_subjects(db):
    """Subject 상세 정보"""
    print("\n" + "="*80)
    print("📖 Subject (전공/기초교양 과목)")
    print("="*80)
    
    total = db.scalar(select(func.count()).select_from(Subject))
    print(f"\n총 {total}개")
    
    # 샘플 5개
    print("\n샘플 5개:")
    samples = db.execute(select(Subject).limit(5)).scalars().all()
    for i, s in enumerate(samples, 1):
        print(f"  {i}. {s.code} - {s.name} ({s.category})")


def print_subject_summaries(db):
    """SubjectSummary 상세 정보"""
    print("\n" + "="*80)
    print("📝 SubjectSummary (강의계획서 요약)")
    print("="*80)
    
    total = db.scalar(select(func.count()).select_from(SubjectSummary))
    print(f"\n총 {total}개")
    
    # 상세 정보가 있는 것 개수
    with_details = db.execute(
        select(func.count()).select_from(SubjectSummary)
        .where(SubjectSummary.lecture_name.isnot(None))
    ).scalar()
    
    print(f"상세 정보 포함: {with_details}개")
    
    # 샘플 3개
    print("\n샘플 3개:")
    samples = db.execute(select(SubjectSummary).limit(3)).scalars().all()
    for i, ss in enumerate(samples, 1):
        print(f"\n  {i}. {ss.subject_code}")
        print(f"     강의명: {ss.lecture_name}")
        print(f"     교수명: {ss.professor}")
        print(f"     학점: {ss.credit} | 강의시간: {ss.schedule_time}")
        print(f"     평가방식: {ss.evaluation_method}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔍 DB 적재 상태 확인")
    print("="*80)
    
    with SessionLocal() as db:
        print_common_subjects(db)
        print_department_curriculum(db)
        print_subjects(db)
        print_subject_summaries(db)
        
        print("\n" + "="*80)
        print("✅ 확인 완료!")
        print("="*80)
        print("\n💡 이 스크립트를 다시 실행하려면:")
        print("   python scripts/check_db.py\n")

