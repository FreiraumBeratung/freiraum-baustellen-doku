import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, clearToken, getToken, postAuthLogin, setToken } from '../api/client'

type AuthState = {
  token: string | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  register: (p: {
    companyName: string
    entrepreneurName: string
    email: string
    password: string
  }) => Promise<void>
  logout: () => void
}

const AuthCtx = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTok] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setTok(getToken())
    setReady(true)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const normalizedEmail = email.trim().toLowerCase()
    const r = await postAuthLogin(normalizedEmail, password)
    setToken(r.access_token)
    setTok(r.access_token)
  }, [])

  const register = useCallback(
    async (p: {
      companyName: string
      entrepreneurName: string
      email: string
      password: string
    }) => {
      const r = await api<{ access_token: string }>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          ...p,
          email: p.email.trim().toLowerCase(),
        }),
      })
      setToken(r.access_token)
      setTok(r.access_token)
    },
    [],
  )

  const logout = useCallback(() => {
    clearToken()
    setTok(null)
  }, [])

  const val = useMemo(
    () => ({ token, ready, login, register, logout }),
    [token, ready, login, register, logout],
  )

  return <AuthCtx.Provider value={val}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  const c = useContext(AuthCtx)
  if (!c) throw new Error('useAuth outside AuthProvider')
  return c
}

export function useRequireAuth() {
  const { token, ready } = useAuth()
  return { token, ready, authed: Boolean(token) }
}
