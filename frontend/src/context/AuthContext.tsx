import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  api,
  clearToken,
  fetchAuthSession,
  getIsAdmin,
  getLicenseActive,
  getToken,
  postAuthLogin,
  setIsAdmin,
  setLicenseActive,
  setToken,
} from '../api/client'
import { LICENSE_REACTIVATED_EVENT, LICENSE_SUSPENDED_EVENT } from '../constants/license'

type AuthState = {
  token: string | null
  licenseActive: boolean
  isAdmin: boolean
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
  const [licenseActive, setLicenseActiveState] = useState(true)
  const [isAdmin, setIsAdminState] = useState(false)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setTok(getToken())
    setLicenseActiveState(getLicenseActive())
    setIsAdminState(getIsAdmin())
    setReady(true)

    const onSuspended = () => setLicenseActiveState(false)
    const onReactivated = () => {
      setLicenseActiveState(true)
      setIsAdminState(getIsAdmin())
    }
    window.addEventListener(LICENSE_SUSPENDED_EVENT, onSuspended)
    window.addEventListener(LICENSE_REACTIVATED_EVENT, onReactivated)

    if (getToken()) {
      void fetchAuthSession().then((session) => {
        if (!session) return
        setLicenseActiveState(session.licenseActive !== false)
        setIsAdminState(session.isAdmin === true)
      })
    }

    const onFocus = () => {
      if (!getToken()) return
      void fetchAuthSession().then((session) => {
        if (!session) return
        setLicenseActiveState(session.licenseActive !== false)
        setIsAdminState(session.isAdmin === true)
      })
    }
    window.addEventListener('focus', onFocus)

    return () => {
      window.removeEventListener(LICENSE_SUSPENDED_EVENT, onSuspended)
      window.removeEventListener(LICENSE_REACTIVATED_EVENT, onReactivated)
      window.removeEventListener('focus', onFocus)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const normalizedEmail = email.trim().toLowerCase()
    const r = await postAuthLogin(normalizedEmail, password)
    setToken(r.access_token)
    setTok(r.access_token)
    const active = r.licenseActive !== false
    setLicenseActive(active)
    setLicenseActiveState(active)
    const admin = r.isAdmin === true
    setIsAdmin(admin)
    setIsAdminState(admin)
  }, [])

  const register = useCallback(
    async (p: {
      companyName: string
      entrepreneurName: string
      email: string
      password: string
    }) => {
      const r = await api<{ access_token: string; licenseActive?: boolean; isAdmin?: boolean }>(
        '/api/auth/register',
        {
          method: 'POST',
          body: JSON.stringify({
            ...p,
            email: p.email.trim().toLowerCase(),
          }),
        },
      )
      setToken(r.access_token)
      setTok(r.access_token)
      const active = r.licenseActive !== false
      setLicenseActive(active)
      setLicenseActiveState(active)
      const admin = r.isAdmin === true
      setIsAdmin(admin)
      setIsAdminState(admin)
    },
    [],
  )

  const logout = useCallback(() => {
    clearToken()
    setTok(null)
    setLicenseActiveState(true)
    setIsAdminState(false)
  }, [])

  const val = useMemo(
    () => ({ token, licenseActive, isAdmin, ready, login, register, logout }),
    [token, licenseActive, isAdmin, ready, login, register, logout],
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
