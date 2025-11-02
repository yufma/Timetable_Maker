import essentials
import load_curriculum
import load_common_curriculums
import load_subject
import read_curriculum
import read_common_curriculums
import read_subject
import load_subject_common

# headless 모드 설정: essentials.py의 HEADLESS_MODE 변수를 True/False로 변경하세요
# 현재 설정: essentials.HEADLESS_MODE = True (모든 드라이버가 headless 모드로 실행됨)
"""
load_common_curriculums.load_common_curriculums()
essentials.move_files_by_extension_to_pdf_dir("common_subjects_excels")

load_curriculum.load_departs(essentials.departs_restrict)
essentials.move_files_by_extension_to_pdf_dir("depart_excels")

read_curriculum.read_excel_rows(essentials.departs_restrict)
read_common_curriculums.read_excel_rows()

load_subject.run_subject_searches_from_data(essentials.departs_restrict)

load_subject_common.run_subject_searches_from_data()
essentials.move_files_by_extension_to_pdf_dir("subject_excel")
"""
read_subject.read_subject_excel_rows()



