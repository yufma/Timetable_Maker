from cProfile import label
from pathlib import Path
import pandas as pd
import essentials
import json

def read_excel_rows():
    script_dir = Path(__file__).resolve().parent
    excels = essentials.list_filenames("common_subjects_excels")
    for excel in excels:
        df = pd.read_excel(script_dir / "common_subjects_excels" / excel, engine="calamine", header=None)
        if not df.empty:
            df = df.drop([3,6], axis=1)
            df = df.drop(0,axis=0)
            df.columns = df.iloc[0]
            print(df.columns)
            df = df.iloc[1:].reset_index(drop=True)
            df = df.dropna(axis = 0)
        out_dir = script_dir / "common_subjects_json"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{Path(excel).stem}.json"
        records = df.to_dict(orient="records")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"Saved {out_path}")
if __name__ == "__main__":
    read_excel_rows()


