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
    driver = essentials.build_driver(download_dir="subject_excel")
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
    time.sleep(0.3)

    # 2) 결과 tbody 대기
    tbody_xpath = "/html/body/form/div[3]/div[2]/div[3]/div/table/tbody"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, tbody_xpath))
    )
    
    # 테이블 렌더링 완료 대기
    time.sleep(0.2)

    # 3) 행 개수 측정
    rows = driver.find_elements(By.XPATH, f"{tbody_xpath}/tr")
    total = len(rows)

    for i in range(1, total + 1):
        # 각 행 처리 전 딜레이
        time.sleep(0.1)
        
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
                time.sleep(0.1)  # 스크롤 후 대기
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
            time.sleep(0.3)

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

            # 페이지 로드 및 타입 판정
            if not new_window_opened:
                # 같은 창에서 갱신된 경우
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except Exception:
                    pass

            # 페이지 타입 판정: 타입 2인지 확인
            is_type2 = False
            try:
                type2_button_xpath = "/html/body/form/div[3]/div[2]/div[1]/span/input"
                # 타입 2 요소가 나타날 때까지 대기 (짧은 타임아웃)
                type2_element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, type2_button_xpath))
                )
                is_type2 = True
                print(f"타입 2 페이지 감지: {safe_file_name}")
            except Exception:
                # 타입 2가 아니면 정상, 넘어감
                pass

            # 타입별 처리
            if is_type2:
                # 타입 2: 페이지에서 정보 파싱하여 JSON 저장
                print(f"타입 2 페이지 처리 중: {safe_file_name}")
                try:
                    # 페이지 로드 완료 대기
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    time.sleep(0.3)  # 추가 로딩 대기
                    
                    # 데이터 파싱 및 저장
                    parse_type2_page(driver, safe_file_name)
                    
                    # 저장 완료 후 이전 페이지로 복귀
                    if new_window_opened:
                        driver.close()
                        driver.switch_to.window(list(prev_handles)[0])
                    else:
                        driver.back()
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, tbody_xpath))
                        )
                    time.sleep(0.2)  # 복귀 후 대기
                except Exception as e:
                    print(f"타입 2 처리 실패 ({safe_file_name}): {e}")
                    # 실패해도 이전 페이지로 복귀
                    if new_window_opened:
                        try:
                            driver.close()
                            driver.switch_to.window(list(prev_handles)[0])
                        except Exception:
                            pass
                    else:
                        try:
                            driver.back()
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, tbody_xpath))
                            )
                        except Exception:
                            pass
                continue

            # 타입 1: 기존 iframe 처리
            # iframe이 나타날 때까지 대기 (다운로드 페이지 로드 확인)
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "ireport"))
                )
                # iframe 로드 후 대기
                time.sleep(0.3)
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
                time.sleep(0.5)
            except Exception as e:
                print(f"다운로드 실패: {e}")
                import traceback
                traceback.print_exc()
            
            # 새 창이었으면 닫고 이전 창으로 복귀
            if new_window_opened:
                driver.close()
                time.sleep(0.1)  # 창 닫은 후 대기
                driver.switch_to.window(list(prev_handles)[0])
                time.sleep(0.2)  # 창 전환 후 대기
                # 복귀 후 tbody 재대기(갱신 대비)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, tbody_xpath))
                )
                time.sleep(0.2)  # tbody 로드 후 대기
            else:
                # 같은 창에서 갱신된 경우 이전 페이지로 복귀
                time.sleep(0.3)
                driver.back()
                # 복귀 후 tbody 재대기(갱신 대비)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, tbody_xpath))
                )
                time.sleep(0.2)  # tbody 로드 후 대기
        except Exception:
            # 개별 행 실패는 건너뛰고 다음 행 처리
            continue


