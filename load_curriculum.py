from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import essentials
import time
import re
import os

def norm(s: str) -> str:
        return " ".join(s.split()).strip()

def load_departs(depart_restrict: list = []):
    
    driver = essentials.build_driver(False, "depart_excels")
    driver.get(essentials.curriculum_url)

    restrict = {norm(x) for x in depart_restrict} if depart_restrict else set()


       # ── 순회: tr의 두 번째 td(학부/학과명) 확인 → 필터 → 4번째 td 버튼 클릭
    # ❶ rows 캐시 대신 인덱스로 재조회하기 위한 설정
    wait = WebDriverWait(driver, 10)
    tbody_xpath = '//*[@id="dgList"]/tbody'
    row_count = len(driver.find_elements(By.XPATH, f"{tbody_xpath}/tr[td]"))
    print(f"🔎 데이터 행 개수: {row_count}")

    def dept_xpath_at(i: int) -> str:
        return f'{tbody_xpath}/tr[td][{i}]/td[2]'  # 두 번째 td = 학부(과)명

    def btn_xpath_at(i: int) -> str:
        # 네 번째 td 내부의 a/button/input(clickable)
        return (
            f'{tbody_xpath}/tr[td][{i}]/td[4]'
            f'//*[self::a or self::button or self::input[@type="button" or @type="submit"]]'
        )

    # 다운로드 완료 대기 헬퍼 (타임아웃 포함)
    download_dir = Path(essentials._resolve_download_dir("depart_excels"))

    def wait_for_download(expected_stem: str, appear_timeout: float = 15.0, finish_timeout: float = 90.0) -> bool:
        # 1) 다운로드 시작 대기: .crdownload 또는 최종 파일 등장
        start = time.time()
        started = False
        while time.time() - start < appear_timeout:
            has_partial = any((f.stem == expected_stem and str(f).endswith('.crdownload')) for f in download_dir.glob("*"))
            has_final = any((f.stem == expected_stem and f.suffix.lower() == '.xlsx') for f in download_dir.glob("*.xlsx"))
            if has_partial or has_final:
                started = True
                break
            time.sleep(0.2)
        if not started:
            return False

        # 2) 다운로드 완료 대기: 최종 파일 존재하며 .crdownload 사라짐
        start2 = time.time()
        while time.time() - start2 < finish_timeout:
            has_final = any((f.stem == expected_stem and f.suffix.lower() == '.xlsx') for f in download_dir.glob("*.xlsx"))
            has_partial = any((f.stem == expected_stem and str(f).endswith('.crdownload')) for f in download_dir.glob("*"))
            if has_final and not has_partial:
                return True
            time.sleep(0.3)
        return False

    i = 1
    while i <= row_count:
        # ❷ 매 루프마다 '다시 찾기' → stale 방지
        try:
            dept_cell = wait.until(
                EC.presence_of_element_located((By.XPATH, dept_xpath_at(i)))
            )
            dept_name = norm(dept_cell.text)
        except Exception:
            # 렌더링 타이밍 등으로 못 찾으면 다음 행
            i += 1
            continue

        # 제한 목록이 있으면 필터 (정확 일치)
        if restrict and dept_name not in restrict:
            i += 1
            continue

        print(f"✅ 대상 행 #{i}: {dept_name}")

        # ❸ 클릭 전 상태 저장 (동기화용)
        prev_tbody = driver.find_element(By.XPATH, tbody_xpath)
        prev_handles = set(driver.window_handles)

        # ❹ 버튼 클릭 (locator 기반 대기 → 클릭, 실패 시 JS 백업)
        bx = btn_xpath_at(i)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, bx))).click()
        except Exception:
            try:
                btn = driver.find_element(By.XPATH, bx)
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                print("  ⚠️ 버튼 클릭 실패, 다음 행으로 진행")
                i += 1
                continue

                # ❺ 팝업/새창 vs 같은 탭 갱신 동기화
        # ==== 팝업/같은 탭 통합 대기: iframe#ireport가 나타난 창을 탐색 ====
        target_found = False
        end_time = time.time() + 12.0
        candidate_handles = list(prev_handles)  # 원래 창 포함
        while time.time() < end_time and not target_found:
            all_handles = driver.window_handles
            for h in all_handles:
                try:
                    driver.switch_to.window(h)
                    # DOM 로드 대기 (짧게)
                    try:
                        WebDriverWait(driver, 2).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                    except Exception:
                        pass
                    # iframe 존재 확인
                    if driver.find_elements(By.ID, "ireport"):
                        target_found = True
                        break
                except Exception:
                    continue
            time.sleep(0.2)

        if not target_found:
            # 같은 탭 갱신 케이스로 간주하고 테이블 복귀만 보장
            try:
                wait.until(EC.staleness_of(prev_tbody))
            except Exception:
                pass
            wait.until(EC.presence_of_element_located((By.XPATH, tbody_xpath)))
            i += 1
            continue

        # ===== iframe 안에서 저장 진행 =====
        iframe = wait.until(EC.presence_of_element_located((By.ID, "ireport")))
        driver.switch_to.frame(iframe)

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="report_menu_save_button"]'))).click()
        filename_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_main_option_frame"]/div/div[2]/input'))
        )
        filename_input.clear()
        filename_input.send_keys(f"{dept_name}")

        sheet_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="select_label"]'))
        )
        select = Select(sheet_select)
        select.select_by_value("xlsx")

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_sub_option_change_button"]'))).click()
        sheet_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_sub_option_frame"]/div/div[1]/div[1]/select'))
        )
        select = Select(sheet_select)
        select.select_by_value("4")

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_sub_option_save_button"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_main_option_download_button"]'))).click()

        # 고정 대기: 저장 후 다운로드 완료까지 여유 시간
        time.sleep(3)

        # 작업 끝나면 창 정리 및 원창 복귀 시도
        try:
            cur = driver.current_window_handle
            if cur not in prev_handles and len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(next(iter(prev_handles)))
        except Exception:
            try:
                driver.switch_to.window(next(iter(prev_handles)))
            except Exception:
                pass
        wait.until(EC.presence_of_element_located((By.XPATH, tbody_xpath)))


        # ❻ 기존 '순차 처리' 흐름 유지: 다음 행으로
        i += 1

    return
if __name__ == "__main__":
    load_departs([])