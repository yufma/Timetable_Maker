## 개요
이 디렉토리는 "과목/교양/교과과정 JSON"을 SQL 데이터베이스에 적재하고 확인하는 스크립트 모음입니다. 시간표 추천의 기반 데이터베이스를 구축하는 단계까지 구현되어 있습니다.

- 지원 데이터 소스
  - `subject_json`: 인공지능공학과 전공/기초교양 과목 상세(JSON)
  - `common_subjects_json`: 핵심교양/일반교양/창의 영역 과목 목록(JSON)
  - `depart_json`: 인공지능공학과 교과과정표(JSON)

## 디렉토리 구조
- `app/db/`
  - `config.py`: 환경변수 로딩 및 `DATABASE_URL`, 소스 디렉토리 경로 정의
  - `session.py`: SQLAlchemy 엔진/세션 팩토리
  - `base.py`: Declarative Base
  - `models/`
    - `common_subject.py`: 핵심/일반/창의 교양 항목
    - `department_curriculum.py`: 교과과정표 항목(종별/세부구분/이수시기 등)
    - `subject.py`: 전공/기초교양 과목(코드/이름 등)
  - `seed/`
    - `load_json.py`: 세 디렉토리의 JSON을 읽어 테이블에 적재
- `scripts/`
  - `init_db.py`: 테이블 생성
  - `import_data.py`: 환경변수 경로에서 JSON 적재 실행
  - `verify_counts.py`: 테이블별 건수/샘플 출력
  - `clear_db.py`: 모든 테이블 비우기(재적재 시 중복 방지)

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- 현재 requirements.txt 포함: SQLAlchemy, python-dotenv (FastAPI 등은 추후 API 단계에서 사용 예정일 수 있음)

## 환경변수 설정(macOS 예시)
```bash
export DATABASE_URL="sqlite:///./app.db"
export COMMON_SUBJECTS_DIR="/Users/choeseong-yong/Downloads/common_subjects_pdf/common_subjects_json"
export DEPARTMENT_CURRICULUM_DIR="/Users/choeseong-yong/Downloads/common_subjects_pdf/depart_json"
export SUBJECTS_DIR="/Users/choeseong-yong/Downloads/common_subjects_pdf/subject_json"
```

## 사용법
1) 테이블 생성
```bash
python scripts/init_db.py
```
2) (선택) 초기화 후 재적재
```bash
python scripts/clear_db.py
```
3) 데이터 적재
```bash
python scripts/import_data.py
```
4) 검증
```bash
python scripts/verify_counts.py
```

## 스키마 개요
- `common_subjects(category, area, code, name)`
- `department_curriculum(year_term, track, code, name)`
- `subjects(category, code, name)`

## 로더 매핑 규칙(요약)
- 리스트/단일 객체 JSON 모두 처리
- 한국어/일반 키 자동 인식
  - 과목코드: `code | 과목코드 | 학수번호 | id`
  - 과목명: `name | 과목명 | 교과목명 | title`
  - 이수시기: `year_term | 학년학기 | 학년/학기 | 이수시기`
  - 종별/영역: `track | 영역 | 과정 | 종 별 | 세부구분`
- `common_subjects`: 파일명 `카테고리-영역.json`에서 카테고리/영역 자동 추론
- NaN 값은 빈 값으로 처리

## 자주 쓰는 명령어
```bash
# 최초 설치
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 테이블 생성 → 적재 → 검증
python scripts/init_db.py && python scripts/import_data.py && python scripts/verify_counts.py

# 재적재(초기화 포함)
python scripts/clear_db.py && python scripts/import_data.py && python scripts/verify_counts.py
```

## 트러블슈팅
- `ModuleNotFoundError: No module named 'app'`: 스크립트에 프로젝트 루트 경로 추가되어 있어야 합니다(이미 처리됨).
- `no such table`: `python scripts/init_db.py`로 테이블 생성 후 다시 실행.
- 적재 건수 2배로 보임: 기존 데이터 위에 재적재된 경우 → `python scripts/clear_db.py` 후 재적재.

## 다음 단계(선택)
- API 추가(FastAPI): 선택 목록/검색/추천 엔드포인트
- 시간표 추천 로직: 시간 파싱/충돌 검사/학점 제한 최적화
