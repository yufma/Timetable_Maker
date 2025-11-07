# 짜요짜요 - 학과 시간표 추천 시스템

학과 커리큘럼, 전공/교양, 최애 교수, 강의 계획서까지 반영한 맞춤 시간표 추천 서비스

## 설치 방법

### 1. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python3 -m venv venv

# 활성화 (macOS/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

### 2. 의존성 설치
```bash
# 가상환경이 활성화된 상태에서 실행
# (venv) 프롬프트가 표시되어야 합니다
pip install -r requirements.txt

# 설치 확인
pip list | grep -E "fastapi|uvicorn|sqlmodel|pdfplumber"
# 또는 Windows에서
pip list | findstr "fastapi uvicorn sqlmodel pdfplumber"
```

### 3. 환경 변수 설정 (선택사항)
```bash
# .env.example 파일이 있다면 .env로 복사
cp .env.example .env  # macOS/Linux
copy .env.example .env  # Windows

# .env 파일을 열어서 OpenAI API 키를 입력 (AI 추천 기능 사용 시 필요)
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. 데이터베이스 초기화
```bash
# 가상환경이 활성화된 상태에서 실행
# 전체 초기화 스크립트 실행 (권장)
python scripts/setup_all.py

# 또는 단계별로 실행
python scripts/init_db.py        # 데이터베이스 테이블 생성
python scripts/import_data.py    # 데이터 적재
python scripts/export_summaries.py  # 요약본 생성
python scripts/load_pdfs.py      # PDF 정보 로드
```

### 5. 서버 실행
```bash
# 가상환경이 활성화된 상태에서 실행
# 방법 1: python -m uvicorn (권장)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 방법 2: 직접 uvicorn 실행
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. 브라우저에서 접속
서버 실행 후 다음 URL로 접속:
```
http://127.0.0.1:8000/
```

**주요 페이지:**
- 홈: `http://127.0.0.1:8000/`
- 로그인: `http://127.0.0.1:8000/login`
- 강의 검색: `http://127.0.0.1:8000/lecture-search`
- 시간표 추천: `http://127.0.0.1:8000/recommend`
- 교과과정표: `http://127.0.0.1:8000/curriculum`
- API 문서: `http://127.0.0.1:8000/docs`

## 주요 기능

- 강의 검색: 강의명/학수번호, 교수명으로 검색
- 강의계획서: 원본 PDF 및 요약본 제공
- 교과과정표: 학과별 교과과정표 PDF 다운로드
- 시간표 추천: AI 기반 맞춤 시간표 추천

## 프로젝트 구조

