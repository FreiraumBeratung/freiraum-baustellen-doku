import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, resolveBackendPublicUrl } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { tilePermission } from '../utils/accountPermissions'
import { formatDateDe } from '../utils/formatDateDe'
import { addDaysIso, todayIsoLocal } from '../utils/taskWeek'

type CompanyProfile = {
  companyName: string
  logoUrl: string | null
}

type RecurringProject = {
  id: string
  name: string
  customer?: string
  recurringCustomer?: boolean
  recurringNextDate?: string
}

type ProtocolReminderItem = {
  id: string
  title?: string
  date?: string
}

type ProtocolReminder = {
  due?: boolean
  items?: ProtocolReminderItem[]
}

type TodayPerson = {
  id: string
  name: string
}

type TodayPresence = {
  due?: boolean
  missing?: TodayPerson[]
  todos?: {
    openToday?: number
    overdue?: number
  }
  leave?: {
    pending?: number
    name?: string
    fromDate?: string
    toDate?: string
  }
}

type Tile = { to: string; title: string; emoji: string; primary?: boolean; accent?: boolean }

const RECURRING_DUE_DAYS = 14

const allTiles: Tile[] = [
  { to: '/bericht', title: 'Tagesbericht', emoji: '📝', primary: true },
  { to: '/aufgaben', title: 'To-do / Aufgaben', emoji: '✅', accent: true },
  { to: '/protokoll', title: 'Protokoll', emoji: '📄' },
  { to: '/berichte', title: 'Berichte', emoji: '📋' },
  { to: '/stunden', title: 'Stundenkonto', emoji: '⏱️' },
  { to: '/urlaub', title: 'Urlaub', emoji: '☀️' },
  { to: '/baustellen', title: 'Baustellen', emoji: '🏗️' },
  { to: '/mitarbeiter', title: 'Mitarbeiter', emoji: '👷' },
  { to: '/profil', title: 'Firmenprofil', emoji: '⚙️' },
]

