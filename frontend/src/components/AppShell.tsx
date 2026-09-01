import { Home, MessageSquareText, Mic, User } from 'lucide-react'
import { useMemo } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LicenseSuspendedBanner } from './LicenseSuspendedBanner'
import { isTabletDevice } from '../utils/isTabletDevice'

const navItems = [
  { to: '/', label: 'Home', Icon: Home, end: true, ownerOnly: false },
  { to: '/bericht', label: 'Bericht', Icon: Mic, end: false, ownerOnly: false },
  { to: '/feedback', label: 'Feedback', Icon: MessageSquareText, end: false, ownerOnly: false },
  { to: '/profil', label: 'Profil', Icon: User, end: false, ownerOnly: true },
] as const

export function AppShell() {
  const { isCompanyOwner } = useAuth()
  // Nur echte Tablets breiter — Handys bleiben bei 390px (auch Querformat).
  const shellMax = useMemo(() => (isTabletDevice() ? 'max-w-[720px]' : 'max-w-[390px]'), [])
  const visibleNav = useMemo(
    () => navItems.filter((item) => (item.ownerOnly ? isCompanyOwner : true)),
    [isCompanyOwner],
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
        <div className={`safe-area-pb mx-auto flex ${shellMax} justify-between gap-1 px-2 py-3`}>
          {visibleNav.map((item) => {
            const Icon = item.Icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex min-h-[3.2rem] flex-1 flex-col items-center justify-center gap-1 rounded-[1.1rem] border text-[11px] font-medium tracking-[0.02em] transition-[color,background-color,box-shadow] duration-200 min-w-[3.05rem] ${
                    isActive
                      ? 'border-orange-500/38 bg-orange-500/[0.08] text-orange-300 shadow-[0_0_22px_-10px_rgba(249,115,22,0.42)]'
                      : 'border-transparent text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300'
                  }`
                }
              >
                <Icon strokeWidth={1.85} className="h-[1.2rem] w-[1.2rem]" aria-hidden />
                <span className="max-w-full truncate">{item.label}</span>
              </NavLink>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
