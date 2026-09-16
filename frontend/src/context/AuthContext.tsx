import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  api,
  clearToken,
  fetchAuthSession,
  getAccountRole,
  getIsAdmin,
  getLicenseActive,
  getPermissions,
  getTenantId,
  getToken,
  postAuthLogin,
  setAccountRole,
  setIsAdmin,
  setLicenseActive,
  setPermissions,
  setTenantId,
  setToken,
} from '../api/client'
import { LICENSE_REACTIVATED_EVENT, LICENSE_SUSPENDED_EVENT } from '../constants/license'
import {
  hasAppPermission,
  isOwnerRole,
  type AccountRole,
  type AppPermission,
} from '../utils/accountPermissions'

type AuthState = {
  token: string | null
  licenseActive: boolean
  isAdmin: boolean
  accountRole: AccountRole
  permissions: string[]
  tenantId: string
  ready: boolean
  can: (permission: AppPermission) => boolean
  isCompanyOwner: boolean
  login: (emailOrUsername: string, password: string) => Promise<void>
  register: (p: {
    companyName: string
    entrepreneurName: string
    email: string
    password: string
  }) => Promise<void>
  logout: () => void
}

const AuthCtx = createContext<AuthState | null>(null)

function applySessionFields(r: {
  licenseActive?: boolean
  isAdmin?: boolean
  accountRole?: string
  permissions?: string[]
  tenantId?: string
}) {
  const active = r.licenseActive !== false
  setLicenseActive(active)
  setIsAdmin(r.isAdmin === true)
  setAccountRole(r.accountRole)
  setPermissions(r.permissions)
  if (typeof r.tenantId === 'string' && r.tenantId.trim()) {
    setTenantId(r.tenantId)
  }
  return {
    active,
    admin: r.isAdmin === true,
    role: (r.accountRole === 'worker' ? 'worker' : 'owner') as AccountRole,
    perms: Array.isArray(r.permissions) ? r.permissions.map(String) : [],
    tenantId: (typeof r.tenantId === 'string' && r.tenantId.trim() ? r.tenantId.trim() : getTenantId()),
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTok] = useState<string | null>(null)
  const [licenseActive, setLicenseActiveState] = useState(true)
  const [isAdmin, setIsAdminState] = useState(false)
  const [accountRole, setAccountRoleState] = useState<AccountRole>('owner')
  const [permissions, setPermissionsState] = useState<string[]>([])
  const [tenantId, setTenantIdState] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setTok(getToken())
    setLicenseActiveState(getLicenseActive())
    setIsAdminState(getIsAdmin())
    setAccountRoleState(getAccountRole())
    setPermissionsState(getPermissions())
    setTenantIdState(getTenantId())
    setReady(true)

    const onSuspended = () => setLicenseActiveState(false)
    const onReactivated = () => {
      setLicenseActiveState(true)
      setIsAdminState(getIsAdmin())
      setAccountRoleState(getAccountRole())
      setPermissionsState(getPermissions())
      setTenantIdState(getTenantId())
    }
    window.addEventListener(LICENSE_SUSPENDED_EVENT, onSuspended)
    window.addEventListener(LICENSE_REACTIVATED_EVENT, onReactivated)

    if (getToken()) {
      void fetchAuthSession().then((session) => {
        if (!session) return
        const applied = applySessionFields(session)
        setLicenseActiveState(applied.active)
        setIsAdminState(applied.admin)
        setAccountRoleState(applied.role)
        setPermissionsState(applied.perms)
        setTenantIdState(applied.tenantId)
      })
    }

    const onFocus = () => {
      if (!getToken()) return
      void fetchAuthSession().then((session) => {
        if (!session) return
        const applied = applySessionFields(session)
        setLicenseActiveState(applied.active)
        setIsAdminState(applied.admin)
        setAccountRoleState(applied.role)
        setPermissionsState(applied.perms)
        setTenantIdState(applied.tenantId)
      })
    }
    window.addEventListener('focus', onFocus)

    return () => {
      window.removeEventListener(LICENSE_SUSPENDED_EVENT, onSuspended)
      window.removeEventListener(LICENSE_REACTIVATED_EVENT, onReactivated)
      window.removeEventListener('focus', onFocus)
    }
  }, [])

  const login = useCallback(async (emailOrUsername: string, password: string) => {
    const identity = emailOrUsername.trim()
    const normalized = identity.includes('@') ? identity.toLowerCase() : identity.toLowerCase()
    const r = await postAuthLogin(normalized, password)
    setToken(r.access_token)
    setTok(r.access_token)
    const applied = applySessionFields(r)
    setLicenseActiveState(applied.active)
    setIsAdminState(applied.admin)
    setAccountRoleState(applied.role)
    setPermissionsState(applied.perms)
    setTenantIdState(applied.tenantId)
  }, [])

  const register = useCallback(
    async (p: {
      companyName: string
      entrepreneurName: string
      email: string
      password: string
    }) => {
      const r = await api<{
        access_token: string
        licenseActive?: boolean
        isAdmin?: boolean
        accountRole?: string
        permissions?: string[]
        tenantId?: string
      }>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          ...p,
          email: p.email.trim().toLowerCase(),
        }),
      })
      setToken(r.access_token)
      setTok(r.access_token)
      const applied = applySessionFields(r)
      setLicenseActiveState(applied.active)
      setIsAdminState(applied.admin)
      setAccountRoleState(applied.role)
      setPermissionsState(applied.perms)
      setTenantIdState(applied.tenantId)
    },
    [],
  )

  const logout = useCallback(() => {
    clearToken()
    setTok(null)
    setLicenseActiveState(true)
    setIsAdminState(false)
    setAccountRoleState('owner')
    setPermissionsState([])
    setTenantIdState('')
  }, [])

  const can = useCallback(
    (permission: AppPermission) => hasAppPermission(accountRole, permissions, permission),
    [accountRole, permissions],
  )

  const isCompanyOwner = isOwnerRole(accountRole)

  const val = useMemo(
    () => ({
      token,
      licenseActive,
      isAdmin,
      accountRole,
      permissions,
      tenantId,
      ready,
      can,
      isCompanyOwner,
      login,
      register,
      logout,
    }),
    [
      token,
      licenseActive,
      isAdmin,
      accountRole,
      permissions,
      tenantId,
      ready,
      can,
      isCompanyOwner,
      login,
      register,
      logout,
    ],
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
