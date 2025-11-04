from pathlib import Path
import pandas as pd
import essentials
import json
import re
from typing import Dict, Tuple, Optional


def read_subject_excel(filename: str = None, excel_dir: str = "subject_excel"):
    """subject_excel 폴더에서 엑셀 파일 하나를 읽어 DataFrame을 반환한다."""
    script_dir = Path(__file__).resolve().parent
    excel_directory = script_dir / excel_dir
    
    # 파일명이 지정되지 않으면 첫 번째 엑셀 파일 사용
    if filename is None:
        excel_files = essentials.list_filenames(excel_dir, pattern="*.xlsx")
        if not excel_files:
            print("엑셀 파일이 없습니다.")
            return None
        filename = excel_files[0]
    
    excel_path = excel_directory / filename
    
    if not excel_path.exists():
        print(f"파일이 존재하지 않습니다: {excel_path}")
        return None
    
    try:
        df = pd.read_excel(excel_path, engine="calamine", header=None)
        return df
    except Exception as e:
        print(f"엑셀 읽기 오류 ({filename}): {e}")
        return None


def find_keyword_cell(df: pd.DataFrame, keyword: str) -> Optional[Tuple[int, int]]:
    """키워드를 포함하는 셀의 위치를 찾는다."""
    for row_idx in range(len(df)):
        for col_idx in range(len(df.columns)):
            cell_value = df.iloc[row_idx, col_idx]
            if pd.notna(cell_value) and keyword in str(cell_value):
                return (row_idx, col_idx)
    return None


def extract_value_after_keyword(df: pd.DataFrame, keyword: str) -> Optional[str]:
    """키워드를 찾은 후, 같은 행에서 키워드 다음 셀의 값을 반환한다."""
    keyword_pos = find_keyword_cell(df, keyword)
    if keyword_pos is None:
        return None
    
    row, col = keyword_pos
    # 같은 행에서 키워드 다음부터 찾기 (비어있지 않은 첫 번째 셀)
    for c in range(col + 1, len(df.columns)):
        value = df.iloc[row, c]
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return None


def extract_evaluation_data(df: pd.DataFrame) -> Dict[str, str]:
    """평가 기준 헤더 행과 값 행에서 평가 데이터를 추출한다.
    
    구조: "중간고사"가 적힌 첫 번째 행 찾기 -> 그 행에서 열 순회하여 평가 항목 위치 찾기 
          -> 다음 행의 같은 열에서 값 가져오기
    """
    result = {}
    evaluation_keywords = ["중간고사", "기말고사", "출석", "과제", "퀴즈", "토론", "기타"]
    
    # ===== 1단계: "중간고사"가 적힌 첫 번째 행 찾기 (헤더 행 검증 포함) =====
    header_row = None
    
    for row_idx in range(len(df)):
        # 이 행에서 "중간고사"가 있는지 열 순회로 확인
        has_midterm = False
        evaluation_keyword_count = 0
        
        for col_idx in range(len(df.columns)):
            cell_value = df.iloc[row_idx, col_idx]
            if pd.notna(cell_value):
                cell_str = str(cell_value).strip()
                # "중간고사" 확인 ("중간고사 이전" 같은 건 제외하기 위해 셀 내용이 "중간고사"로 시작하거나 정확히 일치)
                if "중간고사" in cell_str:
                    # "중간고사 이전", "중간고사 이후" 같은 건 제외
                    if cell_str == "중간고사" or (cell_str.startswith("중간고사") and len(cell_str.split()) <= 2):
                        has_midterm = True
                # 다른 평가 항목도 함께 있는지 확인 (정확히 키워드가 있는지)
                for keyword in evaluation_keywords:
                    if keyword != "중간고사" and keyword in cell_str:
                        # 정확히 키워드만 있거나 키워드로 시작하는 짧은 텍스트만
                        if cell_str == keyword or (cell_str.startswith(keyword) and len(cell_str.split()) <= 2):
                            evaluation_keyword_count += 1
        
        # "중간고사"가 있고, 다른 평가 항목도 최소 2개 이상 있으면 헤더 행 (더 확실하게)
        if has_midterm and evaluation_keyword_count >= 2:
            header_row = row_idx
            break
    
    if header_row is None:
        return {key: "0 %" for key in evaluation_keywords}
    
    # ===== 2단계: 헤더 행에서 열 순회하여 평가 항목 위치 찾기 =====
    evaluation_cols = {}
    
    for col_idx in range(len(df.columns)):
        cell_value = df.iloc[header_row, col_idx]
        if pd.notna(cell_value):
            cell_str = str(cell_value).strip()
            
            # 각 평가 항목 키워드와 매칭 (공백 제거 후도 확인)
            for keyword in evaluation_keywords:
                if keyword not in evaluation_cols:  # 아직 할당되지 않았으면
                    if keyword in cell_str or keyword.replace(" ", "") in cell_str.replace(" ", ""):
                        evaluation_cols[keyword] = col_idx
                        break
    
    # ===== 3단계: 다음 행의 같은 열에서 값 가져오기 =====
    value_row = header_row + 1
    
    if value_row >= len(df):
        return {key: "0 %" for key in evaluation_keywords}
    
    for keyword in evaluation_keywords:
        if keyword in evaluation_cols:
            col_idx = evaluation_cols[keyword]
            value = df.iloc[value_row, col_idx]
            
            # 값 추출 및 포맷팅
            if pd.notna(value):
                value_str = str(value).strip()
                if re.search(r'\d+', value_str):
                    # 숫자 추출
                    percent_match = re.search(r'(\d+\.?\d*)', value_str)
                    if percent_match:
                        num_value = percent_match.group(1)
                        if float(num_value) == 0:
                            result[keyword] = "0 %"
                        elif '%' in value_str:
                            result[keyword] = value_str
                        else:
                            result[keyword] = f"{num_value} %"
                    else:
                        result[keyword] = "0 %"
                else:
                    result[keyword] = "0 %"
            else:
                result[keyword] = "0 %"
        else:
            result[keyword] = "0 %"
    
    return result


