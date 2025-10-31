from cProfile import label
from pathlib import Path
import pandas as pd
import essentials
import json

def read_excel_rows():
    script_dir = Path(__file__).resolve().parent
    # 임시: 인공지능공학과만 처리
    excels = ["인공지능공학과.xlsx"]
    for excel in excels:
        df = pd.read_excel(script_dir / "depart_excels" / excel, engine="calamine", header=None)
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
            print(df)
            # 결과 저장: depart_excels/{엑셀파일명}.json
            out_path = script_dir / "depart_json" / f"{Path(excel).stem}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
            print(f"Saved {out_path}")
            
        break
if __name__ == "__main__":
    read_excel_rows()


