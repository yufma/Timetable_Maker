#!/usr/bin/env python3
"""PDF 파일을 DB에 저장하고 파일 시스템에도 복사"""
from pathlib import Path
import sys
import unicodedata

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.db.models.subject_pdf import SubjectPdf
from app.db.models.department_pdf import DepartmentPdf
from app.db.config import SUBJECT_PDF_DIR, DEPARTMENT_PDF_DIR
import shutil

def load_subject_pdfs(source_dir: str | None = None):
    """과목 PDF 파일 로드"""
    if source_dir is None:
        # 프로젝트 내부 data/subject_pdf 디렉토리 사용
        source_dir = str(Path(__file__).resolve().parents[1] / "data" / "subject_pdf")
    
    source_path = Path(source_dir)
    target_path = Path(SUBJECT_PDF_DIR)
    target_path.mkdir(parents=True, exist_ok=True)
    
    count = 0
    skipped = 0
    
    with SessionLocal() as db:
        for pdf_file in source_path.glob("*.pdf"):
            # 파일명에서 코드 추출 (예: AIE1002.001.pdf -> AIE1002.001)
            stem = pdf_file.stem
            
            # DB에 이미 있는지 확인
            existing = db.query(SubjectPdf).filter(SubjectPdf.subject_code == stem).first()
            if existing:
                skipped += 1
                continue
            
            # 파일 복사 (이미 있으면 스킵)
            dest_file = target_path / pdf_file.name
            if not dest_file.exists():
                shutil.copy2(pdf_file, dest_file)
            
            # DB에 저장 (파일 경로만 저장, 바이너리 데이터는 저장하지 않음 - 성능상 이유)
            pdf_record = SubjectPdf(
                subject_code=stem,
                filename=pdf_file.name,
                pdf_data=None,
                file_path=str(dest_file)
            )
            db.add(pdf_record)
            count += 1
            
            if count % 100 == 0:
                db.commit()
                print(f"  {count}개 저장 중...")
        
        db.commit()
    
    print(f"✅ Subject PDF: {count}개 저장, {skipped}개 건너뜀")


def load_department_pdfs(source_dir: str | None = None):
    """학과 PDF 파일 로드"""
    if source_dir is None:
        # 프로젝트 내부 data/department_pdf 디렉토리 사용
        source_dir = str(Path(__file__).resolve().parents[1] / "data" / "department_pdf")
    
    source_path = Path(source_dir)
    target_path = Path(DEPARTMENT_PDF_DIR)
    target_path.mkdir(parents=True, exist_ok=True)
    
    count = 0
    
    with SessionLocal() as db:
        for pdf_file in source_path.glob("*.pdf"):
            # 파일명에서 학과명 추출 (예: 인공지능공학과.pdf -> 인공지능공학과)
            stem = pdf_file.stem
            # NFC 정규화로 일관성 유지
            department_name = unicodedata.normalize('NFC', stem)
            
            # DB에 이미 있는지 확인
            existing = db.query(DepartmentPdf).filter(
                DepartmentPdf.department_name == department_name
            ).first()
            if existing:
                continue
            
            # 파일 복사 (이미 있으면 스킵)
            dest_file = target_path / pdf_file.name
            if not dest_file.exists():
                shutil.copy2(pdf_file, dest_file)
            
            # DB에 저장 (인공지능공학과는 25학년도로 설정)
            year = "2025" if department_name == "인공지능공학과" else None
            pdf_record = DepartmentPdf(
                department_name=department_name,
                year=year,
                curriculum_name=f"{department_name}교과과정표",
                filename=pdf_file.name,
                pdf_data=None,
                file_path=str(dest_file)
            )
            db.add(pdf_record)
            count += 1
        
        db.commit()
    
    print(f"✅ Department PDF: {count}개 저장")


def main():
    print("PDF 파일 로딩 시작...")
    load_department_pdfs()
    load_subject_pdfs()
    print("완료!")


if __name__ == "__main__":
    main()

