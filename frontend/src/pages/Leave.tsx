import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { Card, PageTitle } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type LeavePerson = {
  employeeId: string
  name: string
  active: boolean
  allowanceSet: boolean
  allowanceDays: number | null
  usedDays: number
  remainingDays: number | null
}

type LeaveOverview = {
  year: number
  selfEmployeeId: string | null
  people: LeavePerson[]
}

function restLine(p: LeavePerson): string {
  if (!p.allowanceSet || p.remainingDays == null || p.allowanceDays == null) {
    return 'Noch nicht gepflegt'
  }
  if (p.allowanceDays === 0) {
    return 'Rest 0 · kein Jahresurlaub'
  }
  return `Rest ${p.remainingDays} von ${p.allowanceDays}`
}

export function LeavePage() {
  const { isCompanyOwner } = useAuth()
  const { writeBlocked } = useWriteBlocked()
  const [data, setData] = useState<LeaveOverview | null>(null)
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [busyId, setBusyId] = useState<string | null>(null)
  const [msg, setMsg] = useState<Record<string, string>>({})
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    const r = await api<LeaveOverview>('/api/leave')
    setData(r)
    const next: Record<string, string> = {}
    for (const p of r.people || []) {
      next[p.employeeId] = p.allowanceSet && p.allowanceDays != null ? String(p.allowanceDays) : ''
    }
    setDrafts(next)
  }

  useEffect(() => {
    setLoading(true)
    setErr('')
    load()
      .catch(() => setErr('Urlaubstage konnten nicht geladen werden.'))
      .finally(() => setLoading(false))
  }, [])

  const people = data?.people ?? []
  const year = data?.year
  const selfId = data?.selfEmployeeId

  const subtitle = useMemo(() => {
    if (!year) return 'Jahresurlaub pro Mitarbeiter.'
    return `Kalenderjahr ${year} · Jahresurlaub pro Mitarbeiter`
  }, [year])

  async function save(p: LeavePerson) {
    if (!isCompanyOwner || writeBlocked) return
    setBusyId(p.employeeId)
    setMsg((m) => ({ ...m, [p.employeeId]: '' }))
    const raw = (drafts[p.employeeId] ?? '').trim()
    if (raw !== '' && !/^\d{1,2}$/.test(raw)) {
      setBusyId(null)
      setMsg((m) => ({ ...m, [p.employeeId]: 'Nur ganze Tage, 0–99.' }))
      return
    }
    const days = raw === '' ? null : Number(raw)
    try {
      await api(`/api/leave/employees/${encodeURIComponent(p.employeeId)}`, {
        method: 'PATCH',
        body: JSON.stringify({ days }),
      })
      await load()
      setMsg((m) => ({ ...m, [p.employeeId]: 'Gespeichert.' }))
    } catch (ex) {
      setMsg((m) => ({
        ...m,
        [p.employeeId]: ex instanceof Error ? ex.message : 'Speichern fehlgeschlagen.',
      }))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Urlaub" subtitle={subtitle} />

      {err ? <p className="mb-4 text-center text-sm text-red-400">{err}</p> : null}
      {loading ? <p className="text-center text-zinc-500">Laden…</p> : null}

      {!loading && people.length === 0 ? (
        <Card>
          <p className="text-center text-sm leading-relaxed text-zinc-500">
            Noch keine Mitarbeiter. Legen Sie Personen unter Mitarbeiter an — hier trägt der Chef
            danach die Urlaubstage ein.
          </p>
        </Card>
      ) : null}

      <div className="space-y-3">
        {people.map((p) => {
          const mine = Boolean(selfId && p.employeeId === selfId)
          const rest = restLine(p)
          return (
            <Card
              key={p.employeeId}
              className={`border-transparent bg-black/38 py-[1.15rem] shadow-none ring-1 backdrop-blur-sm ${
                mine ? 'ring-orange-400/25' : 'ring-white/[0.06]'
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-[1.05rem] font-semibold text-white">{p.name}</h3>
                {!p.active ? (
                  <span className="inline-flex items-center rounded-full border border-zinc-600/75 bg-zinc-800/90 px-2.5 py-[0.22rem] text-[9px] font-semibold uppercase tracking-[0.14em] text-zinc-400">
                    Inaktiv
                  </span>
                ) : null}
              </div>
              <p
                className={`mt-1.5 text-sm ${
                  p.allowanceSet ? 'font-medium text-orange-200/90' : 'text-zinc-500'
                }`}
              >
                {rest}
              </p>

              {isCompanyOwner ? (
                <div className="mt-3 flex items-end gap-2">
                  <label className="min-w-0 flex-1">
                    <span className="text-xs tracking-wide text-zinc-400">Tage im Jahr</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      autoComplete="off"
                      className="mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42 disabled:opacity-50"
                      value={drafts[p.employeeId] ?? ''}
                      placeholder="z. B. 30"
                      disabled={writeBlocked || busyId === p.employeeId}
                      onChange={(e) =>
                        setDrafts((d) => ({ ...d, [p.employeeId]: e.target.value }))
                      }
                    />
                  </label>
                  <button
                    type="button"
                    disabled={writeBlocked || busyId === p.employeeId}
                    onClick={() => save(p)}
                    className="mb-[1px] inline-flex h-[2.7rem] shrink-0 items-center justify-center rounded-[0.9rem] bg-orange-500/90 px-3.5 text-[0.76rem] font-semibold text-zinc-950 transition hover:bg-orange-400 active:scale-[0.99] disabled:opacity-40"
                  >
                    {busyId === p.employeeId ? '…' : 'Speichern'}
                  </button>
                </div>
              ) : null}
              {msg[p.employeeId] ? (
                <p className="mt-2 text-[0.78rem] text-zinc-400">{msg[p.employeeId]}</p>
              ) : null}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
