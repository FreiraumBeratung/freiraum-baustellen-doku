import {
  ClipboardList,
  HardHat,
  Home,
  Mic,
  User,
} from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { LicenseSuspendedBanner } from './LicenseSuspendedBanner'

const nav = [
  { to: '/', label: 'Home', Icon: Home, end: true },
  { to: '/bericht', label: 'Bericht', Icon: Mic, end: false },
  { to: '/berichte', label: 'Berichte', Icon: ClipboardList, end: false },
  { to: '/baustellen', label: 'Baustellen', Icon: HardHat, end: false },
  { to: '/profil', label: 'Profil', Icon: User, end: false },
] as const

export function AppShell() {
  return (
    <div className="flex min-h-dvh flex-col overflow-x-hidden pb-[calc(6.5rem+env(safe-area-inset-bottom,0px))]">
      <main className="safe-area-pt-min mx-auto flex w-full max-w-[390px] flex-1 flex-col overflow-x-hidden px-4 pb-6 pt-[max(1.25rem,env(safe-area-inset-top,0px)+0.35rem)]">
        <LicenseSuspendedBanner />
        <Outlet />
      </main>
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 border-t border-zinc-800/90 bg-zinc-950/90 backdrop-blur-lg"
        aria-label="Hauptnavigation"
      >
        <div className="safe-area-pb mx-auto flex max-w-[390px] justify-between gap-2 px-3 py-3">
          {nav.map((item) => {
            const Icon = item.Icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex min-h-[3.2rem] min-w-[3.05rem] flex-1 flex-col items-center justify-center gap-1 rounded-[1.1rem] text-[10px] font-medium tracking-[0.02em] transition-[color,background-color,box-shadow] duration-200 ${
                    isActive
                      ? 'border border-orange-500/38 bg-orange-500/[0.08] text-orange-300 shadow-[0_0_22px_-10px_rgba(249,115,22,0.42)]'
                      : 'border border-transparent text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300'
                  }`
                }
              >
                <Icon strokeWidth={1.85} className="h-[1.28rem] w-[1.28rem]" aria-hidden />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
