from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import essentials
import time
import re
import os

def norm(s: str) -> str:
        return " ".join(s.split()).strip()

def load_common_subjects():
    
    driver = essentials.build_driver(False, "common_subjects_excels")
    driver.get(essentials.common_curriculum_url)


    wait = WebDriverWait(driver, 10)
    tbody_xpath = '//*[@id="dgList"]/tbody'
    row_count = len(driver.find_elements(By.XPATH, f"{tbody_xpath}/tr[td]"))
    print(f"🔎 데이터 행 개수: {row_count}")

    def curri_xpath_at(i: int) -> str:
        return f'{tbody_xpath}/tr[{i}]/td[1]'
    def btn_xpath_at(i: int) -> str:
        # 네 번째 td 내부의 a/button/input(clickable)
        return (
            f'{tbody_xpath}/tr[{i}]/td[2]/input'
        )
    i = 1
    while i <= row_count:
        # ❷ 매 루프마다 '다시 찾기' → stale 방지
        try:
            curri_cell = wait.until(
                EC.presence_of_element_located((By.XPATH, curri_xpath_at(i)))
            )
            curri_name = norm(curri_cell.text)
        except Exception:
            # 렌더링 타이밍 등으로 못 찾으면 다음 행
            i += 1
            continue

        print(f"✅ 대상 행 #{i}: {curri_name}")

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
        time.sleep(0.3)
        new_handles = list(set(driver.window_handles) - prev_handles)

        if new_handles:
            # ==== 팝업/새 창 케이스 ====
            driver.switch_to.window(new_handles[0])

            # URL이 about:blank라도 상관 없이, "DOM이 채워졌는지"를 기다린다.
            # 1) readyState == 'complete' AND
            # 2) body가 있고, 내용이 충분히 채워졌는지(길이/자식노드 수) 또는
            # 3) 우리가 기대하는 루트 요소(예: 상세 테이블/컨테이너 id)가 등장했는지
            def popup_dom_ready(d):
                try:
                    if d.execute_script("return document.readyState") != "complete":
                        return False
                    # 바디가 충분히 렌더링됐는지(길이나 자식 수로 추정)
                    has_body = d.execute_script(
                        "return !!document.body && (document.body.innerHTML.length > 500 || document.body.children.length > 0);"
                    )
                    return bool(has_body)
                except Exception:
                    return False

            WebDriverWait(driver, 10).until(popup_dom_ready)
            iframe = wait.until(EC.presence_of_element_located((By.ID, "ireport")))
            driver.switch_to.frame(iframe)


            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="report_menu_save_button"]'))).click()
            
            filename_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="report_download_main_option_frame"]/div/div[2]/input')
            )
            )
            filename_input.clear()
            filename_input.send_keys(f"{curri_name}")

            sheet_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="select_label"]')))
            select = Select(sheet_select)
            select.select_by_value("xlsx")

            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_sub_option_change_button"]'))).click()

            sheet_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_sub_option_frame"]/div/div[1]/div[1]/select')))
            select = Select(sheet_select)
            select.select_by_value("4")

            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_sub_option_save_button"]'))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_main_option_download_button"]'))).click()

            time.sleep(5)

            # 작업 끝나면 닫고 원창 복귀
            driver.close()
            driver.switch_to.window(next(iter(prev_handles)))
            wait.until(EC.presence_of_element_located((By.XPATH, tbody_xpath)))

        else:
            # ==== 같은 탭(전체/부분) 갱신 케이스 ====
            try:
                wait.until(EC.staleness_of(prev_tbody))
            except Exception:
                pass
            wait.until(EC.presence_of_element_located((By.XPATH, tbody_xpath)))


        # ❻ 기존 '순차 처리' 흐름 유지: 다음 행으로
        i += 1

    return
if __name__ == "__main__":
    load_common_subjects()