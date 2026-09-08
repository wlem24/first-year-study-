import { createContext, useContext, useState, useEffect } from 'react'
import { checkAuth as apiCheckAuth, login as apiLogin, logout as apiLogout } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [admin, setAdmin] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verify auth status on mount via httpOnly cookie
    apiCheckAuth()
      .then((data) => {
        setIsAuthenticated(true)
        setAdmin(data)
      })
      .catch(() => {
        setIsAuthenticated(false)
        setAdmin(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    await apiLogin(email, password)
    const data = await apiCheckAuth()
    setIsAuthenticated(true)
    setAdmin(data)
  }

  const logout = async () => {
    await apiLogout()
    setIsAuthenticated(false)
    setAdmin(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, admin, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
