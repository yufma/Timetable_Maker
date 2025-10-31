import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  studentId: string
  name: string
  grade?: string
  department?: string
}

interface AuthContextType {
  user: User | null
  login: (studentId: string, password: string) => Promise<boolean>
  signup: (studentId: string, password: string, name: string, grade: string, department: string) => Promise<boolean>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    // 페이지 로드 시 로컬 스토리지에서 사용자 정보 확인
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const login = async (studentId: string, password: string): Promise<boolean> => {
    // 로컬 스토리지에서 사용자 정보 확인
    const savedUsers = localStorage.getItem('users')
    if (savedUsers) {
      const users = JSON.parse(savedUsers)
      const foundUser = users.find(
        (u: any) => u.studentId === studentId && u.password === password
      )
      if (foundUser) {
        const userData = {
          studentId: foundUser.studentId,
          name: foundUser.name,
          grade: foundUser.grade,
          department: foundUser.department,
        }
        setUser(userData)
        localStorage.setItem('user', JSON.stringify(userData))
        return true
      }
    }
    return false
  }

  const signup = async (
    studentId: string,
    password: string,
    name: string,
    grade: string,
    department: string
  ): Promise<boolean> => {
    // 로컬 스토리지에서 기존 사용자 확인
    const savedUsers = localStorage.getItem('users')
    let users = savedUsers ? JSON.parse(savedUsers) : []
    
    // 이미 존재하는 학번인지 확인
    if (users.some((u: any) => u.studentId === studentId)) {
      return false
    }

    // 새 사용자 추가
    users.push({ studentId, password, name, grade, department })
    localStorage.setItem('users', JSON.stringify(users))

    // 자동 로그인
    const userData = { studentId, name, grade, department }
    setUser(userData)
    localStorage.setItem('user', JSON.stringify(userData))
    return true
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('user')
  }

  const isAuthenticated = user !== null

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

