from pathlib import Path
import sys

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXPORT_DIR = PROJECT_ROOT / "exports"
SUBJECT_DIR = EXPORT_DIR / "subjects"
INDEX_FILE = EXPORT_DIR / "index.html"


def verify_exports() -> dict:
    result = {
        "index_exists": INDEX_FILE.exists(),
        "subjects_dir_exists": SUBJECT_DIR.exists(),
        "html_count": 0,
        "md_count": 0,
        "with_details": 0,
        "missing_json": 0,
        "sample_files": [],
    }

    if not SUBJECT_DIR.exists():
        return result

    html_files = list(SUBJECT_DIR.glob("*.html"))
    md_files = list(SUBJECT_DIR.glob("*.md"))
    result["html_count"] = len(html_files)
    result["md_count"] = len(md_files)

    # 샘플 3개 확인
    for html_file in html_files[:3]:
        content = html_file.read_text(encoding="utf-8")
        has_details = (
            "강의명" in content
            or "교수명" in content
            or "학점" in content
            or "강의시간" in content
        )
        missing_json_msg = "원본 subject_json을 찾지 못했습니다" in content

        result["sample_files"].append(
            {
                "file": html_file.name,
                "has_details": has_details,
                "missing_json": missing_json_msg,
            }
        )

        if has_details:
            result["with_details"] += 1
        if missing_json_msg:
            result["missing_json"] += 1

    return result


if __name__ == "__main__":
    result = verify_exports()
    print("\n=== 요약본 생성 확인 ===")
    print(f"✓ 인덱스 파일 존재: {result['index_exists']}")
    print(f"✓ subjects 디렉토리 존재: {result['subjects_dir_exists']}")
    print(f"✓ HTML 파일 개수: {result['html_count']}")
    print(f"✓ Markdown 파일 개수: {result['md_count']}")
    print(f"\n샘플 확인 (처음 3개):")
    for sample in result["sample_files"]:
        status = "✓" if sample["has_details"] and not sample["missing_json"] else "✗"
        print(f"  {status} {sample['file']}: 상세정보={sample['has_details']}, JSON누락={sample['missing_json']}")
    print(f"\n상세정보 포함된 파일: {result['with_details']}/{len(result['sample_files'])}")
    print(f"\n생성 위치: {EXPORT_DIR}")
    print(f"웹으로 보기: cd {EXPORT_DIR} && python -m http.server 8000")
    print()




