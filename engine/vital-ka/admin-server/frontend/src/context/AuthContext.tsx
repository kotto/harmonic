// ──────────────────────────────────────────────
// Auth Context
// ──────────────────────────────────────────────
import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import type { UserInfo } from '../types'
import { api } from '../services/api'

interface AuthContextType {
  user: UserInfo | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('access_token')

    if (storedUser && token) {
      try {
        const currentUser = await api.getCurrentUser()
        setUser(currentUser)
        localStorage.setItem('user', JSON.stringify(currentUser))
      } catch (error) {
        console.error('Failed to refresh user:', error)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        setUser(null)
      }
    }
    setIsLoading(false)
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (email: string, password: string, rememberMe = false) => {
    const response = await api.login({ email, password, remember_me: rememberMe })
    setUser(response.user)
  }

  const logout = async () => {
    try {
      await api.logoutApi()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}