import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

interface User {
  id: number
  email: string
  role: 'restaurant' | 'admin'
  business_name?: string
  subscription_tier?: string
  subscription_status?: string
  trial_ends_at?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string, isAdmin?: boolean) => Promise<void>
  signup: (data: SignupData) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
  isRestaurant: boolean
}

interface SignupData {
  business_name: string
  owner_email: string
  password: string
  phone: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      fetchCurrentUser(token)
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async (token: string) => {
    try {
      const response = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      localStorage.removeItem('auth_token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string, isAdmin = false) => {
    try {
      if (isAdmin) {
        // Admin login
        const response = await api.post('/auth/admin/login', {
          email,
          password
        })
        const { access_token, user: userData } = response.data
        localStorage.setItem('auth_token', access_token)
        setUser(userData)
        navigate('/admin/dashboard')
      } else {
        // Restaurant login (OAuth2 format)
        const formData = new URLSearchParams()
        formData.append('username', email)
        formData.append('password', password)

        const response = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
        const { access_token, user: userData } = response.data
        localStorage.setItem('auth_token', access_token)
        setUser(userData)
        navigate('/restaurant/dashboard')
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const signup = async (data: SignupData) => {
    try {
      const response = await api.post('/auth/signup', data)
      const { access_token, user: userData } = response.data
      localStorage.setItem('auth_token', access_token)
      setUser(userData)
      navigate('/restaurant/dashboard')
    } catch (error: any) {
      console.error('Signup failed:', error)
      throw new Error(error.response?.data?.detail || 'Signup failed')
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
    navigate('/')
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isRestaurant: user?.role === 'restaurant'
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
