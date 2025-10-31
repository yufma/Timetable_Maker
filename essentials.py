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

def build_driver(headless: bool = False, download_dir: str | None = None, base: str = "script"):
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


