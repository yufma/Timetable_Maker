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

    # depart_restrict가 비어있으면 모든 학과 처리, 아니면 지정된 학과만 처리
    restrict = {norm(x) for x in depart_restrict} if depart_restrict else set()
    if restrict:
        print(f"📋 제한 목록: {sorted(restrict)}")
    else:
        print("📋 제한 없음: 모든 학과를 처리합니다.")


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

    def wait_for_pdf_download(expected_stem: str, appear_timeout: float = 15.0, finish_timeout: float = 90.0) -> bool:
        # 1) 다운로드 시작 대기: .crdownload 또는 최종 파일 등장
        start = time.time()
        started = False
        while time.time() - start < appear_timeout:
            has_partial = any((f.stem == expected_stem and str(f).endswith('.crdownload')) for f in download_dir.glob("*"))
            has_final = any((f.stem == expected_stem and f.suffix.lower() == '.pdf') for f in download_dir.glob("*.pdf"))
            if has_partial or has_final:
                started = True
                break
            time.sleep(0.2)
        if not started:
            return False

        # 2) 다운로드 완료 대기: 최종 파일 존재하며 .crdownload 사라짐
        start2 = time.time()
        while time.time() - start2 < finish_timeout:
            has_final = any((f.stem == expected_stem and f.suffix.lower() == '.pdf') for f in download_dir.glob("*.pdf"))
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
        if restrict:
            if dept_name not in restrict:
                print(f"⏭️  건너뜀 행 #{i}: {dept_name} (제한 목록에 없음)")
                i += 1
                continue
            print(f"✅ 대상 행 #{i}: {dept_name} (제한 목록에 있음)")
        else:
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
            filename_input.send_keys(f"{dept_name}")

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

            time.sleep(0.8)  # Excel 다운로드 완료 대기

            # PDF 다운로드를 위해 다시 저장 다이얼로그 열기 시도
            # 다이얼로그가 닫혔는지 확인 (더 정확한 체크)
            dialog_open = False
            try:
                # select_label 요소가 여전히 존재하고 클릭 가능한지 확인
                sheet_select = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="select_label"]'))
                )
                # 다운로드 버튼도 존재하는지 확인
                download_btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="download_main_option_download_button"]'))
                )
                dialog_open = True
            except Exception:
                dialog_open = False
            
            if not dialog_open:
                # 다이얼로그가 닫혔으면 다시 저장 버튼 클릭
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="report_menu_save_button"]'))).click()
                time.sleep(0.3)  # 저장 버튼 클릭 후 다이얼로그 열릴 때까지 대기
                
                # 다이얼로그가 완전히 열릴 때까지 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_main_option_frame"]'))
                )
                time.sleep(0.2)  # 추가 로딩 대기
                
                # 파일명 입력 필드 대기 및 재입력
                filename_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="report_download_main_option_frame"]/div/div[2]/input'))
                )
                filename_input.clear()
                time.sleep(0.1)
                filename_input.send_keys(f"{dept_name}")
                time.sleep(0.2)  # 입력 완료 대기
            
            # select 요소 가져오기 (클릭 가능할 때까지 대기)
            sheet_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="select_label"]'))
            )
            
            # select 요소가 보이도록 스크롤
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sheet_select)
                time.sleep(0.2)
            except Exception:
                pass
            
            # 파일 형식 선택 (pdf) - 여러 방법 시도
            try:
                select = Select(sheet_select)
                select.select_by_value("pdf")
                time.sleep(0.2)  # 선택 후 대기
            except Exception:
                # Select가 실패하면 JavaScript로 직접 선택
                try:
                    driver.execute_script(
                        "arguments[0].value = 'pdf'; "
                        "var event = new Event('change', { bubbles: true }); "
                        "arguments[0].dispatchEvent(event);",
                        sheet_select
                    )
                    time.sleep(0.2)
                except Exception as e:
                    print(f"PDF 형식 선택 실패: {e}")

            # PDF 다운로드 버튼 찾기 및 클릭 (여러 방법 시도)
            download_btn_xpath = '//*[@id="download_main_option_download_button"]'
            try:
                download_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, download_btn_xpath))
                )
                # 버튼이 보이도록 스크롤
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", download_btn)
                    time.sleep(0.2)
                except Exception:
                    pass
                
                # 일반 클릭 시도
                try:
                    download_btn.click()
                except Exception:
                    # JavaScript 클릭 시도
                    try:
                        driver.execute_script("arguments[0].click();", download_btn)
                    except Exception:
                        # 마지막으로 XPath로 직접 클릭
                        wait.until(EC.element_to_be_clickable((By.XPATH, download_btn_xpath))).click()
            except Exception as e:
                print(f"PDF 다운로드 버튼 클릭 실패: {e}")
            
            # PDF 다운로드 완료 대기
            pdf_downloaded = wait_for_pdf_download(dept_name, appear_timeout=15.0, finish_timeout=90.0)
            if pdf_downloaded:
                print(f"  ✅ PDF 다운로드 완료: {dept_name}")
            else:
                print(f"  ⚠️ PDF 다운로드 타임아웃 또는 실패: {dept_name}")

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
    load_departs(essentials.departs_restrict)