```
timetable/
├── app/                           # FastAPI 애플리케이션
│   ├── main.py                    # 메인 서버 파일 (라우팅, 세션 관리)
│   ├── api_subjects.py            # 강의 검색 및 조회 API 엔드포인트
│   ├── auth.py                    # 사용자 인증 (로그인/회원가입/세션)
│   ├── algorithm.py               # 시간표 생성 알고리즘 (충돌 검사, 스케줄 생성)
│   ├── db_bridge.py               # 데이터베이스 세션 관리
│   ├── models.py                  # SQLModel 기반 사용자 모델
│   │
│   ├── data/                      # 데이터 관리
│   │   └── majors.py              # 단과대/전공 정보 (FACULTIES, MAJORS)
│   │
│   ├── db/                        # 데이터베이스 모델 및 설정
│   │   ├── base.py                # SQLAlchemy Base 설정
│   │   ├── config.py              # DB 설정 (경로, 디렉토리)
│   │   ├── session.py             # DB 세션 팩토리
│   │   │
│   │   ├── models/                # 데이터베이스 모델
│   │   │   ├── subject.py         # 강의 정보 (학수번호, 강의명, 학점 등)
│   │   │   ├── subject_summary.py # 강의 요약 정보
│   │   │   ├── subject_pdf.py     # 강의계획서 PDF 정보
│   │   │   ├── common_subject.py  # 교양 과목 정보
│   │   │   ├── department_curriculum.py  # 학과 커리큘럼
│   │   │   ├── department_pdf.py  # 학과 교과과정표 PDF
│   │   │   ├── favorite.py        # 찜 기능 (강의, 교수, 시간표)
│   │   │   └── transcript.py      # 성적표 및 수강 이력
│   │   │
│   │   └── seed/                  # 데이터 시딩
│   │       └── load_json.py       # JSON 데이터 로드
│   │
│   ├── templates/                 # Jinja2 HTML 템플릿
│   │   ├── base.html              # 기본 레이아웃
│   │   ├── home.html              # 홈 페이지
│   │   ├── login.html             # 로그인 페이지
│   │   ├── signup.html            # 회원가입 페이지
│   │   ├── mypage.html            # 마이페이지
│   │   ├── account_edit.html      # 계정 수정
│   │   ├── lecture_search.html    # 강의 검색
│   │   ├── curriculum.html        # 교과과정표 조회
│   │   ├── favorites.html         # 찜 목록
│   │   ├── recommend.html         # 시간표 추천 (7단계)
│   │   └── view_summary.html      # 강의계획서 요약 보기
│   │
│   ├── static/                    # 정적 파일
│   │   └── custom.css             # 커스텀 CSS
│   │
│   └── utils/                     # 유틸리티 함수
│       ├── pdf_parser.py          # PDF 파싱 (성적표, 강의계획서)
│       ├── recommendation.py      # AI 추천 로직 (OpenAI)
│       └── logs/                  # 추천 로그
│
├── data/                          # 원본 데이터 파일
│   ├── subject_json/              # 강의 정보 JSON (756개)
│   ├── subject_pdf/               # 강의계획서 PDF (740개)
│   ├── department_pdf/            # 교과과정표 PDF
│   ├── common_subjects_json/      # 교양 과목 정보 JSON
│   └── depart_json/               # 학과 정보 JSON
│
├── exports/                       # 생성된 파일
│   ├── index.html                 # 요약본 인덱스
│   └── subjects/                  # 강의 요약본 (HTML/MD)
│
├── scripts/                       # 유틸리티 스크립트
│   ├── setup_all.py               # 전체 환경 설정 (일괄 실행)
│   ├── init_db.py                 # 데이터베이스 초기화
│   ├── clear_db.py                # 데이터베이스 비우기
│   ├── import_data.py             # 데이터 적재
│   ├── export_summaries.py        # 강의 요약본 생성
│   ├── load_pdfs.py               # PDF 파일 정보 DB에 로드
│   ├── check_db.py                # 데이터베이스 상태 확인
│   ├── verify_counts.py           # 데이터 개수 검증
│   └── verify_exports.py          # 요약본 검증
│
├── app.db                         # SQLite 데이터베이스 파일
├── requirements.txt               # Python 패키지 의존성
├── README.md                      # 이 문서
└── DEPLOY.md                      # 배포 가이드
```

### 주요 디렉토리 설명

#### `app/`
- **`main.py`**: FastAPI 애플리케이션의 진입점. 라우팅, 세션 관리, 페이지 렌더링 담당
- **`api_subjects.py`**: 강의 검색, 찜 기능, PDF 제공 등의 REST API 엔드포인트
- **`algorithm.py`**: 시간표 생성 알고리즘. 시간 충돌 검사, 스케줄 조합 생성
- **`auth.py`**: 사용자 인증 로직 (비밀번호 해싱, 세션 관리)
- **`db/models/`**: 데이터베이스 모델 정의 (Subject, CommonSubject, Favorite 등)
- **`utils/recommendation.py`**: OpenAI API를 사용한 AI 기반 시간표 추천

#### `data/`
- 원본 데이터 파일 저장소
- JSON 파일: 강의 정보, 교양 과목 정보
- PDF 파일: 강의계획서, 교과과정표

#### `scripts/`
- 데이터베이스 초기화 및 데이터 적재 스크립트
- `setup_all.py`: 모든 초기화 작업을 순차적으로 실행

#### `exports/`
- 생성된 강의 요약본 (HTML형식)
- 정적 파일로 제공되어 웹에서 조회 가능