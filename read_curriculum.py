from cProfile import label
from pathlib import Path
import pandas as pd
import essentials
import json

def read_excel_rows(depart_restrict: list = []):
    script_dir = Path(__file__).resolve().parent
    
    # depart_restrict가 비어있으면 모든 엑셀 파일 처리
    if not depart_restrict:
        excel_files = essentials.list_filenames("depart_excels", pattern="*.xlsx")
        print(f"제한 없음: {len(excel_files)}개 파일을 모두 처리합니다.")
    else:
        # 학과명에 .xlsx 확장자 추가
        excel_files = [f"{dept}.xlsx" for dept in depart_restrict]
        print(f"제한 목록: {len(depart_restrict)}개 파일을 처리합니다.")
    
    # depart_json 폴더 생성
    json_dir = script_dir / "depart_json"
    json_dir.mkdir(parents=True, exist_ok=True)
    
    for excel in excel_files:
        excel_path = script_dir / "depart_excels" / excel
        if not excel_path.exists():
            print(f"⚠️  파일이 존재하지 않습니다: {excel}")
            continue
            
        print(f"처리 중: {excel}")
        try:
            df = pd.read_excel(excel_path, engine="calamine", header=None)
            if not df.empty:
                df = df.drop([2,3,4,9], axis=1)
                df = df.drop([0,1],axis=0)
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)
                df.columns = ["세부구분" if pd.isna(c) else c for c in df.columns]
                # '종 별'이 비어있는 행만 제거 (NaN 또는 공백 문자열)
                if "종 별" in df.columns:
                    df = df.dropna(subset=["학점"]).copy()
                    df = df[df["학점"].astype(str).str.strip() != ""].reset_index(drop=True)
                
                # 결과 저장: depart_json/{엑셀파일명}.json
                out_path = json_dir / f"{Path(excel).stem}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
                print(f"  ✓ 저장 완료: {out_path}\n")
            else:
                print(f"  ✗ 빈 파일: {excel}\n")
        except Exception as e:
            print(f"  ✗ 처리 실패 ({excel}): {e}\n")
    
    print(f"모든 파일 처리 완료! ({json_dir})")

if __name__ == "__main__":
    read_excel_rows(essentials.departs_restrict)


