import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Header.css'

const Header: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const isActive = (path: string) => {
    return location.pathname === path ? 'active' : ''
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo">
          <span className="logo-icon">🎓</span>
          <span className="logo-text">시간표 추천 시스템</span>
        </Link>
        <nav className="nav">
          <Link to="/" className={`nav-item ${isActive('/')}`}>
            <span className="nav-icon">🏠</span>
            <span>홈</span>
          </Link>
          <Link to="/search" className={`nav-item ${isActive('/search')}`}>
            <span className="nav-icon">🔍</span>
            <span>강의 검색</span>
          </Link>
          <Link to="/schedule" className={`nav-item ${isActive('/schedule')}`}>
            <span className="nav-icon">📅</span>
            <span>시간표 추천</span>
          </Link>
          <Link to="/wishlist" className={`nav-item ${isActive('/wishlist')}`}>
            <span className="nav-icon">❤️</span>
            <span>찜 목록</span>
          </Link>
        </nav>
        <div className="user-info">
          <span className="user-name">{user?.studentId}학번님</span>
          <button onClick={handleLogout} className="logout">
            <span className="logout-icon">🚪</span>
            <span>로그아웃</span>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header

