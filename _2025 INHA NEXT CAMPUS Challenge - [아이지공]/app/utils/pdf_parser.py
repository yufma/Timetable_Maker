# app/utils/pdf_parser.py
import pdfplumber
import re
import json
from typing import Dict, List, Optional
from io import BytesIO


def extract_text_from_pdf(pdf_file: bytes) -> str:
    """PDF 파일에서 텍스트 추출"""
    try:
        with pdfplumber.open(BytesIO(pdf_file)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"PDF 텍스트 추출 오류: {e}")
        return ""


def parse_transcript(text: str) -> Dict:
    """
    성적표 텍스트를 파싱하여 JSON 형식으로 변환
    
    성적표 형식 예시:
    2023학년도 1학기
    AIE1001  인공지능의 이해  3  A+  홍길동
    ...
    """
    result = {
        "total_credits": 0.0,
        "major_credits": 0.0,  # 주전공(필/선) 학점
        "gpa": 0.0,
        "courses": []
    }
    
    lines = text.split('\n')
    current_year = None
    current_semester = None
    
    # 학점과 성적 패턴
    credit_pattern = re.compile(r'(\d+\.?\d*)\s*학점')
    gpa_pattern = re.compile(r'평점\s*[평균]*\s*[:=]?\s*(\d+\.\d+)')
    
    # 과목 정보 패턴 (학수번호, 과목명, 학점, 성적, 교수/구분)
    # 예: AIE1001 인공지능의 이해 3 A+ 홍길동
    # 예: AIE1004 인공지능창의설계 3.0 B+ 전선
    course_pattern = re.compile(
        r'([A-Z]{3}\d{4})\s+'  # 학수번호
        r'(.+?)\s+'            # 과목명
        r'(\d+\.?\d*)\s+'      # 학점
        r'([A-F][+0]?|P|NP|W|RE)\s*'  # 성적 (RE 포함)
        r'(.+)?'               # 교수/구분 (전선, 전필 등)
    )
    
    # 학년도/학기 패턴
    semester_pattern = re.compile(r'(\d{4})[학년도]*\s*(\d+학기|여름학기|겨울학기)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 학년도/학기 찾기
        semester_match = semester_pattern.search(line)
        if semester_match:
            current_year = semester_match.group(1)
            current_semester = semester_match.group(2)
            continue
        
        # 주전공(필/선) 학점 찾기
        # 형식: 주전공(필/선) 24(15/9) 또는 주전공(필 / 선) 24(15 / 9)
        # 테이블 형식에서도 찾을 수 있도록 개선
        major_pattern = re.compile(r'주전공\s*\(필\s*[/／]\s*선\)\s*[:：]?\s*(\d+\.?\d*)(?:\s*\([^)]+\))?')
        major_match = major_pattern.search(line)
        if major_match:
            try:
                result["major_credits"] = float(major_match.group(1))
            except:
                pass
        
        # 취득학점(B) 찾기 (테이블 형식에서 정확히 매칭)
        # 형식: 취득학점(B) 61
        acquired_pattern = re.compile(r'취득학점\s*\(B\)\s*[:：]?\s*(\d+\.?\d*)')
        acquired_match = acquired_pattern.search(line)
        if acquired_match:
            try:
                result["total_credits"] = float(acquired_match.group(1))
            except:
                pass
        
        # 취득학점(R)도 지원 (R이 있으면 R 우선)
        acquired_r_pattern = re.compile(r'취득학점\s*\(R\)\s*[:：]?\s*(\d+\.?\d*)')
        acquired_r_match = acquired_r_pattern.search(line)
        if acquired_r_match:
            try:
                result["total_credits"] = float(acquired_r_match.group(1))
            except:
                pass
        
        # 총 이수학점 찾기 (취득학점(B)가 없을 때만)
        if result["total_credits"] == 0.0:
            credit_match = credit_pattern.search(line)
            if credit_match and '이수' in line:
                try:
                    result["total_credits"] = float(credit_match.group(1))
                except:
                    pass
        
        # 평점 찾기
        gpa_match = gpa_pattern.search(line)
        if gpa_match:
            try:
                result["gpa"] = float(gpa_match.group(1))
            except:
                pass
        
        # 과목 정보 파싱
        course_match = course_pattern.match(line)
        if course_match and current_year and current_semester:
            grade = course_match.group(4)
            # RE(재수강)이면 제외
            if grade == "RE" or "RE" in line.upper():
                continue
            
            rest_text = course_match.group(5).strip() if course_match.group(5) else ""
            
            # 전선, 전필 구분 찾기
            course_type = None
            professor = ""
            
            if "전선" in rest_text:
                course_type = "전공선택"
                professor = rest_text.replace("전선", "").strip()
            elif "전필" in rest_text:
                course_type = "전공필수"
                professor = rest_text.replace("전필", "").strip()
            else:
                course_type = "교양"
                professor = rest_text
            
            course = {
                "year": current_year,
                "semester": current_semester,
                "course_code": course_match.group(1),
                "course_name": course_match.group(2).strip(),
                "credit": float(course_match.group(3)),
                "grade": grade,
                "professor": professor,
                "course_type": course_type  # 전선, 전필, 교양
            }
            result["courses"].append(course)
    
    return result


def parse_transcript_flexible(text: str) -> Dict:
    """
    더 유연한 성적표 파싱 (다양한 형식 지원)
    대학교마다 성적표 형식이 다를 수 있으므로 여러 패턴을 시도
    """
    result = {
        "total_credits": 0.0,
        "major_credits": 0.0,  # 주전공(필/선) 학점
        "gpa": 0.0,
        "courses": []
    }
    
    # 먼저 PDF 하단부에서 주전공(필/선)과 취득학점(B) 찾기 (우선순위 높음)
    # 여러 줄에 걸쳐 있을 수 있으므로 전체 텍스트에서 검색
    # 형식: 주전공(필/선) 24(15/9) 또는 주전공(필 / 선) 24(15 / 9)
    # 테이블 형식에서는 탭이나 여러 공백으로 구분될 수 있음
    
    # 주전공(필/선) 찾기 - 직접적인 문자열 검색 + 정규식
    # 형식: 주전공(필/선) 24(15/9) → 24 추출
    # 먼저 "주전공"과 "필"과 "선"이 포함된 라인 찾기
    lines = text.split('\n')
    for line in lines:
        if '주전공' in line and '필' in line and '선' in line:
            # "주전공(필/선)" 또는 "주전공(필 / 선)" 패턴 찾기
            # 그 다음에 나오는 숫자 (괄호 앞의 숫자, 24(15/9)에서 24 추출)
            # 패턴 1: 주전공(필/선) 24(15/9) 형식
            pattern = re.compile(r'주전공\s*\(필\s*[/／]\s*선\)\s*(\d+\.?\d*)(?:\([^)]+\))?')
            match = pattern.search(line)
            if match:
                try:
                    value = float(match.group(1))
                    result["major_credits"] = value
                    print(f"[DEBUG] 주전공(필/선) 학점 파싱 성공: {value}")
                    print(f"[DEBUG] 매칭된 라인: {line.strip()}")
                    break
                except:
                    continue
            # 패턴 2: "선)" 다음에 나오는 첫 번째 숫자 (괄호 앞)
            major_idx = line.find('주전공')
            if major_idx >= 0:
                after_major = line[major_idx:]
                # "선)" 다음에 나오는 숫자 찾기 (괄호 안 제외)
                pattern2 = re.compile(r'선\s*\)\s*(\d+\.?\d*)(?:\([^)]+\))?')
                match2 = pattern2.search(after_major)
                if match2:
                    try:
                        value = float(match2.group(1))
                        result["major_credits"] = value
                        print(f"[DEBUG] 주전공(필/선) 학점 파싱 성공 (대체 방법): {value}")
                        print(f"[DEBUG] 매칭된 라인: {line.strip()}")
                        break
                    except:
                        continue
            # 패턴 3: 주전공(필/선) 다음 숫자 찾기 (가장 간단한 방법)
            pattern3 = re.compile(r'주전공.*?필.*?선.*?\)\s*(\d+\.?\d*)')
            match3 = pattern3.search(line)
            if match3:
                try:
                    value = float(match3.group(1))
                    result["major_credits"] = value
                    print(f"[DEBUG] 주전공(필/선) 학점 파싱 성공 (패턴 3): {value}")
                    print(f"[DEBUG] 매칭된 라인: {line.strip()}")
                    break
                except:
                    continue
    
    # 정규식 패턴도 시도 (이전 방식) - 괄호 안 숫자 무시
    if result["major_credits"] == 0.0:
        major_patterns = [
            re.compile(r'주전공\s*\(필\s*[/／]\s*선\)[\s\t:：]+(\d+\.?\d*)(?:\([^)]+\))?'),  # 괄호 포함, 뒤 괄호 무시
            re.compile(r'주전공\s*\(필[/／]선\)[\s\t:：]+(\d+\.?\d*)(?:\([^)]+\))?'),  # 공백 없음
            re.compile(r'주전공\s*\(필\s*[/／]\s*선\)\s*(\d+\.?\d*)(?:\([^)]+\))?'),  # 간단한 패턴
            re.compile(r'주전공.*?필.*?선.*?\)\s*(\d+\.?\d*)'),  # 가장 유연한 패턴 - ) 다음 숫자
        ]
        
        for i, pattern in enumerate(major_patterns):
            major_match = pattern.search(text)
            if major_match:
                try:
                    value = float(major_match.group(1))
                    result["major_credits"] = value
                    print(f"[DEBUG] 주전공(필/선) 학점 파싱 성공 (정규식 패턴 {i+1}): {value}")
                    break
                except:
                    continue
    
    if result["major_credits"] == 0.0:
        print(f"[DEBUG] 주전공(필/선) 파싱 실패 - '주전공' 포함 라인:")
        for line in lines:
            if '주전공' in line:
                print(f"  {line.strip()}")
    
    # 취득학점(B) 찾기 - 전체학점으로 사용
    # 먼저 "취득학점"과 "B"가 포함된 라인 찾기
    for line in lines:
        if '취득학점' in line and 'B' in line:
            # "취득학점(B)" 패턴 찾기
            pattern = re.compile(r'취득학점\s*\(B\)\s*(\d+\.?\d*)')
            match = pattern.search(line)
            if match:
                try:
                    value = float(match.group(1))
                    result["total_credits"] = value
                    print(f"[DEBUG] 취득학점(B) 파싱 성공: {value}")
                    print(f"[DEBUG] 매칭된 라인: {line.strip()}")
                    break
                except:
                    continue
            # 패턴이 정확히 매칭되지 않으면, B) 다음 숫자 찾기
            b_idx = line.find('B')
            if b_idx >= 0:
                # "B)" 다음에 나오는 숫자 찾기
                after_b = line[b_idx:]
                pattern2 = re.compile(r'B\s*\)\s*(\d+\.?\d*)')
                match2 = pattern2.search(after_b)
                if match2:
                    try:
                        value = float(match2.group(1))
                        result["total_credits"] = value
                        print(f"[DEBUG] 취득학점(B) 파싱 성공 (대체 방법): {value}")
                        print(f"[DEBUG] 매칭된 라인: {line.strip()}")
                        break
                    except:
                        continue
    
    # 정규식 패턴도 시도 (이전 방식)
    if result["total_credits"] == 0.0:
        acquired_patterns = [
            re.compile(r'취득학점\s*\(B\)[\s\t:：]+(\d+\.?\d*)'),  # 탭/공백/콜론으로 구분
            re.compile(r'취득학점\s*\(B\)\s*(\d+\.?\d*)'),  # 간단한 패턴
            re.compile(r'취득학점.*?B.*?(\d+\.?\d*)'),  # 더 유연한 패턴
        ]
        
        for i, pattern in enumerate(acquired_patterns):
            acquired_match = pattern.search(text)
            if acquired_match:
                try:
                    value = float(acquired_match.group(1))
                    result["total_credits"] = value
                    print(f"[DEBUG] 취득학점(B) 파싱 성공 (정규식 패턴 {i+1}): {value}")
                    break
                except:
                    continue
    
    if result["total_credits"] == 0.0:
        print(f"[DEBUG] 취득학점(B) 파싱 실패 - '취득학점' 포함 라인:")
        for line in lines:
            if '취득학점' in line:
                print(f"  {line.strip()}")
    
    # 취득학점(R)도 지원 (B가 없으면 R 사용)
    if result["total_credits"] == 0.0:
        acquired_r_patterns = [
            re.compile(r'취득학점\s*\(R\)\s*[:：]?\s*(\d+\.?\d*)'),
            re.compile(r'취득학점\s*\(R\)\s+(\d+\.?\d*)'),
        ]
        for pattern in acquired_r_patterns:
            acquired_r_match = pattern.search(text)
            if acquired_r_match:
                try:
                    result["total_credits"] = float(acquired_r_match.group(1))
                    print(f"[DEBUG] 취득학점(R) 파싱 성공: {result['total_credits']}")
                    break
                except:
                    continue
    
    # 기본 파서 시도 (과목 정보 파싱)
    basic_result = parse_transcript(text)
    if basic_result["courses"]:
        result["courses"] = basic_result["courses"]
        result["gpa"] = basic_result.get("gpa", 0.0)
        # 하단부에서 찾은 값이 없으면 기본 파서 결과 사용
        if result["major_credits"] == 0.0:
            result["major_credits"] = basic_result.get("major_credits", 0.0)
        if result["total_credits"] == 0.0:
            result["total_credits"] = basic_result.get("total_credits", 0.0)
    
    # 기본 파서에서 과목이 없으면 다른 형식 시도 (탭으로 구분된 경우)
    if not result["courses"]:
        lines = text.split('\n')
        current_year = None
        current_semester = None
        
        for line in lines:
            # 학년도/학기 찾기
            if re.search(r'\d{4}.*?학기', line):
                year_match = re.search(r'(\d{4})', line)
                sem_match = re.search(r'(\d+학기|여름학기|겨울학기)', line)
                if year_match:
                    current_year = year_match.group(1)
                if sem_match:
                    current_semester = sem_match.group(1)
                continue
            
            # 탭 또는 여러 공백으로 구분된 데이터
            parts = re.split(r'\t+|\s{2,}', line.strip())
            if len(parts) >= 4 and current_year and current_semester:
                # 학수번호 패턴 확인
                if re.match(r'[A-Z]{3}\d{4}', parts[0]):
                    try:
                        grade = parts[3] if len(parts) > 3 else ""
                        # RE(재수강)이면 제외
                        if grade == "RE" or "RE" in line.upper():
                            continue
                        
                        rest_text = " ".join(parts[4:]) if len(parts) > 4 else ""
                        
                        # 전선, 전필 구분 찾기
                        course_type = None
                        professor = ""
                        
                        if "전선" in rest_text:
                            course_type = "전공선택"
                            professor = rest_text.replace("전선", "").strip()
                        elif "전필" in rest_text:
                            course_type = "전공필수"
                            professor = rest_text.replace("전필", "").strip()
                        else:
                            course_type = "교양"
                            professor = rest_text
                        
                        course = {
                            "year": current_year,
                            "semester": current_semester,
                            "course_code": parts[0],
                            "course_name": parts[1] if len(parts) > 1 else "",
                            "credit": float(parts[2]) if len(parts) > 2 and parts[2].replace('.', '').isdigit() else 0.0,
                            "grade": grade,
                            "professor": professor,
                            "course_type": course_type  # 전선, 전필, 교양
                        }
                        result["courses"].append(course)
                    except:
                        continue
        
        # GPA와 총 학점은 텍스트에서 찾기
        gpa_match = re.search(r'평점.*?(\d+\.\d+)', text)
        if gpa_match:
            result["gpa"] = float(gpa_match.group(1))
        
        # 취득학점(B)가 없으면 이수학점 찾기
        if result["total_credits"] == 0.0:
            credit_match = re.search(r'이수.*?(\d+\.?\d*)\s*학점', text)
            if credit_match:
                result["total_credits"] = float(credit_match.group(1))
        
        # 주전공(필/선) 학점 찾기
        if result["major_credits"] == 0.0:
            # 형식: 주전공(필/선) 24(15/9) 또는 주전공(필 / 선) 24(15 / 9)
            major_pattern = re.compile(r'주전공\s*\(필\s*[/／]\s*선\)\s*[:：]?\s*(\d+\.?\d*)(?:\s*\([^)]+\))?')
            major_match = major_pattern.search(text)
            if major_match:
                try:
                    result["major_credits"] = float(major_match.group(1))
                except:
                    pass
    
    # 하단부 값이 있으면 우선 사용 (덮어쓰지 않음)
    print(f"[DEBUG] 최종 파싱 결과 - 전공학점: {result['major_credits']}, 전체학점: {result['total_credits']}")
    return result


def save_transcript_json(data: Dict, filepath: str):
    """파싱된 데이터를 JSON 파일로 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_transcript_json(filepath: str) -> Dict:
    """저장된 JSON 파일 로드"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


