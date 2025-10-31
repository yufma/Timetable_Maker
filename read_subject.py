from pathlib import Path
import pandas as pd
import essentials
import json
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


def extract_subject_data(df: pd.DataFrame, positions: Dict[str, Tuple[int, int]]) -> pd.DataFrame:
    """
    고정된 위치에서 데이터를 추출하여 레이블이 지정된 DataFrame을 생성한다.
    
    Args:
        df: 원본 엑셀 DataFrame
        positions: 각 필드별 (행, 열) 위치를 지정하는 딕셔너리
                  예: {"강의명": (3, 3), "학점": (4, 3), ...}
    
    Returns:
        컬럼명이 지정된 DataFrame
    """
    result_data = {}
    
    # positions에 지정된 모든 필드 추출
    for col_name, (row, col) in positions.items():
        try:
            # 해당 위치의 값 추출 (NaN 처리)
            value = df.iloc[row, col]
            if pd.isna(value):
                result_data[col_name] = None
            else:
                result_data[col_name] = str(value).strip()
        except (IndexError, KeyError):
            result_data[col_name] = None
    
    # 단일 행 DataFrame 생성
    result_df = pd.DataFrame([result_data])
    return result_df


if __name__ == "__main__":
    # 위치 지정
    positions = {
        "강의명" : (3, 3),
        "교수명": (3, 11),
        "학점": (4, 3),
        "강의시간": (5, 3),
        "평가방식" : (5, 11),
        "중간고사": (23, 0),
        "기말고사": (23, 2),
        "출석": (23, 5),
        "과제": (23, 7),
        "퀴즈": (23, 8),
        "토론": (23, 10),
        "기타": (23, 13),
    }
    
    script_dir = Path(__file__).resolve().parent
    excel_dir = "subject_excel"
    
    # 모든 엑셀 파일 목록 가져오기
    excel_files = essentials.list_filenames(excel_dir, pattern="*.xlsx")
    
    if not excel_files:
        print("엑셀 파일이 없습니다.")
    else:
        print(f"총 {len(excel_files)}개 파일을 처리합니다.\n")
        
        # subject_json 폴더 생성
        json_dir = script_dir / "subject_json"
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # 모든 엑셀 파일 순회
        for filename in excel_files:
            print(f"처리 중: {filename}")
            df = read_subject_excel(filename, excel_dir)
            
            if df is not None:
                # 데이터 추출
                result_df = extract_subject_data(df, positions)
                
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