def extract_subject_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    키워드 기반으로 데이터를 추출하여 레이블이 지정된 DataFrame을 생성한다.
    
    Args:
        df: 원본 엑셀 DataFrame
    
    Returns:
        컬럼명이 지정된 DataFrame
    """
    result_data = {}
    
    # 강의명: "교과목명" 키워드 찾고 같은 행에서 다음 셀 추출
    강의명 = extract_value_after_keyword(df, "교과목명")
    result_data["강의명"] = 강의명 if 강의명 else ""
    
    # 교수명: "담당교수명" 키워드 찾고 같은 행에서 다음 셀 추출
    교수명 = extract_value_after_keyword(df, "담당교수명")
    result_data["교수명"] = 교수명 if 교수명 else ""
    
    # 학점: "학수번호" 키워드 찾고 같은 행에서 다음 셀에서 "학점:" 패턴 추출
    학수번호_셀 = extract_value_after_keyword(df, "학수번호")
    if 학수번호_셀:
        학점_match = re.search(r"학점[:\s]*(\d+\.?\d*)", 학수번호_셀)
        if 학점_match:
            result_data["학점"] = 학점_match.group(1)
        else:
            result_data["학점"] = ""
    
    # 강의시간: "강의시간표" 키워드 찾고 같은 행에서 다음 셀 추출
    강의시간 = extract_value_after_keyword(df, "강의시간표")
    result_data["강의시간"] = 강의시간 if 강의시간 else ""
    
    # 평가방식: "강좌평가방법" 또는 "평가방법" 키워드 찾고 같은 행에서 다음 셀 추출
    평가방식 = extract_value_after_keyword(df, "강좌평가방법")
    if not 평가방식:
        평가방식 = extract_value_after_keyword(df, "평가방법")
    result_data["평가방식"] = 평가방식 if 평가방식 else ""
    
    # 평가 기준 데이터 추출
    evaluation_data = extract_evaluation_data(df)
    result_data.update(evaluation_data)
    
    # 단일 행 DataFrame 생성
    result_df = pd.DataFrame([result_data])
    return result_df


def read_subject_excel_rows(excel_dir: str = "subject_excel"):
    """
    subject_excel 폴더의 모든 엑셀 파일을 읽어서 JSON 파일로 변환한다.
    
    Args:
        excel_dir: 엑셀 파일이 있는 디렉터리명 (기본값: "subject_excel")
    """
    script_dir = Path(__file__).resolve().parent
    
    # 모든 엑셀 파일 목록 가져오기
    excel_files = essentials.list_filenames(excel_dir, pattern="*.xlsx")
    
    if not excel_files:
        print("엑셀 파일이 없습니다.")
        return
    
    print(f"제한 없음: {len(excel_files)}개 파일을 모두 처리합니다.\n")
    
    # subject_json 폴더 생성
    json_dir = script_dir / "subject_json"
    json_dir.mkdir(parents=True, exist_ok=True)
    
    # 모든 엑셀 파일 순회
    for filename in excel_files:
        print(f"처리 중: {filename}")
        df = read_subject_excel(filename, excel_dir)
        
        if df is not None:
            # 키워드 기반 데이터 추출
            result_df = extract_subject_data(df)
            
            # JSON 파일로 저장
            json_filename = Path(filename).stem + ".json"
            json_path = json_dir / json_filename
            
            # DataFrame을 딕셔너리로 변환하여 JSON 저장
            result_dict = result_df.to_dict(orient="records")[0]
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ 저장 완료: {json_filename}\n")
        else:
            print(f"  ✗ 읽기 실패: {filename}\n")
    
    print(f"모든 파일 처리 완료! ({json_dir})")


if __name__ == "__main__":
    read_subject_excel_rows()
