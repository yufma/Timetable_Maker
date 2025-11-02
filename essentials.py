from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
from pathlib import Path
import time
import re
import os

def _resolve_download_dir(path: str, base: str = "script") -> str:
    """
    path가 상대면 절대로 바꿔서 반환. base='cwd'면 현재 작업경로,
    base='script'면 이 파일(essentials.py) 위치 기준으로 변환.
    """
    p = Path(path)
    if not p.is_absolute():
        base_dir = Path.cwd() if base == "cwd" else Path(__file__).resolve().parent
        p = (base_dir / p).resolve()
    return str(p)

def list_filenames(dir_name: str, pattern: str = "*") -> list[str]:
    """
    주어진 디렉터리에 있는 모든 파일의 이름을 리스트로 반환합니다.
    pattern으로 필터링 가능합니다(기본값: 전체 파일).
    예: pattern="*.xlsx", pattern="*.csv"
    """
    script_dir = Path(__file__).resolve().parent
    target_dir = (script_dir / dir_name).resolve()

    if not target_dir.exists():
        return []

    return [p.name for p in sorted(target_dir.glob(pattern)) if p.is_file()]

def to_pdf_dir_name(dir_name: str) -> str:
    """
    폴더명에서 밑줄(_)로 구분된 마지막 부분을 "pdf"로 변경한 새로운 폴더명을 반환합니다.
    
    Args:
        dir_name: 원본 폴더명
    
    Returns:
        마지막 부분이 "pdf"로 변경된 폴더명
    
    Examples:
        >>> to_pdf_dir_name("depart_excels")
        "depart_pdf"
        >>> to_pdf_dir_name("common_subjects_excels")
        "common_subjects_pdf"
        >>> to_pdf_dir_name("subject_excel")
        "subject_pdf"
        >>> to_pdf_dir_name("pdf")  # 밑줄이 없는 경우
        "pdf"
    """
    parts = dir_name.rsplit("_", 1)  # 오른쪽부터 첫 번째 밑줄에서 분리
    if len(parts) == 1:
        # 밑줄이 없는 경우
        return "pdf"
    else:
        # 밑줄이 있는 경우: 마지막 부분을 "pdf"로 변경
        return f"{parts[0]}_pdf"

def move_files_by_extension_to_pdf_dir(dir_name: str, base: str = "script", target_ext: str = ".pdf") -> int:
    """
    원본 폴더에서 지정한 확장자(target_ext)의 파일들을 찾아서,
    PDF 폴더명으로 새로 만든 폴더로 이동시킵니다.
    
    Args:
        dir_name: 원본 폴더명 (상대 경로 또는 절대 경로)
        base: 기본 경로 기준 ('script' 또는 'cwd')
        target_ext: 이동할 파일 확장자 (기본값: ".pdf")
    
    Returns:
        이동된 파일 개수
    
    Examples:
        >>> move_files_by_extension_to_pdf_dir("depart_excels")
        # depart_excels 폴더의 .pdf 파일들을 depart_pdf 폴더로 이동
        >>> move_files_by_extension_to_pdf_dir("common_subjects_excels", target_ext=".pdf")
        # common_subjects_excels 폴더의 .pdf 파일들을 common_subjects_pdf 폴더로 이동
    """
    import shutil
    
    # 원본 폴더 경로
    source_dir = Path(_resolve_download_dir(dir_name, base=base))
    
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"⚠️ 원본 폴더를 찾을 수 없습니다: {source_dir}")
        return 0
    
    # 대상 폴더명 생성
    pdf_dir_name = to_pdf_dir_name(dir_name)
    
    # 대상 폴더 경로 (원본 폴더와 같은 상위 디렉터리에 생성)
    if base == "cwd":
        target_dir = Path.cwd() / pdf_dir_name
    else:
        target_dir = Path(__file__).resolve().parent / pdf_dir_name
    
    # 대상 폴더 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 대상 폴더 생성/확인: {target_dir}")
    
    # 확장자 정규화 (소문자, 점 포함)
    target_ext = target_ext.lower()
    if not target_ext.startswith("."):
        target_ext = f".{target_ext}"
    
    # 원본 폴더에서 대상 확장자 파일 찾아서 이동
    moved_count = 0
    for file_path in source_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == target_ext:
            target_file = target_dir / file_path.name
            try:
                shutil.move(str(file_path), str(target_file))
                print(f"  ✓ 이동: {file_path.name} -> {pdf_dir_name}/")
                moved_count += 1
            except Exception as e:
                print(f"  ✗ 이동 실패 ({file_path.name}): {e}")
    
    if moved_count > 0:
        print(f"✅ 총 {moved_count}개 파일을 {pdf_dir_name} 폴더로 이동했습니다.")
    else:
        print(f"ℹ️ 이동할 {target_ext} 파일이 없습니다.")
    
    return moved_count

def build_driver(headless: bool = None, download_dir: str | None = None, base: str = "script"):
    # headless가 None이면 전역 설정 사용
    if headless is None:
        headless = HEADLESS_MODE
    
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")

    if download_dir:
        download_dir = _resolve_download_dir(download_dir, base=base)  # ✅ 여기서 절대 경로로 보정
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        opts.add_experimental_option("prefs", prefs)
        opts.add_argument("--disable-features=DownloadBubble,DownloadBubbleV2")
    
    # HTML 파일 자동 저장 방지
    opts.add_argument("--disable-features=DownloadHats,DownloadHatsErrorDetails")
    opts.add_argument("--disable-extensions")

    driver = webdriver.Chrome(options=opts)

    # (옵션) headless 보조
    if headless and download_dir:
        try:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": download_dir
            })
        except Exception:
            pass

    print(f"📂 Chrome download dir = {download_dir if download_dir else '(default)'}")
    return driver

# 드라이버 headless 모드 설정 (True로 설정하면 모든 드라이버가 headless 모드로 실행됨)
HEADLESS_MODE = True

#아래의 common_semester 변수와 code_semester 변수는 현재 학기에 맞춰 변경할 것
common_semester = "SU_51001"
code_semester = "2025-2"
curriculum_url = f"https://sugang.inha.ac.kr/sugang/{common_semester}/curriculum.aspx"
common_curriculum_url = f"https://sugang.inha.ac.kr/sugang/{common_semester}/curriculum_common.aspx"
#LecPlanHistory_url은 common_semester 변수를 사용하지 않음. 매 학기 직접 변경할 것
LecPlanHistory_url = "https://sugang.inha.ac.kr/STD/SU_65002/LecPlanHistory.aspx"

#main 코드에서 사용할 학과 제한
departs_restrict = ["인공지능공학과"]

if __name__ == "__main__":
    print(list_filenames("common_subjects_excels"))
    print(list_filenames("depart_excels"))
    print("\n확장자별 파일 분류:")
    print("\nPDF 폴더명 변환:")
    print(f"depart_excels -> {to_pdf_dir_name('depart_excels')}")
    print(f"common_subjects_excels -> {to_pdf_dir_name('common_subjects_excels')}")
    print(f"subject_excel -> {to_pdf_dir_name('subject_excel')}")


