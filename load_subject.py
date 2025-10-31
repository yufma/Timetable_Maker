from pathlib import Path
import json
from typing import List, Dict, Any
import essentials
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import re
import time


def load_department_subjects(department_name: str = "인공지능공학과") -> List[Dict[str, Any]]:
    """depart_json/{department_name}.json 파일을 읽어 과목 리스트를 반환한다."""
    script_dir = Path(__file__).resolve().parent
    json_path = script_dir / "depart_json" / f"{department_name}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def load_subject_depart(text: str | None = None):
    driver = essentials.build_driver(False, "subject_excel")
    driver.get(essentials.LecPlanHistory_url)

    # 지정한 버튼 클릭 → 입력창에 텍스트 입력
    click_xpath = "/html/body/form/div[3]/div[2]/div[1]/span/input[3]"
    input_xpath = "/html/body/form/div[3]/div[2]/div[1]/input[1]"

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, click_xpath))
    ).click()

    target = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, input_xpath))
    )
    target.clear()
    if text is None:
        # 기본값: essentials.departs_restrict[0] 사용 (존재 시)
        if hasattr(essentials, "departs_restrict") and essentials.departs_restrict:
            text = essentials.departs_restrict[0]
        else:
            text = ""
    target.send_keys(text)

    return driver


def search_and_visit_result_links(driver, max_rows: int | None = None):
    """검색 버튼 클릭 후 결과 테이블 각 행의 5번째 열 링크(onclick/href)로 이동한다."""
    # 1) 검색 버튼 클릭
    search_btn_xpath = "/html/body/form/div[3]/div[2]/div[1]/input[2]"
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, search_btn_xpath))
    ).click()
    
    # 검색 결과 로드 대기
    time.sleep(0.8)

    # 2) 결과 tbody 대기
    tbody_xpath = "/html/body/form/div[3]/div[2]/div[3]/div/table/tbody"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, tbody_xpath))
    )
    
    # 테이블 렌더링 완료 대기
    time.sleep(0.5)

    # 3) 행 개수 측정
    rows = driver.find_elements(By.XPATH, f"{tbody_xpath}/tr")
    total = len(rows)

    for i in range(1, total + 1):
        # 각 행 처리 전 딜레이
        time.sleep(0.3)
        
        # 먼저 첫 번째 열(td[1]) 값 확인하여 code_semester와 일치하는지 체크
        semester_xpath = f"{tbody_xpath}/tr[{i}]/td[1]"
        try:
            semester_el = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, semester_xpath))
            )
            semester_value = (semester_el.text or "").strip()
            # code_semester와 일치하지 않으면 건너뜀
            if semester_value != essentials.code_semester:
                continue
        except Exception:
            # 첫 번째 열을 못 찾으면 건너뜀
            continue
        
        # code_semester와 일치하는 행이므로 처리 진행

        link_xpath = f"{tbody_xpath}/tr[{i}]/td[5]/a"
        name_s_xpath = f"{tbody_xpath}/tr[{i}]/td[3]"
        name_l_xpath = f"{tbody_xpath}/tr[{i}]/td[4]"
        try:
            a = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, link_xpath))
            )
            # 텍스트 안전 추출 및 파일명 안전화
            name_s_el = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, name_s_xpath))
            )
            name_l_el = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, name_l_xpath))
            )
            name_s = (name_s_el.text or "").strip()
            name_l = (name_l_el.text or "").strip()
            raw_file_name = f"{name_s}.{name_l}" if name_s or name_l else "unknown"
            safe_file_name = re.sub(r"[\\/:*?\"<>|]", "_", raw_file_name)
            print(safe_file_name)

            # 우선 onclick에서 url 스니펫 추출 시도
            onclick = a.get_attribute("onclick") or ""
            href = a.get_attribute("href") or ""
            url = None
            # onclick 내부의 http(s) URL 추출
            m = re.search(r"https?://[^'\"]+", onclick)
            if m:
                url = m.group(0)
            elif href and href.startswith("http"):
                url = href

            # 스크롤 후 클릭 시도 → 실패하면 JS 클릭 → 마지막으로 URL 이동
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", a)
                time.sleep(0.3)  # 스크롤 후 대기
            except Exception:
                pass
            
            # 클릭 전 창 핸들 저장 (팝업 확인용)
            prev_handles = set(driver.window_handles)
            
            clicked = False
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, link_xpath))
                ).click()
                clicked = True
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", a)
                    clicked = True
                except Exception:
                    clicked = False
            if not clicked:
                if url:
                    driver.get(url)
                else:
                    # 더 이상 수단이 없으면 건너뜀
                    continue

            # 링크 클릭 후 페이지 로드 대기
            time.sleep(0.8)

            # 새 창이 열렸는지 확인
            new_window_opened = False
            end_time = time.time() + 10.0
            while time.time() < end_time:
                current_handles = set(driver.window_handles)
                if current_handles != prev_handles:
                    # 새 창이 열렸으면 해당 창으로 전환
                    new_handle = (current_handles - prev_handles).pop()
                    driver.switch_to.window(new_handle)
                    new_window_opened = True
                    break
                time.sleep(0.2)

            # 페이지 로드 및 iframe 대기
            if not new_window_opened:
                # 같은 창에서 갱신된 경우
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except Exception:
                    pass

            # iframe이 나타날 때까지 대기 (다운로드 페이지 로드 확인)
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "ireport"))
                )
                # iframe 로드 후 대기
                time.sleep(0.8)
            except Exception:
                print(f"iframe(ireport) 로드 실패, 건너뜀")
                # 새 창이었으면 닫고 이전 창으로 복귀
                if new_window_opened:
                    driver.close()
                    driver.switch_to.window(list(prev_handles)[0])
                continue

            # 다운로드 수행
            try:
                download_from_current_page(driver, safe_file_name)
                # 다운로드 완료 후 대기
                time.sleep(1)
            except Exception as e:
                print(f"다운로드 실패: {e}")
                import traceback
                traceback.print_exc()
            
            # 새 창이었으면 닫고 이전 창으로 복귀
            if new_window_opened:
                driver.close()
                time.sleep(0.3)  # 창 닫은 후 대기
                driver.switch_to.window(list(prev_handles)[0])
                time.sleep(0.5)  # 창 전환 후 대기
                # 복귀 후 tbody 재대기(갱신 대비)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, tbody_xpath))
                )
                time.sleep(0.5)  # tbody 로드 후 대기
            else:
                # 같은 창에서 갱신된 경우 이전 페이지로 복귀
                time.sleep(0.8)
                driver.back()
                # 복귀 후 tbody 재대기(갱신 대비)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, tbody_xpath))
                )
                time.sleep(0.5)  # tbody 로드 후 대기
        except Exception:
            # 개별 행 실패는 건너뛰고 다음 행 처리
            continue


