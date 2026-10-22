import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import authService from '../services/authService'
import type { LoginRequest, RegisterRequest, UserInfo } from '../types'

interface AuthContextValue {
  loading: boolean
  enabled: boolean
  registrationEnabled: boolean
  user: UserInfo | null
  login: (payload: LoginRequest) => Promise<void>
  register: (payload: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
}

const noop = async () => undefined

const AuthContext = createContext<AuthContextValue>({
  loading: false,
  enabled: false,
  registrationEnabled: false,
  user: null,
  login: noop,
  register: noop,
  logout: noop,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [enabled, setEnabled] = useState(false)
  const [registrationEnabled, setRegistrationEnabled] = useState(false)
  const [user, setUser] = useState<UserInfo | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const mode = await authService.mode()
        if (cancelled) return
        setEnabled(mode.auth_enabled)
        setRegistrationEnabled(mode.allow_registration)
        try {
          const current = await authService.me()
          if (!cancelled) setUser(current)
        } catch {
          if (!cancelled) setUser(null)
        }
      } catch {
        if (!cancelled) {
          setEnabled(false)
          setRegistrationEnabled(false)
          setUser(null)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (payload: LoginRequest) => {
    const response = await authService.login(payload)
    setUser(response.user)
  }, [])

  const register = useCallback(async (payload: RegisterRequest) => {
    const response = await authService.register(payload)
    setUser(response.user)
  }, [])

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(
    () => ({ loading, enabled, registrationEnabled, user, login, register, logout }),
    [loading, enabled, registrationEnabled, user, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}

export default AuthProvider
