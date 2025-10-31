# 시간표 추천 시스템

React + TypeScript로 구성된 시간표 추천 시스템입니다.

## 🚀 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **React Router DOM** - 라우팅
- **Vite** - 빌드 도구 및 개발 서버
- **Context API** - 전역 상태 관리 (인증, 찜 목록)

## 📁 프로젝트 구조

```
time_table_ver3/
├── public/
│   └── index.html          # Vite 진입점 (최소한의 HTML만)
├── src/
│   ├── components/         # React 컴포넌트들 (TSX)
│   │   ├── Header.tsx
│   │   ├── LoginPage.tsx
│   │   ├── SignupPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── CourseSearchPage.tsx
│   │   ├── ScheduleRecommendationPage.tsx
│   │   ├── WishlistPage.tsx
│   │   └── ... (모든 UI 컴포넌트)
│   ├── contexts/          # Context API (전역 상태)
│   │   ├── AuthContext.tsx      # 인증 상태 관리
│   │   └── WishlistContext.tsx  # 찜 목록 상태 관리
│   ├── pages/             # 페이지 컴포넌트
│   │   └── HomePage.tsx
│   ├── App.tsx            # 메인 App 컴포넌트 (라우팅)
│   ├── index.tsx           # React 진입점
│   └── index.css           # 글로벌 스타일
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## ✨ 주요 기능

### 인증 시스템
- ✅ 로그인/회원가입
- ✅ Protected Route (인증 필요 페이지 보호)
- ✅ 로컬 스토리지 기반 세션 관리

### 강의 검색
- ✅ 실시간 검색 (강의명, 학수번호, 교수명)
- ✅ 필터링 (분류, 학과)
- ✅ 강의 상세 정보 표시

### 찜 목록
- ✅ 강의 찜하기/제거
- ✅ 찜 목록 관리
- ✅ 사용자별 찜 목록 저장

### 시간표 추천
- ✅ 기본 정보 입력 (학과, 학년)
- ✅ 제외할 시간대 선택
- ✅ 수강 완료 과목 선택

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속하세요.

### 3. 프로덕션 빌드
```bash
npm run build
```

빌드된 파일은 `dist/` 폴더에 생성됩니다.

## 📝 개발 가이드

### 컴포넌트 구조
- 모든 컴포넌트는 **함수형 컴포넌트**로 작성
- TypeScript로 타입 안정성 보장
- 각 컴포넌트마다 별도의 CSS 파일 분리

### 상태 관리
- **Context API** 사용 (AuthContext, WishlistContext)
- 로컬 스토리지로 데이터 영속성

### 라우팅
- **React Router DOM** 사용
- Protected Route로 인증 필요 페이지 보호

### 스타일링
- CSS 모듈 방식 (컴포넌트별 CSS 파일)
- 반응형 디자인 지원

## 🔐 인증 정보

현재 로컬 스토리지 기반 인증을 사용합니다:
- 회원가입 시 사용자 정보가 로컬 스토리지에 저장됩니다
- 로그인 시 로컬 스토리지에서 사용자 정보를 확인합니다
- 프로덕션 환경에서는 실제 백엔드 API로 연동해야 합니다
