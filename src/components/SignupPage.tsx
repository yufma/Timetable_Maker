import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './SignupPage.css'

const SignupPage: React.FC = () => {
  const [studentId, setStudentId] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [name, setName] = useState('')
  const [grade, setGrade] = useState('')
  const [department, setDepartment] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { signup } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    // 유효성 검사
    if (!studentId || !password || !confirmPassword || !name || !grade || !department) {
      setError('모든 필드를 입력해주세요.')
      setIsLoading(false)
      return
    }

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      setIsLoading(false)
      return
    }

    if (password.length < 4) {
      setError('비밀번호는 최소 4자 이상이어야 합니다.')
      setIsLoading(false)
      return
    }

    const success = await signup(studentId, password, name, grade, department)
    setIsLoading(false)

    if (success) {
      navigate('/')
    } else {
      setError('이미 존재하는 학번입니다.')
    }
  }

  return (
    <div className="signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <div className="logo-large">
            <span className="logo-icon">🎓</span>
            <h1 className="logo-text">시간표 추천 시스템</h1>
          </div>
          <p className="signup-subtitle">새 계정을 만들어 서비스를 시작하세요</p>
        </div>

        <form className="signup-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">이름</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="이름을 입력하세요"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="studentId">아이디 (학번)</label>
            <input
              type="text"
              id="studentId"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="학번을 입력하세요 (아이디는 학번으로 입력하세요)"
              className="form-input"
            />
            <small className="form-hint">아이디는 학번으로 입력하세요</small>
          </div>

          <div className="form-group">
            <label htmlFor="grade">학년</label>
            <select
              id="grade"
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
              className="form-input"
            >
              <option value="">학년을 선택하세요</option>
              <option value="1학년">1학년</option>
              <option value="2학년">2학년</option>
              <option value="3학년">3학년</option>
              <option value="4학년">4학년</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="department">학과</label>
            <select
              id="department"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="form-input"
            >
              <option value="">학과를 선택하세요</option>
              <option value="컴퓨터공학과">컴퓨터공학과</option>
              <option value="인공지능공학과">인공지능공학과</option>
              <option value="전기공학과">전기공학과</option>
              <option value="기계공학과">기계공학과</option>
              <option value="화학공학과">화학공학과</option>
              <option value="산업공학과">산업공학과</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요 (최소 4자)"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">비밀번호 확인</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="비밀번호를 다시 입력하세요"
              className="form-input"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="signup-button" disabled={isLoading}>
            {isLoading ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <div className="signup-footer">
          <p>
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="link-text">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default SignupPage