def run_subject_searches_from_data(depart_restrict: list = []):
    """JSON 데이터에서 전공 계열의 학수번호만 골라 순차 검색 및 결과 링크 순회."""
    script_dir = Path(__file__).resolve().parent
    
    # depart_restrict가 비어있으면 depart_excels의 모든 엑셀 파일 처리
    if not depart_restrict:
        excel_files = essentials.list_filenames("depart_excels", pattern="*.xlsx")
        # 파일명에서 확장자 제거하여 학과명 추출
        depart_restrict = [Path(f).stem for f in excel_files]
        print(f"제한 없음: {len(depart_restrict)}개 학과를 모두 처리합니다.")
    else:
        print(f"제한 목록: {len(depart_restrict)}개 학과를 처리합니다.")
    
    # 모든 학과의 학수번호 수집
    all_codes = set()
    for dept_name in depart_restrict:
        try:
            subjects = load_department_subjects(dept_name)
            codes = extract_major_course_codes(subjects)
            all_codes.update(codes)
            print(f"{dept_name}: {len(codes)}개 학수번호")
        except Exception as e:
            print(f"{dept_name} 읽기 실패: {e}")
            continue
    
    if not all_codes:
        print("전공 학수번호가 없습니다.")
        return None
    
    codes = sorted(list(all_codes))
    print(f"\n총 {len(codes)}개 학수번호를 처리합니다.\n")

    driver = load_subject_depart("")  # 입력칸 포커싱만 진행, 내용은 비워둠

    input_xpath = "/html/body/form/div[3]/div[2]/div[1]/input[1]"
    for code in codes:
        try:
            # 각 코드 검색 전 딜레이
            time.sleep(0.2)
            
            target = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, input_xpath))
            )
            target.clear()
            time.sleep(0.1)  # clear 후 대기
            target.send_keys(code)
            time.sleep(0.1)  # 입력 후 대기
            
            search_and_visit_result_links(driver, max_rows=None)
            
            # 검색 완료 후 대기
            time.sleep(0.3)
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
    
    # 다운로드 완료 대기 헬퍼 (타임아웃 포함)
    download_dir = Path(essentials._resolve_download_dir("subject_excel"))

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
    
    # ===== iframe 안에서 저장 진행 =====
    iframe = wait.until(EC.presence_of_element_located((By.ID, "ireport")))
    driver.switch_to.frame(iframe)

    # 저장 버튼 클릭
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="report_menu_save_button"]'))).click()
    time.sleep(0.2)  # 저장 버튼 클릭 후 대기
    
    # 파일명 입력 부분 (비워둠 - 사용자가 채울 수 있음)
    filename_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_main_option_frame"]/div/div[2]/input'))
    )
    filename_input.clear()
    time.sleep(0.1)  # clear 후 대기
    # safe_file_name을 파라미터로 받아서 사용
    if filename:
        filename_input.send_keys(filename)
        time.sleep(0.1)  # 입력 후 대기

    # 파일 형식 선택 (xlsx)
    sheet_select = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="select_label"]'))
    )
    select = Select(sheet_select)
    select.select_by_value("xlsx")
    time.sleep(0.1)  # 선택 후 대기

    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_sub_option_change_button"]'))).click()

    sheet_select = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//*[@id="report_download_sub_option_frame"]/div/div[1]/div[1]/select')))
    select = Select(sheet_select)
    select.select_by_value("4")

    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download_sub_option_save_button"]'))).click()
    # Excel 다운로드 버튼 클릭
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
        if filename:
            filename_input.send_keys(filename)
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
    if filename:
        pdf_downloaded = wait_for_pdf_download(filename, appear_timeout=15.0, finish_timeout=90.0)
        if pdf_downloaded:
            print(f"  ✅ PDF 다운로드 완료: {filename}")
        else:
            print(f"  ⚠️ PDF 다운로드 타임아웃 또는 실패: {filename}")
    else:
        time.sleep(1.2)  # 파일명이 없으면 기본 대기

    # iframe에서 나오기
    driver.switch_to.default_content()


