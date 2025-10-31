import essentials
import load_curriculum
import load_common_curriculums
import load_subject
import read_curriculum
import read_common_curriculums
import read_subject
import load_subject_common
"""
load_common_curriculums.load_common_curriculums()
essentials.move_files_by_extension_to_pdf_dir("common_subjects_excels")

load_curriculum.load_departs(essentials.departs_restrict)
essentials.move_files_by_extension_to_pdf_dir("depart_excels")

read_curriculum.read_excel_rows(essentials.departs_restrict)
read_common_curriculums.read_excel_rows()

load_subject.run_subject_searches_from_data(essentials.departs_restrict)
essentials.move_files_by_extension_to_pdf_dir("subject_excel")

load_subject_common.run_subject_searches_from_data(essentials.departs_restrict)
essentials.move_files_by_extension_to_pdf_dir("common_subjects_excels")
"""
read_subject.read_subject_excel_rows()


