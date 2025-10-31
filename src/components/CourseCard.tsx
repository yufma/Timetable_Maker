import React, { useState } from 'react'
import { useWishlist } from '../contexts/WishlistContext'
import CourseSection from './CourseSection'
import './CourseCard.css'

interface Section {
  id: number
  sectionNumber: string
  professor: string
  time: string
  location?: string
  enrolled: string
  capacity: string
  teamProject: string
}

interface CourseCardProps {
  course: {
    id: number
    name: string
    courseNumber: string
    credits: string
    department: string
    tags: string[]
    sections: Section[]
  }
}

const CourseCard: React.FC<CourseCardProps> = ({ course }) => {
  const { isInWishlist, toggleWishlist } = useWishlist()
  const [showAllSections, setShowAllSections] = useState(false)

  const isFavorite = isInWishlist(course.id)

  const handleFavoriteClick = () => {
    toggleWishlist(course)
  }

  const hasMultipleSections = course.sections.length > 1

  return (
    <div className="course-card">
      <div className="course-card-header">
        <div className="course-title-section">
          <h2 className="course-name">{course.name}</h2>
          <div className="course-tags">
            {course.tags.map((tag, index) => (
              <span
                key={index}
                className={`tag ${tag === '전공필수' ? 'required' : ''}`}
              >
                {tag}
              </span>
            ))}
          </div>
          <p className="course-department">{course.department}</p>
        </div>
        <button
          className={`favorite-button ${isFavorite ? 'active' : ''}`}
          onClick={handleFavoriteClick}
          aria-label="찜하기"
        >
          {isFavorite ? '❤️' : '♡'}
        </button>
      </div>

      {hasMultipleSections && (
        <div className="section-comparison">
          <button
            className="compare-button"
            onClick={() => setShowAllSections(!showAllSections)}
          >
            {course.sections.length}개 분반 비교하기
          </button>
        </div>
      )}

      <div className="course-sections">
        {course.sections.map((section, index) => (
          <CourseSection
            key={section.id}
            section={section}
            isExpanded={showAllSections || !hasMultipleSections || index === 0}
          />
        ))}
      </div>
    </div>
  )
}

export default CourseCard

