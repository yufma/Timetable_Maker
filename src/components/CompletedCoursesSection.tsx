import React from 'react'
import './CompletedCoursesSection.css'

interface CompletedCoursesSectionProps {
  completedCourses: Set<string>
  onCompletedCoursesChange: (courses: Set<string>) => void
}

const CompletedCoursesSection: React.FC<CompletedCoursesSectionProps> = ({
  completedCourses,
  onCompletedCoursesChange,
}) => {
  const allCourses = [
    '자료구조',
    '알고리즘',
    '현대사회와 윤리',
    '인공지능',
    '글쓰기의 기초',
    '데이터베이스',
    '미술과 문화',
    '컴퓨터네트워크',
    '운영체제',
    '소프트웨어공학',
    '웹프로그래밍',
    '모바일프로그래밍',
  ]

  const toggleCourse = (course: string) => {
    const newCompletedCourses = new Set(completedCourses)
    
    if (newCompletedCourses.has(course)) {
      newCompletedCourses.delete(course)
    } else {
      newCompletedCourses.add(course)
    }
    
    onCompletedCoursesChange(newCompletedCourses)
  }

  // 2열로 나누기
  const midPoint = Math.ceil(allCourses.length / 2)
  const leftColumn = allCourses.slice(0, midPoint)
  const rightColumn = allCourses.slice(midPoint)

  return (
    <div className="completed-courses-section">
      <h2 className="section-title">수강 완료 과목</h2>
      <p className="section-subtitle">
        이미 수강한 과목을 선택하세요 (추천에서 제외됩니다)
      </p>
      
      <div className="courses-grid">
        <div className="courses-column">
          {leftColumn.map((course) => {
            const isChecked = completedCourses.has(course)
            return (
              <label key={course} className="course-checkbox-label">
                <input
                  type="checkbox"
                  className="course-checkbox"
                  checked={isChecked}
                  onChange={() => toggleCourse(course)}
                />
                <span className={`checkbox-indicator ${isChecked ? 'checked' : ''}`}>
                  {isChecked ? '✓' : ''}
                </span>
                <span className="course-name">{course}</span>
              </label>
            )
          })}
        </div>
        <div className="courses-column">
          {rightColumn.map((course) => {
            const isChecked = completedCourses.has(course)
            return (
              <label key={course} className="course-checkbox-label">
                <input
                  type="checkbox"
                  className="course-checkbox"
                  checked={isChecked}
                  onChange={() => toggleCourse(course)}
                />
                <span className={`checkbox-indicator ${isChecked ? 'checked' : ''}`}>
                  {isChecked ? '✓' : ''}
                </span>
                <span className="course-name">{course}</span>
              </label>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default CompletedCoursesSection

