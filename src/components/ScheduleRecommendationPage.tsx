import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import BasicInfoSection from './BasicInfoSection'
import TimeExclusionSection from './TimeExclusionSection'
import CompletedCoursesSection from './CompletedCoursesSection'
import './ScheduleRecommendationPage.css'

const ScheduleRecommendationPage: React.FC = () => {
  const { user } = useAuth()
  const [department, setDepartment] = useState('')
  const [grade, setGrade] = useState('')
  const [excludedTimes, setExcludedTimes] = useState<Set<string>>(new Set())
  const [completedCourses, setCompletedCourses] = useState<Set<string>>(
    new Set(['알고리즘', '현대사회와 윤리', '인공지능', '글쓰기의 기초', '데이터베이스', '미술과 문화'])
  )

  // 사용자 정보에서 기본값 설정
  useEffect(() => {
    if (user) {
      if (user.department) {
        setDepartment(user.department)
      } else {
        setDepartment('컴퓨터공학과') // 기본값
      }
      if (user.grade) {
        setGrade(user.grade)
      } else {
        setGrade('2학년') // 기본값
      }
    }
  }, [user])

  const handleRecommend = () => {
    // 시간표 추천 로직 (향후 API 연동)
    console.log('Department:', department)
    console.log('Grade:', grade)
    console.log('Excluded Times:', excludedTimes)
    console.log('Completed Courses:', completedCourses)
    alert('시간표 추천 기능은 준비 중입니다.')
  }

  return (
    <div className="schedule-recommendation-page">
      <div className="page-header">
        <h1 className="page-title">시간표 추천 설정</h1>
        <p className="page-subtitle">정보를 입력하면 최적의 시간표를 추천해드립니다</p>
      </div>

      <div className="sections-container">
        <BasicInfoSection
          department={department}
          grade={grade}
          onDepartmentChange={setDepartment}
          onGradeChange={setGrade}
        />

        <TimeExclusionSection
          excludedTimes={excludedTimes}
          onExcludedTimesChange={setExcludedTimes}
        />

        <CompletedCoursesSection
          completedCourses={completedCourses}
          onCompletedCoursesChange={setCompletedCourses}
        />
      </div>

      <div className="footer-button-container">
        <button className="recommend-button" onClick={handleRecommend}>
          <span className="recommend-icon">✨</span>
          <span>시간표 추천받기</span>
        </button>
      </div>
    </div>
  )
}

export default ScheduleRecommendationPage