def parse_type2_page(driver, filename: str) -> bool:
    """타입 2 페이지에서 정보를 파싱하여 JSON 파일로 저장한다."""
    script_dir = Path(__file__).resolve().parent
    json_dir = script_dir / "subject_json"
    json_dir.mkdir(parents=True, exist_ok=True)
    
    # XPath 매핑
    xpath_mapping = {
        "강의명": "/html/body/form/div[3]/div[2]/div[2]/table[1]/tbody/tr[1]/td[1]/span",
        "교수명": "/html/body/form/div[3]/div[2]/div[2]/table[2]/tbody/tr[4]/td[1]/span",
        "학점": "/html/body/form/div[3]/div[2]/div[2]/table[2]/tbody/tr[3]/td[1]/span[1]",
        "강의시간": "/html/body/form/div[3]/div[2]/div[2]/table[1]/tbody/tr[3]/td[3]/span",
        "강의실": "/html/body/form/div[3]/div[2]/div[2]/table[2]/tbody/tr[4]/td[3]/span",
        "평가방식": "/html/body/form/div[3]/div[2]/div[2]/table[2]/tbody/tr[2]/td[3]/span",
        "중간고사": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[1]/span",
        "기말고사": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[2]/span",
        "출석": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[3]/span",
        "과제": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[4]/span",
        "퀴즈": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[5]/span",
        "토론": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[6]/span",
        "기타": "/html/body/form/div[3]/div[2]/div[2]/table[3]/tbody/tr[14]/td/table/tbody/tr[2]/td[7]/span",
    }
    
    # 데이터 추출
    data = {}
    wait = WebDriverWait(driver, 10)
    
    # 평가 항목 키워드 목록
    evaluation_keywords = ["중간고사", "기말고사", "출석", "과제", "퀴즈", "토론", "기타"]
    
    for key, xpath in xpath_mapping.items():
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            value = (element.text or "").strip()
            
            # 학점 처리: "3학점 (이론:3 , 설계:0 , 실험/실습:0)" 형태에서 숫자만 추출
            if key == "학점":
                if value:
                    # "3학점" 패턴에서 숫자 추출
                    match = re.search(r'(\d+\.?\d*)', value)
                    if match:
                        data[key] = match.group(1)
                    else:
                        data[key] = ""
                else:
                    data[key] = ""
            # 평가 비율 처리: 숫자만 있으면 "% " 추가
            elif key in evaluation_keywords:
                if value:
                    # 이미 %가 포함되어 있으면 그대로 사용
                    if '%' in value:
                        data[key] = value
                    else:
                        # 숫자만 있으면 "% " 추가
                        match = re.search(r'(\d+\.?\d*)', value)
                        if match:
                            num_value = match.group(1)
                            if float(num_value) == 0:
                                data[key] = "0 %"
                            else:
                                data[key] = f"{num_value} %"
                        else:
                            data[key] = "0 %"
                else:
                    data[key] = "0 %"
            else:
                data[key] = value if value else ""
        except Exception as e:
            # 요소를 찾지 못하면 빈 문자열 (평가 항목은 "0 %")
            if key in evaluation_keywords:
                data[key] = "0 %"
            else:
                data[key] = ""
            print(f"  경고: {key} 추출 실패 ({xpath})")
    
    # 강의시간 형식 변환 (타입 1 형식으로)
    강의실 = data.get("강의실", "").strip()
    강의시간 = data.get("강의시간", "").strip()
    
    if 강의시간:
        # 타입 2 형식: "월 1,월 2,월 3,수 1,수 2,수 3" -> 타입 1 형식: "강의실:월1,2,3,수1,2,3"
        # 요일별로 그룹화
        from collections import defaultdict
        요일별_시간 = defaultdict(list)
        
        # "월 1,월 2,월 3,수 1,수 2,수 3" 형식을 파싱
        parts = 강의시간.split(",")
        for part in parts:
            part = part.strip()
            if part:
                # 요일과 시간 분리 (예: "월 1" -> "월", "1")
                match = re.match(r'([월화수목금토일])\s*(\d+)', part)
                if match:
                    요일 = match.group(1)
                    시간 = match.group(2)
                    요일별_시간[요일].append(시간)
        
        # 타입 1 형식으로 변환: "월1,2,3,수1,2,3"
        if 요일별_시간:
            변환된_시간 = []
            for 요일 in ["월", "화", "수", "목", "금", "토", "일"]:
                if 요일 in 요일별_시간:
                    시간들 = ",".join(요일별_시간[요일])
                    변환된_시간.append(f"{요일}{시간들}")
            
            if 변환된_시간:
                최종_강의시간 = ",".join(변환된_시간)
                # 강의실 정보가 있으면 앞에 붙이기
                if 강의실:
                    data["강의시간"] = f"{강의실}:{최종_강의시간}"
                else:
                    data["강의시간"] = 최종_강의시간
    
    # 강의실 키는 제거 (최종 결과에는 강의시간에 포함됨)
    if "강의실" in data:
        del data["강의실"]
    
    # JSON 파일로 저장
    json_filename = f"{filename}.json"
    json_path = json_dir / json_filename
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 타입 2 JSON 저장 완료: {json_filename}")
        return True
    except Exception as e:
        print(f"  ✗ JSON 저장 실패 ({json_filename}): {e}")
        return False


def can_search_by_course_code(code: str, subjects: List[Dict[str, Any]]) -> bool:
    """주어진 code가 전공 계열 항목의 학수번호에 존재하는지 여부 반환."""
    if not code:
        return False
    return code.strip() in extract_major_course_codes(subjects)

if __name__ == "__main__":
    # JSON 기반으로 전공 학수번호를 순회 검색 (code_semester와 일치하는 모든 행 처리)
    # essentials.departs_restrict를 인수로 전달 (비어있으면 모든 학과 처리)
    driver = run_subject_searches_from_data(essentials.departs_restrict)
    print("\n전공 학수번호 기반 검색 및 링크 순회 완료")