def run_subject_searches_from_data(
    department_name: str = "인공지능공학과",
    max_rows_per_code: int | None = None,
):
    """JSON 데이터에서 전공 계열의 학수번호만 골라 순차 검색 및 결과 링크 순회."""
    subjects = load_department_subjects(department_name)
    codes = sorted(list(extract_major_course_codes(subjects)))

    if not codes:
        print("전공 학수번호가 없습니다.")
        return None

    driver = load_subject_depart("")  # 입력칸 포커싱만 진행, 내용은 비워둠

    input_xpath = "/html/body/form/div[3]/div[2]/div[1]/input[1]"
    for code in codes:
        try:
            # 각 코드 검색 전 딜레이
            time.sleep(0.5)
            
            target = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, input_xpath))
            )
            target.clear()
            time.sleep(0.3)  # clear 후 대기
            target.send_keys(code)
            time.sleep(0.3)  # 입력 후 대기
            
            search_and_visit_result_links(driver, max_rows=max_rows_per_code)
            
            # 검색 완료 후 대기
            time.sleep(1)
        except Exception:
            # 개별 코드 실패는 건너뜀
            continue
    return driver


def extract_major_course_codes(subjects: List[Dict[str, Any]]) -> set[str]:
    """subjects에서 '종 별'이 '전공'으로 시작하는 항목의 학수번호만 집합으로 추출한다."""
    codes: set[str] = set()
    for row in subjects:
        kind = str(row.get("종 별", ""))
        code = row.get("학수번호")
        if kind.startswith("전공") and isinstance(code, str) and code.strip():
            codes.add(code.strip())
    return codes


def download_from_current_page(driver, filename: str = ""):
    """현재 페이지(iframe 내부)에서 다운로드를 수행한다. load_curriculum.py 구조 참고."""
    wait = WebDriverWait(driver, 10)
    
    # ===== iframe 안에서 저장 진행 =====
    iframe = wait.until(EC.presence_of_element_located((By.ID, "ireport")))
    driver.switch_to.frame(iframe)

    # 저장 버튼 클릭
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="report_menu_save_button"]'))).click()
    time.sleep(0.5)  # 저장 버튼 클릭 후 대기
    
    # 파일명 입력 부분 (비워둠 - 사용자가 채울 수 있음)
    filename_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_main_option_frame"]/div/div[2]/input'))
    )
    filename_input.clear()
    time.sleep(0.3)  # clear 후 대기
    # safe_file_name을 파라미터로 받아서 사용
    if filename:
        filename_input.send_keys(filename)
        time.sleep(0.3)  # 입력 후 대기

    # 파일 형식 선택 (xlsx)
    sheet_select = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="select_label"]'))
    )
    select = Select(sheet_select)
    select.select_by_value("xlsx")
    time.sleep(0.3)  # 선택 후 대기

    # 최종 다운로드 버튼 클릭
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_main_option_download_button"]'))).click()
    
    # 다운로드 완료 대기
    time.sleep(1.5)

    # iframe에서 나오기
    driver.switch_to.default_content()


def can_search_by_course_code(code: str, subjects: List[Dict[str, Any]]) -> bool:
    """주어진 code가 전공 계열 항목의 학수번호에 존재하는지 여부 반환."""
    if not code:
        return False
    return code.strip() in extract_major_course_codes(subjects)

if __name__ == "__main__":
    # JSON 기반으로 전공 학수번호를 순회 검색 (code_semester와 일치하는 모든 행 처리)
    driver = run_subject_searches_from_data("인공지능공학과", max_rows_per_code=None)
    print("전공 학수번호 기반 검색 및 링크 순회 완료")
