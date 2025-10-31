import React from 'react'
import { Link } from 'react-router-dom'
import { useWishlist } from '../contexts/WishlistContext'
import CourseCard from './CourseCard'
import './WishlistPage.css'

const WishlistPage: React.FC = () => {
  const { wishlist } = useWishlist()
  const wishlistCount = wishlist.length

  return (
    <div className="wishlist-page">
      <div className="page-header">
        <h1 className="page-title">찜한 강의</h1>
        <p className="page-subtitle">{wishlistCount}개의 강의를 찜했습니다</p>
      </div>
      {wishlistCount > 0 ? (
        <div className="wishlist-courses">
          {wishlist.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      ) : (
        <div className="empty-wishlist-card">
          <span className="empty-wishlist-icon">♡</span>
          <p className="empty-wishlist-message">찜한 강의가 없습니다</p>
          <p className="empty-wishlist-cta">관심있는 강의를 찜 목록에 추가해보세요</p>
          <Link to="/search" className="go-to-search-button">
            강의 검색하러 가기
          </Link>
        </div>
      )}
    </div>
  )
}

export default WishlistPage

