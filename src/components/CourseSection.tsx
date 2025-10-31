import React from 'react'
import './CourseSection.css'

interface CourseSectionProps {
  section: {
    id: number
    sectionNumber: string
    professor: string
    time: string
    location?: string
    enrolled: string
    capacity: string
    teamProject: string
  }
  isExpanded: boolean
}

const CourseSection: React.FC<CourseSectionProps> = ({
  section,
  isExpanded,
}) => {
  if (!isExpanded) {
    return null
  }

  return (
    <div className="course-section">
      <div className="section-header">
        <h3 className="section-number">{section.sectionNumber}</h3>
      </div>
      <div className="section-details">
        <div className="detail-item">
          <span className="detail-icon">📖</span>
          <span className="detail-label">교수:</span>
          <span className="detail-value">{section.professor}</span>
        </div>
        <div className="detail-item">
          <span className="detail-icon">🕐</span>
          <span className="detail-label">시간:</span>
          <span className="detail-value">{section.time}</span>
        </div>
        {section.location && (
          <div className="detail-item">
            <span className="detail-label">장소:</span>
            <span className="detail-value">{section.location}</span>
          </div>
        )}
        <div className="detail-item">
          <span className="detail-icon">👥</span>
          <span className="detail-label">수강인원:</span>
          <span className="detail-value">
            {section.enrolled}/{section.capacity}명
          </span>
        </div>
        <div className="detail-item">
          <span className="detail-icon">📊</span>
          <span className="detail-label">팀플 비중:</span>
          <span className="detail-value">{section.teamProject}</span>
        </div>
      </div>
    </div>
  )
}

export default CourseSection

