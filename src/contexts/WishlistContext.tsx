import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useAuth } from './AuthContext'

interface Course {
  id: number
  name: string
  courseNumber: string
  credits: string
  department: string
  tags: string[]
  sections: any[]
}

interface WishlistContextType {
  wishlist: Course[]
  addToWishlist: (course: Course) => void
  removeFromWishlist: (courseId: number) => void
  isInWishlist: (courseId: number) => boolean
  toggleWishlist: (course: Course) => void
}

const WishlistContext = createContext<WishlistContextType | undefined>(undefined)

export const useWishlist = () => {
  const context = useContext(WishlistContext)
  if (context === undefined) {
    throw new Error('useWishlist must be used within a WishlistProvider')
  }
  return context
}

interface WishlistProviderProps {
  children: ReactNode
}

export const WishlistProvider: React.FC<WishlistProviderProps> = ({ children }) => {
  const { user } = useAuth()
  const [wishlist, setWishlist] = useState<Course[]>([])

  useEffect(() => {
    if (user) {
      // 사용자별 찜 목록 로드
      const savedWishlist = localStorage.getItem(`wishlist_${user.studentId}`)
      if (savedWishlist) {
        setWishlist(JSON.parse(savedWishlist))
      }
    } else {
      setWishlist([])
    }
  }, [user])

  const saveWishlist = (newWishlist: Course[]) => {
    if (user) {
      localStorage.setItem(`wishlist_${user.studentId}`, JSON.stringify(newWishlist))
    }
  }

  const addToWishlist = (course: Course) => {
    if (!isInWishlist(course.id)) {
      const newWishlist = [...wishlist, course]
      setWishlist(newWishlist)
      saveWishlist(newWishlist)
    }
  }

  const removeFromWishlist = (courseId: number) => {
    const newWishlist = wishlist.filter((course) => course.id !== courseId)
    setWishlist(newWishlist)
    saveWishlist(newWishlist)
  }

  const isInWishlist = (courseId: number) => {
    return wishlist.some((course) => course.id === courseId)
  }

  const toggleWishlist = (course: Course) => {
    if (isInWishlist(course.id)) {
      removeFromWishlist(course.id)
    } else {
      addToWishlist(course)
    }
  }

  return (
    <WishlistContext.Provider
      value={{ wishlist, addToWishlist, removeFromWishlist, isInWishlist, toggleWishlist }}
    >
      {children}
    </WishlistContext.Provider>
  )
}

