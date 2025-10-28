# 대학교 수강신청 시간표 추천 시스템

사용자가 원하는 시간대와 제외하고 싶은 시간대를 입력하면, 학과 정보와 수강 완료 과목을 바탕으로 최적의 시간표를 자동으로 생성해주는 시스템입니다.

## 주요 기능

### 📚 과목 추천 우선순위
1. **기초교양** - 필수 교양 과목
2. **전공필수** - 전공 필수 과목
3. **전공선택** - 전공 선택 과목
4. **핵심교양** - 핵심 교양 과목

### ✨ 핵심 기능
- **시간표 자동 생성**: 원하는/제외 시간대 기반 최적 시간표 추천
- **강의계획서 요약**: 팀플 비중, 과제 비중, 평가 방식 한눈에 확인
- **찜 기능**: 관심 강의 저장 및 관리
- **분반 비교**: 같은 과목의 다른 분반 비교
- **강의 검색**: 과목명, 교수명, 과목 코드로 검색
- **로그인 시스템**: 학번과 비밀번호 기반 인증

### 📱 반응형 디자인
- 데스크톱, 태블릿, 모바일 모든 기기 지원

## 기술 스택

- **Frontend**: React 18 + TypeScript
- **Styling**: Tailwind CSS 4.0
- **UI Components**: Radix UI
- **Icons**: Lucide React
- **Build Tool**: Vite
- **State Management**: React Hooks + LocalStorage

## 시작하기

### 설치

```bash
# 의존성 설치
npm install
# 또는
yarn install
# 또는
pnpm install
```

### 개발 서버 실행

```bash
npm run dev
# 또는
yarn dev
# 또는
pnpm dev
```

개발 서버가 `http://localhost:5173`에서 실행됩니다.

### 빌드

```bash
npm run build
# 또는
yarn build
# 또는
pnpm build
```

### 프리뷰

```bash
npm run preview
# 또는
yarn preview
# 또는
pnpm preview
```

## 프로젝트 구조

```
├── App.tsx                      # 메인 애플리케이션 컴포넌트
├── main.tsx                     # 애플리케이션 진입점
├── components/                  # React 컴포넌트
│   ├── LoginPage.tsx           # 로그인 페이지
│   ├── HomePage.tsx            # 홈페이지
│   ├── Navigation.tsx          # 네비게이션 바
│   ├── CourseSearchPage.tsx    # 강의 검색 페이지
│   ├── CourseDetailPage.tsx    # 강의 상세 페이지
│   ├── BookmarksPage.tsx       # 찜한 강의 페이지
│   ├── TimetableRecommendPage.tsx  # 시간표 추천 페이지
│   ├── TimetableView.tsx       # 시간표 뷰 컴포넌트
│   └── ui/                     # UI 컴포넌트 라이브러리
├── data/
│   └── mockCourses.ts          # 목업 강의 데이터
├── types/
│   └── course.ts               # TypeScript 타입 정의
├── hooks/
│   └── useLocalStorage.ts      # LocalStorage 커스텀 훅
└── styles/
    └── globals.css             # 전역 스타일
```

## 사용 방법

### 1. 로그인
- 학번과 비밀번호를 입력하여 로그인 (현재는 목업 데이터 사용)

### 2. 강의 검색
- 과목명, 교수명, 과목 코드로 강의 검색
- 학년, 학점, 과목 유형으로 필터링
- 찜 버튼으로 관심 강의 저장

### 3. 시간표 추천
- 학과 정보 입력
- 수강 완료 과목 선택
- 원하는 시간대/제외 시간대 설정
- AI 기반 최적 시간표 자동 생성

### 4. 강의 상세보기
- 강의계획서 요약 확인
- 팀플 비중, 과제 비중, 평가 방식 확인
- 분반 비교 기능 활용

### 5. 찜한 강의
- 찜한 강의 목록 관리
- 한 번에 시간표에 추가

## 데이터 구조

### Course (강의)
```typescript
{
  id: string;              // 고유 ID
  courseCode: string;      // 과목 코드
  courseName: string;      // 과목명
  professor: string;       // 교수명
  credits: number;         // 학점
  courseType: string;      // 과목 유형
  grade: number;           // 학년
  schedule: Array<{        // 수업 시간
    day: string;
    startTime: string;
    endTime: string;
  }>;
  capacity: number;        // 정원
  enrolled: number;        // 수강 인원
  syllabus: {             // 강의계획서
    teamProjectWeight: number;
    assignmentWeight: number;
    evaluationMethod: string;
    description: string;
  };
}
```

## 개발 팁

### Cursor AI에서 작업하기
1. 이 프로젝트를 Cursor AI에서 열기
2. `npm install`로 의존성 설치
3. `npm run dev`로 개발 서버 실행
4. Cursor의 AI 기능으로 코드 수정 및 개선

### 목업 데이터 수정
`/data/mockCourses.ts` 파일에서 강의 데이터를 수정할 수 있습니다.

### 새로운 컴포넌트 추가
`/components` 폴더에 새 컴포넌트를 추가하고 `App.tsx`에서 import하여 사용하세요.

## 라이선스

MIT License

## 기여

이 프로젝트는 대학교 수강신청 시스템 개선을 위한 프로토타입입니다. 
피드백과 개선 제안은 언제나 환영합니다!
