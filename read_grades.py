import pdfplumber
import os
import json
import re
from pathlib import Path


def is_course_code(text):
    """
    첫 번째 요소가 학수번호 형식(영어+숫자)인지 확인합니다.
    
    Args:
        text: 확인할 문자열
    
    Returns:
        학수번호 형식이면 True, 아니면 False
    """
    if not text:
        return False
    
    # 학수번호 형식: 영어 문자(대소문자)로 시작하고 숫자가 포함된 형식
    # 예: AIE1001, GEB1109, MTH1901 등
    pattern = r'^[A-Za-z]+[A-Za-z0-9]*\d+[A-Za-z0-9]*$'
    return bool(re.match(pattern, text))


def parse_grade_line(words):
    """
    행을 파싱해서 정리된 딕셔너리로 반환합니다.
    
    Args:
        words: 띄어쓰기로 분리된 단어 리스트
    
    Returns:
        딕셔너리: {'학수번호': ..., '학점': ..., '성적': ..., '분류': ...}
    """
    if len(words) < 4:
        return None
    
    # 첫번째: 학수번호
    course_code = words[0]
    
    # 마지막 3개: 학점(-3), 성적(-2), 분류(-1)
    credit = words[-3]
    grade = words[-2]
    category = words[-1]
    
    return {
        '학수번호': course_code,
        '학점': credit,
        '성적': grade,
        '분류': category
    }


def read_pdf(file_path, verbose=False):
    """
    PDF 파일을 읽어서 모든 텍스트를 추출하고, 각 행을 정리된 형식으로 파싱합니다.
    
    Args:
        file_path: PDF 파일 경로
        verbose: 상세 출력 여부
    
    Returns:
        정리된 과목 리스트 (딕셔너리 리스트)
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            if verbose:
                print(f"PDF 파일: {file_path}")
                print(f"총 페이지 수: {len(pdf.pages)}\n")
                print("=" * 80)
            
            all_courses = []
            
            # 각 페이지를 순회하며 텍스트 추출
            for page_num, page in enumerate(pdf.pages, start=1):
                if verbose:
                    print(f"\n[페이지 {page_num}]")
                    print("-" * 80)
                
                text = page.extract_text()
                if text:
                    # 텍스트를 행으로 나누기
                    lines = text.split('\n')
                    
                    # 필터링할 마지막 요소 목록
                    target_endings = ['교필', '교선', '전필', '전선', '기필']
                    
                    # 각 행을 띄어쓰기 기준으로 리스트로 나누기
                    for line_num, line in enumerate(lines, start=1):
                        if line.strip():  # 빈 행이 아닌 경우만
                            # 띄어쓰기로 분리
                            words = line.split()
                            
                            # 첫 번째 요소가 학수번호 형식이 아니면 제거
                            if words and not is_course_code(words[0]):
                                words = words[1:]  # 첫 번째 요소(한글 부분) 제거
                            
                            # 학수번호가 있는지 확인 (제거 후에도 요소가 있어야 함)
                            if not words or not is_course_code(words[0]):
                                continue
                            
                            # 마지막 요소가 필터링 대상인지 확인
                            if words[-1] in target_endings:
                                # 행을 파싱해서 정리
                                parsed = parse_grade_line(words)
                                if parsed:
                                    if verbose:
                                        print(f"행 {line_num}: {parsed}")
                                    all_courses.append(parsed)
                
                else:
                    if verbose:
                        print("(이 페이지에서 텍스트를 찾을 수 없습니다.)")
            
            if verbose:
                print("\n" + "=" * 80)
                print(f"\n정리된 과목 수: {len(all_courses)}")
                print("전체 텍스트 추출 완료!")
            
            # 정리된 과목 리스트를 반환
            return all_courses
            
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다: {file_path}")
        return []
    except Exception as e:
        print(f"오류 발생 ({file_path}): {str(e)}")
        return []


def process_directory(directory_path, output_file=None, verbose=False):
    """
    디렉토리 내의 모든 PDF 파일을 처리하여 JSON 파일로 저장합니다.
    
    Args:
        directory_path: PDF 파일들이 있는 디렉토리 경로
        output_file: 출력 JSON 파일 경로 (None이면 자동 생성)
        verbose: 상세 출력 여부
    
    Returns:
        저장된 JSON 파일 경로
    """
    # 디렉토리 경로 확인
    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"오류: 디렉토리를 찾을 수 없습니다: {directory_path}")
        return None
    
    if not dir_path.is_dir():
        print(f"오류: 경로가 디렉토리가 아닙니다: {directory_path}")
        return None
    
    # PDF 파일 찾기
    pdf_files = list(dir_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"경고: 디렉토리에 PDF 파일이 없습니다: {directory_path}")
        return None
    
    if verbose:
        print(f"찾은 PDF 파일 수: {len(pdf_files)}")
        print(f"디렉토리: {directory_path}\n")
    
    # 모든 PDF 파일 처리
    all_results = {}
    
    for pdf_file in pdf_files:
        if verbose:
            print(f"\n처리 중: {pdf_file.name}")
        
        courses = read_pdf(str(pdf_file), verbose=verbose)
        
        if courses:
            all_results[pdf_file.name] = {
                '파일명': pdf_file.name,
                '과목수': len(courses),
                '과목목록': courses
            }
            
            if verbose:
                print(f"  → {len(courses)}개 과목 추출 완료")
        else:
            if verbose:
                print(f"  → 추출된 과목 없음")
    
    # 출력 파일 경로 설정
    if output_file is None:
        output_file = dir_path / "grades_result.json"
    else:
        output_file = Path(output_file)
    
    # JSON 파일로 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 처리 완료: {len(pdf_files)}개 파일")
        print(f"✓ JSON 파일 저장: {output_file}")
        print(f"✓ 총 과목 수: {sum(data['과목수'] for data in all_results.values())}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 발생: {str(e)}")
        return None


if __name__ == "__main__":
    # 예시 사용법
    # 디렉토리 경로를 인자로 받거나 현재 디렉토리 사용
    import sys
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."  # 현재 디렉토리
    
    # 디렉토리 처리 및 JSON 저장
    process_directory(directory, verbose=True)
