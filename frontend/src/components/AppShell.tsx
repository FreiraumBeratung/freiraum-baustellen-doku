import { CheckSquare, Home, MessageSquareText, Mic, User } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { LicenseSuspendedBanner } from './LicenseSuspendedBanner'
import { isTabletDevice } from '../utils/isTabletDevice'

export function AppShell() {
  const { isCompanyOwner, token } = useAuth()
  const location = useLocation()
  // Nur echte Tablets breiter — Handys bleiben bei 390px (auch Querformat).
  const shellMax = useMemo(() => (isTabletDevice() ? 'max-w-[720px]' : 'max-w-[390px]'), [])
  const [openTaskCount, setOpenTaskCount] = useState(0)

  const refreshBadge = useCallback(() => {
    if (!token) {
      setOpenTaskCount(0)
      return
    }
    api<{ openCount: number; doneUnseenCount?: number }>('/api/tasks/badge')
      .then((r) => {
        const n = isCompanyOwner
          ? Number(r.doneUnseenCount) || 0
          : Number(r.openCount) || 0
        setOpenTaskCount(Math.max(0, n))
      })
      .catch(() => setOpenTaskCount(0))
  }, [token, isCompanyOwner])

  useEffect(() => {
    refreshBadge()
    const id = window.setInterval(refreshBadge, 30000)
    return () => window.clearInterval(id)
  }, [refreshBadge])

  useEffect(() => {
    refreshBadge()
  }, [location.pathname, refreshBadge])

  useEffect(() => {
    const onChange = () => refreshBadge()
    window.addEventListener('freiraum-tasks-changed', onChange)
    return () => window.removeEventListener('freiraum-tasks-changed', onChange)
  }, [refreshBadge])

  const navItems = useMemo(
    () =>
      [
        { to: '/', label: 'Home', Icon: Home, end: true, ownerOnly: false, badge: 0 },
        { to: '/bericht', label: 'Bericht', Icon: Mic, end: false, ownerOnly: false, badge: 0 },
        {
          to: '/aufgaben',
          label: isCompanyOwner ? 'To-do' : 'Aufgaben',
          Icon: CheckSquare,
          end: false,
          ownerOnly: false,
          badge: openTaskCount,
        },
        { to: '/feedback', label: 'Feedback', Icon: MessageSquareText, end: false, ownerOnly: false, badge: 0 },
        { to: '/profil', label: 'Profil', Icon: User, end: false, ownerOnly: true, badge: 0 },
      ] as const,
    [isCompanyOwner, openTaskCount],
  )

  const visibleNav = useMemo(
    () => navItems.filter((item) => (item.ownerOnly ? isCompanyOwner : true)),
    [isCompanyOwner, navItems],
  )

  return (
    <div className="flex min-h-dvh flex-col overflow-x-hidden pb-[calc(6.5rem+env(safe-area-inset-bottom,0px))]">
      <main
        className={`safe-area-pt-min mx-auto flex w-full ${shellMax} flex-1 flex-col overflow-x-hidden px-4 pb-6 pt-[max(1.25rem,env(safe-area-inset-top,0px)+0.35rem)]`}
      >
        <LicenseSuspendedBanner />
        <Outlet />
      </main>
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 border-t border-zinc-800/90 bg-zinc-950/90 backdrop-blur-lg"
        aria-label="Hauptnavigation"
      >
        <div className={`safe-area-pb mx-auto flex ${shellMax} justify-between gap-0.5 px-1.5 py-3`}>
          {visibleNav.map((item) => {
            const Icon = item.Icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `relative flex min-h-[3.2rem] flex-1 flex-col items-center justify-center gap-1 rounded-[1.1rem] border text-[10px] font-medium tracking-[0.02em] transition-[color,background-color,box-shadow] duration-200 min-w-[2.85rem] ${
                    isActive
                      ? 'border-orange-500/38 bg-orange-500/[0.08] text-orange-300 shadow-[0_0_22px_-10px_rgba(249,115,22,0.42)]'
                      : 'border-transparent text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300'
                  }`
                }
              >
                <span className="relative">
                  <Icon strokeWidth={1.85} className="h-[1.15rem] w-[1.15rem]" aria-hidden />
                  {item.badge > 0 ? (
                    <span className="absolute -right-2.5 -top-1.5 flex h-[1.05rem] min-w-[1.05rem] items-center justify-center rounded-full bg-orange-500 px-1 text-[0.62rem] font-bold leading-none text-zinc-950">
                      {item.badge > 9 ? '9+' : item.badge}
                    </span>
                  ) : null}
                </span>
                <span className="max-w-full truncate">{item.label}</span>
              </NavLink>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