export function DashboardPage() {
  const { can, isCompanyOwner, logout } = useAuth()
  const nav = useNavigate()
  const [company, setCompany] = useState<CompanyProfile | null>(null)
  const [todoOpen, setTodoOpen] = useState(false)
  const [recurringDue, setRecurringDue] = useState<RecurringProject[]>([])
  const [protocolReminder, setProtocolReminder] = useState<ProtocolReminderItem[]>([])
  const [todayMissing, setTodayMissing] = useState<TodayPerson[]>([])
  const [todayTodos, setTodayTodos] = useState({ openToday: 0, overdue: 0 })
  const [todayLeave, setTodayLeave] = useState({
    pending: 0,
    name: '',
    fromDate: '',
    toDate: '',
  })

  const tiles = useMemo(
    () =>
      allTiles
        .filter((t) => {
          const need = tilePermission(t.to)
          if (!need) return true
          return can(need)
        })
        .map((t) =>
          t.to === '/aufgaben'
            ? { ...t, title: isCompanyOwner ? 'To-do' : 'Aufgaben' }
            : t,
        ),
    [can, isCompanyOwner],
  )

  const todayTodoCount = todayTodos.openToday + todayTodos.overdue
  const todayLeavePending = todayLeave.pending
  const showHeute = todayMissing.length > 0 || todayTodoCount > 0 || todayLeavePending > 0
  const todayLeaveLabel = (() => {
    if (todayLeavePending <= 0) return ''
    if (todayLeavePending > 1) return `${todayLeavePending} Anträge`
    const from = formatDateDe(todayLeave.fromDate)
    const to = formatDateDe(todayLeave.toDate)
    const span = from && to && from !== to ? `${from} – ${to}` : from || to
    const name = todayLeave.name.trim()
    if (name && span) return `${name} · ${span}`
    return name || span || 'Antrag'
  })()
  const todayTodoLabel =
    todayTodos.openToday > 0 && todayTodos.overdue > 0
      ? `${todayTodos.openToday} offen · ${todayTodos.overdue} überfällig`
      : todayTodos.overdue > 0
        ? `${todayTodos.overdue} überfällig`
        : todayTodos.openToday > 0
          ? `${todayTodos.openToday} offen`
          : ''

  useEffect(() => {
    api<CompanyProfile>('/api/company-profile')
      .then(setCompany)
      .catch(() => setCompany({ companyName: '', logoUrl: null }))
  }, [])

  useEffect(() => {
    if (!can('tasks')) {
      setTodoOpen(false)
      return
    }
    let cancelled = false
    api<{ tasks?: { status?: string }[] }>('/api/tasks?status=open')
      .then((r) => {
        if (cancelled) return
        const list = Array.isArray(r.tasks) ? r.tasks : []
        setTodoOpen(list.length > 0)
      })
      .catch(() => {
        if (!cancelled) setTodoOpen(false)
      })
    return () => {
      cancelled = true
    }
  }, [can])

  useEffect(() => {
    if (!can('projects')) {
      setRecurringDue([])
      return
    }
    let cancelled = false
    const today = todayIsoLocal()
    const horizon = addDaysIso(today, RECURRING_DUE_DAYS)
    api<{ projects?: RecurringProject[] }>('/api/projects')
      .then((r) => {
        if (cancelled) return
        const list = Array.isArray(r.projects) ? r.projects : []
        const due = list
          .filter((p) => {
            if (!p.recurringCustomer) return false
            const d = String(p.recurringNextDate || '').trim()
            if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return false
            return d <= horizon
          })
          .sort((a, b) =>
            String(a.recurringNextDate || '').localeCompare(String(b.recurringNextDate || '')),
          )
        setRecurringDue(due.slice(0, 5))
      })
      .catch(() => {
        if (!cancelled) setRecurringDue([])
      })
    return () => {
      cancelled = true
    }
  }, [can])

  useEffect(() => {
    if (!can('protocol')) {
      setProtocolReminder([])
      return
    }
    let cancelled = false
    api<ProtocolReminder>('/api/reminders/protocol')
      .then((r) => {
        if (cancelled) return
        if (!r?.due) {
          setProtocolReminder([])
          return
        }
        const list = Array.isArray(r.items) ? r.items : []
        setProtocolReminder(
          list.filter((item) => item && typeof item.id === 'string' && item.id).slice(0, 5),
        )
      })
      .catch(() => {
        if (!cancelled) setProtocolReminder([])
      })
    return () => {
      cancelled = true
    }
  }, [can])

  useEffect(() => {
    if (!isCompanyOwner) {
      setTodayMissing([])
      setTodayTodos({ openToday: 0, overdue: 0 })
      setTodayLeave({ pending: 0, name: '', fromDate: '', toDate: '' })
      return
    }
    let cancelled = false
    api<TodayPresence>('/api/reminders/today')
      .then((r) => {
        if (cancelled) return
        const missing = Array.isArray(r?.missing) ? r.missing : []
        const openToday = Math.max(0, Number(r?.todos?.openToday) || 0)
        const overdue = Math.max(0, Number(r?.todos?.overdue) || 0)
        setTodayTodos({ openToday, overdue })
        setTodayLeave({
          pending: Math.max(0, Number(r?.leave?.pending) || 0),
          name: String(r?.leave?.name || '').trim(),
          fromDate: String(r?.leave?.fromDate || '').trim(),
          toDate: String(r?.leave?.toDate || '').trim(),
        })
        if (missing.length === 0) {
          setTodayMissing([])
          return
        }
        setTodayMissing(
          missing
            .filter((p) => p && typeof p.id === 'string' && p.id && String(p.name || '').trim())
            .slice(0, 12),
        )
      })
      .catch(() => {
        if (!cancelled) {
          setTodayMissing([])
          setTodayTodos({ openToday: 0, overdue: 0 })
          setTodayLeave({ pending: 0, name: '', fromDate: '', toDate: '' })
        }
      })
    return () => {
      cancelled = true
    }
  }, [isCompanyOwner])

  return (
    <div className="flex min-h-full flex-col">
      {/* Dominanter Kopf: großes Logo schafft das „meine App"-Gefühl */}
      <header
        className={`relative -mx-4 overflow-hidden rounded-b-[2rem] border-b border-white/[0.05] px-5 pt-10 text-center ${
          showHeute ? 'pb-6' : 'pb-12'
        }`}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_100%_at_50%_-12%,rgba(249,115,22,0.17),transparent_64%)]"
        />
        <div className={`relative flex flex-col items-center ${showHeute ? 'gap-3' : 'gap-5'}`}>
          <p className="text-[0.72rem] font-medium uppercase tracking-[0.3em] text-orange-300/85">
            Freiraum · Baustellen-Doku
          </p>
          {company?.logoUrl ? (
            <div className="dashboard-company-logo flex items-center justify-center">
              <img
                src={resolveBackendPublicUrl(company.logoUrl) ?? company.logoUrl}
                alt="Firmenlogo"
                className={`w-auto object-contain ${
                  showHeute ? 'h-[4.75rem] max-w-[200px]' : 'h-[6.25rem] max-w-[260px]'
                }`}
              />
            </div>
          ) : (
            <div
              aria-hidden
              className={`flex items-center justify-center rounded-[1.6rem] bg-white/[0.05] ring-1 ring-white/[0.08] ${
                showHeute ? 'h-[5.25rem] w-[5.25rem] text-[2.1rem]' : 'h-[7rem] w-[7rem] text-[2.8rem]'
              }`}
            >
              🏢
            </div>
          )}
          <p className="text-[1.55rem] font-semibold tracking-tight text-white/96">
            {company?.companyName?.trim() || 'Ihre Firma'}
          </p>
          {showHeute ? (
            <div className="mt-1 w-full rounded-[1.15rem] border border-white/[0.1] bg-black/45 px-3.5 py-2.5 text-left ring-1 ring-white/[0.04]">
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                Heute
              </p>
              {todayMissing.length > 0 ? (
                <Link
                  to="/berichte"
                  className="mt-1.5 block rounded-lg transition hover:bg-white/[0.03] active:scale-[0.99]"
                >
                  <ul className="space-y-1">
                    {todayMissing.map((p) => (
                      <li
                        key={p.id}
                        className="flex items-baseline justify-between gap-3 text-[0.82rem]"
                      >
                        <span className="min-w-0 truncate text-zinc-100">{p.name}</span>
                        <span className="shrink-0 text-orange-300">fehlt</span>
                      </li>
                    ))}
                  </ul>
                </Link>
              ) : null}
              {todayTodoCount > 0 && todayTodoLabel ? (
                <Link
                  to="/aufgaben"
                  className={`flex items-baseline justify-between gap-3 text-[0.82rem] transition hover:bg-white/[0.03] active:scale-[0.99] ${
                    todayMissing.length > 0 ? 'mt-1.5 border-t border-white/[0.06] pt-1.5' : 'mt-1.5'
                  }`}
                >
                  <span className="min-w-0 truncate text-zinc-100">To-do</span>
                  <span
                    className={`shrink-0 ${
                      todayTodos.overdue > 0 ? 'text-orange-300' : 'text-zinc-400'
                    }`}
                  >
                    {todayTodoLabel}
                  </span>
                </Link>
              ) : null}
              {todayLeavePending > 0 && todayLeaveLabel ? (
                <Link
                  to="/urlaub"
                  className={`flex items-baseline justify-between gap-3 text-[0.82rem] transition hover:bg-white/[0.03] active:scale-[0.99] ${
                    todayMissing.length > 0 || todayTodoCount > 0
                      ? 'mt-1.5 border-t border-white/[0.06] pt-1.5'
                      : 'mt-1.5'
                  }`}
                >
                  <span className="min-w-0 truncate text-zinc-100">Urlaub</span>
                  <span className="min-w-0 shrink truncate text-orange-300">{todayLeaveLabel}</span>
                </Link>
              ) : null}
            </div>
          ) : null}
        </div>
      </header>

      {recurringDue.length > 0 ? (
        <Link
          to="/baustellen"
          className="relative mt-6 block rounded-[1.25rem] border border-orange-400/18 bg-orange-500/[0.06] px-4 py-3 ring-1 ring-orange-400/10 transition hover:bg-orange-500/[0.09] active:scale-[0.99]"
        >
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-orange-300/90">
            Dauerkunde
          </p>
          <ul className="mt-2 space-y-1.5">
            {recurringDue.map((p) => {
              const d = String(p.recurringNextDate || '').trim()
              const overdue = d < todayIsoLocal()
              const today = d === todayIsoLocal()
              return (
                <li
                  key={p.id}
                  className="flex items-baseline justify-between gap-3 text-[0.82rem]"
                >
                  <span className="min-w-0 truncate text-zinc-200">
                    {p.customer?.trim() || p.name}
                  </span>
                  <span
                    className={`shrink-0 tabular-nums ${
                      overdue || today ? 'text-orange-300' : 'text-zinc-500'
                    }`}
                  >
                    {overdue ? 'fällig · ' : today ? 'heute · ' : ''}
                    {formatDateDe(d)}
                  </span>
                </li>
              )
            })}
          </ul>
        </Link>
      ) : null}

      {protocolReminder.length > 0 ? (
        <Link
          to="/protokolle"
          className="relative mt-6 block rounded-[1.25rem] border border-orange-400/18 bg-orange-500/[0.06] px-4 py-3 ring-1 ring-orange-400/10 transition hover:bg-orange-500/[0.09] active:scale-[0.99]"
        >
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-orange-300/90">
            Protokoll
          </p>
          <p className="mt-1 text-[0.78rem] text-zinc-400">Noch nicht ans Büro gesendet</p>
          <ul className="mt-2 space-y-1.5">
            {protocolReminder.map((item) => (
              <li
                key={item.id}
                className="flex items-baseline justify-between gap-3 text-[0.82rem]"
              >
                <span className="min-w-0 truncate text-zinc-200">
                  {item.title?.trim() || 'Protokoll'}
                </span>
                {item.date ? (
                  <span className="shrink-0 tabular-nums text-zinc-500">{formatDateDe(item.date)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </Link>
      ) : null}

      {/* 3 × 3 Kacheln — ans untere Ende geschoben */}
      <nav aria-label="Schnellzugriff" className="mt-auto grid grid-cols-3 gap-2.5 pb-1 pt-8">
        {tiles.map((t, i) => (
          <Link
            key={t.to}
            to={t.to}
            className={`group relative flex aspect-square flex-col items-center justify-center gap-2.5 rounded-[1.25rem] px-1.5 text-center outline-none ring-offset-2 ring-offset-zinc-950 transition focus-visible:ring-2 focus-visible:ring-orange-400/40 active:scale-[0.98] ${
              tiles.length % 3 === 1 && i === tiles.length - 1 ? 'col-start-2' : ''
            } ${
              t.primary
                ? 'border border-orange-400/35 bg-[linear-gradient(155deg,rgba(249,115,22,0.16),rgba(249,115,22,0.04)_60%)] ring-1 ring-orange-400/20'
                : t.accent
                  ? 'border border-orange-400/22 bg-[linear-gradient(155deg,rgba(249,115,22,0.10),rgba(24,24,27,0.55)_62%)] ring-1 ring-orange-400/12 hover:bg-orange-500/[0.08]'
                  : 'border border-white/[0.09] bg-[linear-gradient(180deg,rgba(255,255,255,0.045),rgba(24,24,27,0.55))] ring-1 ring-white/[0.05] hover:bg-white/[0.06]'
            } ${t.accent && todoOpen ? 'freiraum-todo-breathe' : ''}`}
          >
            <span
              className={`flex h-[3rem] w-[3rem] items-center justify-center rounded-[1rem] text-[1.45rem] ring-1 transition ${
                t.primary
                  ? 'bg-black/40 ring-orange-300/25'
                  : t.accent
                    ? 'bg-black/40 ring-orange-300/20'
                    : 'bg-black/45 ring-white/[0.08] group-hover:ring-white/[0.14]'
              }`}
            >
              {t.emoji}
            </span>
            <span
              className={`text-[0.8rem] font-medium leading-tight tracking-tight ${
                t.primary ? 'text-orange-100/95' : t.accent ? 'text-orange-100/88' : 'text-zinc-300'
              }`}
            >
              {t.title}
            </span>
          </Link>
        ))}
      </nav>

      {/* Mitarbeiter ohne Profil-Reiter: dezentes Abmelden (Chef bleibt über Profil) */}
      {!isCompanyOwner ? (
        <div className="mt-5 flex justify-center pb-1">
          <button
            type="button"
            className="min-h-[2.5rem] px-3 text-[0.8rem] font-medium tracking-wide text-zinc-500 transition hover:text-zinc-300"
            onClick={() => {
              logout()
              nav('/login', { replace: true })
            }}
          >
            Abmelden
          </button>
        </div>
      ) : null}
    </div>
  )
}
