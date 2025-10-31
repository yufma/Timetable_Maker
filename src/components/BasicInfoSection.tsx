import React from 'react'
import FilterDropdown from './FilterDropdown'
import './BasicInfoSection.css'

interface BasicInfoSectionProps {
  department: string
  grade: string
  onDepartmentChange: (value: string) => void
  onGradeChange: (value: string) => void
}

const BasicInfoSection: React.FC<BasicInfoSectionProps> = ({
  department,
  grade,
  onDepartmentChange,
  onGradeChange,
}) => {
  const departments = [
    '인공지능공학과',
    '컴퓨터공학과',
    '전기공학과',
    '기계공학과',
    '화학공학과',
    '산업공학과',
  ]

  const grades = ['1학년', '2학년', '3학년', '4학년']

  return (
    <div className="basic-info-section">
      <h2 className="section-title">기본 정보</h2>
      <div className="basic-info-content">
        <div className="info-field">
          <label className="info-label">학과</label>
          <FilterDropdown
            label="학과"
            options={departments}
            value={department}
            onChange={onDepartmentChange}
          />
        </div>
        <div className="info-field">
          <label className="info-label">학년</label>
          <div className="grade-buttons">
            {grades.map((g) => (
              <button
                key={g}
                type="button"
                className={`grade-button ${grade === g ? 'active' : ''}`}
                onClick={() => onGradeChange(g)}
              >
                {g}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default BasicInfoSection

