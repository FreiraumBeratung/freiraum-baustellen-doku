import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { type CompanyProfileResponse, isCompanyProfileComplete } from '../utils/companyProfile'

function ProfileGateInner() {
  const location = useLocation()
  const [profile, setProfile] = useState<CompanyProfileResponse | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    api<CompanyProfileResponse>('/api/company-profile')
      .then((p) => {
        if (!cancelled) setProfile(p)
      })
      .catch(() => {
        if (!cancelled) setProfile(null)
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (!ready) {
    return (
      <div className="flex min-h-dvh items-start justify-center overflow-x-hidden pt-24 text-zinc-400">
        Laden…
      </div>
    )
  }

  const complete = isCompanyProfileComplete(profile)

  if (!complete && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />
  }
  if (complete && location.pathname === '/onboarding') {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}

export function ProfileGate() {
  const { pathname } = useLocation()
  return <ProfileGateInner key={pathname} />
}
