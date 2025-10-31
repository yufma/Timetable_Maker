import React, { useState } from 'react'
import SearchBar from './SearchBar'
import FilterDropdown from './FilterDropdown'
import CourseCard from './CourseCard'
import './CourseSearchPage.css'

interface Course {
  id: number
  name: string
  courseNumber: string
  credits: string
  department: string
  tags: string[]
  sections: Section[]
}

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

const CourseSearchPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('전체 분류')
  const [departmentFilter, setDepartmentFilter] = useState('전체 학과')

  // 샘플 강의 데이터 (더 많은 데이터 추가)
  const allCourses: Course[] = [
    {
      id: 1,
      name: '자료구조',
      courseNumber: 'CSE2010',
      credits: '3학점',
      department: '컴퓨터공학과',
      tags: ['전공필수', 'CSE2010', '3학점'],
      sections: [
        {
          id: 1,
          sectionNumber: '01분반',
          professor: '김교수',
          time: '월 09:00-10:30 수 09:00-10:30',
          enrolled: '45',
          capacity: '60',
          teamProject: '팀플 10%',
        },
        {
          id: 2,
          sectionNumber: '02분반',
          professor: '이교수',
          time: '화 13:00-14:30 목 13:00-14:30',
          enrolled: '52',
          capacity: '60',
          teamProject: '팀플 0% (없음)',
        },
      ],
    },
    {
      id: 2,
      name: '알고리즘',
      courseNumber: 'CSE3010',
      credits: '3학점',
      department: '컴퓨터공학과',
      tags: ['전공필수', 'CSE3010', '3학점'],
      sections: [
        {
          id: 1,
          sectionNumber: '01분반',
          professor: '박교수',
          time: '월 14:00-15:30 수 14:00-15:30',
          location: '공학관 401',
          enrolled: '48',
          capacity: '50',
          teamProject: '팀플 비중: 10%',
        },
      ],
    },
    {
      id: 3,
      name: '데이터베이스',
      courseNumber: 'CSE2020',
      credits: '3학점',
      department: '컴퓨터공학과',
      tags: ['전공필수', 'CSE2020', '3학점'],
      sections: [
        {
          id: 1,
          sectionNumber: '01분반',
          professor: '최교수',
          time: '월 11:00-12:30 수 11:00-12:30',
          enrolled: '38',
          capacity: '60',
          teamProject: '팀플 15%',
        },
      ],
    },
    {
      id: 4,
      name: '컴퓨터네트워크',
      courseNumber: 'CSE3020',
      credits: '3학점',
      department: '컴퓨터공학과',
      tags: ['전공선택', 'CSE3020', '3학점'],
      sections: [
        {
          id: 1,
          sectionNumber: '01분반',
          professor: '정교수',
          time: '화 10:00-11:30 목 10:00-11:30',
          enrolled: '42',
          capacity: '50',
          teamProject: '팀플 5%',
        },
      ],
    },
    {
      id: 5,
      name: '현대사회와 윤리',
      courseNumber: 'GEN1001',
      credits: '2학점',
      department: '전기공학과',
      tags: ['교양', 'GEN1001', '2학점'],
      sections: [
        {
          id: 1,
          sectionNumber: '01분반',
          professor: '한교수',
          time: '화 15:00-17:00',
          enrolled: '55',
          capacity: '80',
          teamProject: '팀플 0% (없음)',
        },
      ],
    },
  ]

  // 검색 및 필터링 로직
  const filteredCourses = allCourses.filter((course) => {
    // 검색어 필터
    const matchesSearch =
      !searchQuery ||
      course.name.includes(searchQuery) ||
      course.courseNumber.includes(searchQuery) ||
      course.sections.some((section) => section.professor.includes(searchQuery))

    // 분류 필터
    const matchesCategory =
      categoryFilter === '전체 분류' ||
      (categoryFilter === '전공필수' && course.tags.includes('전공필수')) ||
      (categoryFilter === '전공선택' && course.tags.includes('전공선택')) ||
      (categoryFilter === '교양' && course.tags.includes('교양'))

    // 학과 필터
    const matchesDepartment =
      departmentFilter === '전체 학과' || course.department === departmentFilter

    return matchesSearch && matchesCategory && matchesDepartment
  })

  const handleSearch = (query: string) => {
    setSearchQuery(query)
  }

  const resultCount = filteredCourses.length

  return (
    <div className="course-search-page">
      <div className="page-header">
        <h1 className="page-title">강의 검색</h1>
        <p className="page-subtitle">강의명, 학수번호, 교수명으로 검색하세요</p>
      </div>

      <div className="search-section">
        <SearchBar onSearch={handleSearch} />
        <div className="filters">
          <FilterDropdown
            label="전체 분류"
            options={['전체 분류', '전공필수', '전공선택', '교양']}
            value={categoryFilter}
            onChange={setCategoryFilter}
          />
          <FilterDropdown
            label="전체 학과"
            options={['전체 학과', '컴퓨터공학과', '전기공학과', '기계공학과']}
            value={departmentFilter}
            onChange={setDepartmentFilter}
          />
        </div>
        <p className="result-count">{resultCount}개의 강의가 검색되었습니다</p>
      </div>

      <div className="courses-list">
        {filteredCourses.length > 0 ? (
          filteredCourses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))
        ) : (
          <div className="no-results">
            <p>검색 결과가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default CourseSearchPage

