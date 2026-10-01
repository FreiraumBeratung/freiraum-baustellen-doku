import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { BigButton, Card, PageTitle, Switch } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { formatDateDe } from '../utils/formatDateDe'

type LeavePerson = {
  employeeId: string
  name: string
  active: boolean
  allowanceSet: boolean
  allowanceDays: number | null
  usedDays: number
  remainingDays: number | null
}

type LeaveBlock = {
  id: string
  employeeId: string
  employeeName: string
  fromDate: string
  toDate: string
  status: string
}

type LeaveOpenRequest = {
  id: string
  employeeId: string
  employeeName: string
  fromDate: string
  toDate: string
  status: string
  weekdayCount: number
  yearDays: number
}

type LeaveOverview = {
  year: number
  selfEmployeeId: string | null
  people: LeavePerson[]
  openRequests?: LeaveOpenRequest[]
  approvedRequests?: LeaveOpenRequest[]
  blocks?: LeaveBlock[]
}

const dateInputClass =
  'mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42 [color-scheme:dark]'

const selectClass =
  'mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42'

function restLine(p: LeavePerson): string {
  if (!p.allowanceSet || p.remainingDays == null || p.allowanceDays == null) {
    return 'Noch nicht gepflegt'
  }
  if (p.allowanceDays === 0) {
    return 'Rest 0 · kein Jahresurlaub'
  }
  return `Rest ${p.remainingDays} von ${p.allowanceDays}`
}

function parseIsoStrict(iso: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || '').trim())
  if (!m) return null
  const y = Number(m[1])
  const mo = Number(m[2]) - 1
  const d = Number(m[3])
  const dt = new Date(y, mo, d, 12, 0, 0, 0)
  if (dt.getFullYear() !== y || dt.getMonth() !== mo || dt.getDate() !== d) return null
  return dt
}

function countWeekdays(fromIso: string, toIso: string, year?: number): number {
  const start = parseIsoStrict(fromIso)
  const end = parseIsoStrict(toIso)
  if (!start || !end || end < start) return 0
  let n = 0
  const cur = new Date(start.getTime())
  let guard = 0
  while (cur <= end && guard < 400) {
    const wd = cur.getDay()
    const isWeekday = wd !== 0 && wd !== 6
    if (isWeekday && (year == null || cur.getFullYear() === year)) n += 1
    cur.setDate(cur.getDate() + 1)
    guard += 1
  }
  return n
}

function rangeLabel(fromDate: string, toDate: string): string {
  const a = formatDateDe(fromDate)
  const b = formatDateDe(toDate)
  if (a && b && a === b) return a
  if (a && b) return `${a}–${b}`
  return a || b
}

function statusLabel(status: string): string {
  if (status === 'approved') return 'Genehmigt'
  if (status === 'rejected') return 'Abgelehnt'
  return 'Offen'
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

  const [reqEmployeeId, setReqEmployeeId] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [reqBusy, setReqBusy] = useState(false)
  const [reqMsg, setReqMsg] = useState('')
  const [immediate, setImmediate] = useState(false)
  const [decideBusy, setDecideBusy] = useState<string | null>(null)
  const [decideMsg, setDecideMsg] = useState<Record<string, string>>({})

  async function load(opts?: { keepDrafts?: boolean }) {
    const r = await api<LeaveOverview>('/api/leave')
    setData(r)
    if (!opts?.keepDrafts) {
      const next: Record<string, string> = {}
      for (const p of r.people || []) {
        next[p.employeeId] = p.allowanceSet && p.allowanceDays != null ? String(p.allowanceDays) : ''
      }
      setDrafts(next)
    }
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
  const openRequests = data?.openRequests ?? []
  const approvedRequests = data?.approvedRequests ?? []
  const blocks = data?.blocks ?? []

  useEffect(() => {
    if (!data) return
    if (isCompanyOwner && !reqEmployeeId && data.people.length) {
      setReqEmployeeId(data.people[0]!.employeeId)
    }
    if (!isCompanyOwner && data.selfEmployeeId) {
      setReqEmployeeId(data.selfEmployeeId)
    }
  }, [isCompanyOwner, data, reqEmployeeId])

  const subtitle = useMemo(() => {
    if (!year) return 'Jahresurlaub pro Mitarbeiter.'
    return `Kalenderjahr ${year} · Jahresurlaub pro Mitarbeiter`
  }, [year])

  const targetPerson = people.find((p) => p.employeeId === reqEmployeeId) || null
  const weekdayCount = fromDate && toDate ? countWeekdays(fromDate, toDate) : 0
  const yearDays = fromDate && toDate && year ? countWeekdays(fromDate, toDate, year) : 0
  const dateOrderOk = Boolean(fromDate && toDate && fromDate <= toDate)
  const overlaps = useMemo(() => {
    if (!fromDate || !toDate || fromDate > toDate) return []
    return blocks.filter((b) => b.fromDate <= toDate && fromDate <= b.toDate)
  }, [blocks, fromDate, toDate])

  const remainingAfter =
    targetPerson?.allowanceSet && targetPerson.remainingDays != null
      ? targetPerson.remainingDays - yearDays
      : null

  const canRequest = isCompanyOwner ? people.length > 0 : Boolean(selfId)

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

  async function submitRequest(e: React.FormEvent) {
    e.preventDefault()
    if (writeBlocked || !canRequest) return
    setReqMsg('')
    if (!fromDate || !toDate) {
      setReqMsg('Bitte Von und Bis wählen.')
      return
    }
    if (fromDate > toDate) {
      setReqMsg('Von muss vor oder gleich Bis liegen.')
      return
    }
    if (weekdayCount <= 0) {
      setReqMsg('Keine Werktage (Mo–Fr) in diesem Zeitraum.')
      return
    }
    setReqBusy(true)
    try {
      await api('/api/leave/requests', {
        method: 'POST',
        body: JSON.stringify({
          employeeId: isCompanyOwner ? reqEmployeeId : selfId,
          fromDate,
          toDate,
          immediate: isCompanyOwner ? immediate : false,
        }),
      })
      setFromDate('')
      setToDate('')
      await load({ keepDrafts: true })
      setReqMsg(
        isCompanyOwner && immediate
          ? 'Eingetragen und genehmigt. Resttage sind angepasst.'
          : 'Antrag ist offen. Resttage ändern sich erst nach der Genehmigung.',
      )
    } catch (ex) {
      setReqMsg(ex instanceof Error ? ex.message : 'Antrag fehlgeschlagen.')
    } finally {
      setReqBusy(false)
    }
  }

  async function decide(id: string, status: 'approved' | 'rejected') {
    if (!isCompanyOwner || writeBlocked) return
    setDecideBusy(id)
    setDecideMsg((m) => ({ ...m, [id]: '' }))
    try {
      await api(`/api/leave/requests/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      })
      await load({ keepDrafts: true })
    } catch (ex) {
      setDecideMsg((m) => ({
        ...m,
        [id]: ex instanceof Error ? ex.message : 'Entscheidung fehlgeschlagen.',
      }))
    } finally {
      setDecideBusy(null)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Urlaub" subtitle={subtitle} />

      {err ? <p className="mb-4 text-center text-sm text-red-400">{err}</p> : null}
      {loading ? <p className="text-center text-zinc-500">Laden…</p> : null}

      {!loading && canRequest ? (
        <Card className="mb-6 border-transparent bg-black/44 py-8 shadow-none ring-1 ring-white/[0.08]">
          <form onSubmit={submitRequest} className="space-y-2.5">
            <p className="text-sm font-medium text-zinc-200">Antrag</p>
            {isCompanyOwner ? (
              <label className="block min-w-0">
                <span className="text-xs tracking-wide text-zinc-400">Mitarbeiter</span>
                <select
                  className={selectClass}
                  value={reqEmployeeId}
                  disabled={writeBlocked || reqBusy}
                  onChange={(e) => setReqEmployeeId(e.target.value)}
                >
                  {people.map((p) => (
                    <option key={p.employeeId} value={p.employeeId}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <div className="grid grid-cols-2 gap-2.5">
              <label className="block min-w-0">
                <span className="text-xs tracking-wide text-zinc-400">Von</span>
                <input
                  type="date"
                  lang="de-DE"
                  className={dateInputClass}
                  value={fromDate}
                  disabled={writeBlocked || reqBusy}
                  onChange={(e) => setFromDate(e.target.value)}
                />
              </label>
              <label className="block min-w-0">
                <span className="text-xs tracking-wide text-zinc-400">Bis</span>
                <input
                  type="date"
                  lang="de-DE"
                  className={dateInputClass}
                  value={toDate}
                  disabled={writeBlocked || reqBusy}
                  onChange={(e) => setToDate(e.target.value)}
                />
              </label>
            </div>
            {fromDate && toDate && dateOrderOk && weekdayCount > 0 ? (
              <p className="text-[0.82rem] leading-snug text-zinc-400">
                {weekdayCount === 1 ? '1 Werktag' : `${weekdayCount} Werktage`}
                {targetPerson?.allowanceSet && remainingAfter != null
                  ? ` · Rest nach Genehmigung ${remainingAfter}`
                  : ' · Jahresurlaub noch nicht gepflegt'}
              </p>
            ) : null}
            {fromDate && toDate && dateOrderOk && weekdayCount === 0 ? (
              <p className="text-[0.82rem] text-zinc-500">Keine Werktage (Mo–Fr) in diesem Zeitraum.</p>
            ) : null}
            {fromDate && toDate && !dateOrderOk ? (
              <p className="text-[0.82rem] text-zinc-500">Von muss vor oder gleich Bis liegen.</p>
            ) : null}
            {overlaps.length > 0 ? (
              <div className="rounded-2xl border border-orange-400/18 bg-orange-500/[0.06] px-3 py-2.5 ring-1 ring-orange-400/10">
                <p className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-orange-300/90">
                  Überschneidung
                </p>
                <ul className="mt-1.5 space-y-1">
                  {overlaps.map((b) => (
                    <li key={`${b.id}-${b.employeeId}-${b.fromDate}`} className="text-[0.8rem] text-zinc-300">
                      {b.employeeName} · {rangeLabel(b.fromDate, b.toDate)} · {statusLabel(b.status)}
                    </li>
                  ))}
                </ul>
                <p className="mt-1.5 text-[0.7rem] text-zinc-500">Nur Hinweis — Antrag bleibt möglich.</p>
              </div>
            ) : null}
            {isCompanyOwner ? (
              <div className="rounded-2xl border border-white/[0.06] bg-black/30 px-3 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <span className="text-sm text-zinc-300">Sofort eintragen</span>
                    <p className="mt-0.5 text-[0.72rem] leading-snug text-zinc-600">
                      An: schon genehmigt, Rest wird abgezogen. Aus: Antrag bleibt offen.
                    </p>
                  </div>
                  <Switch
                    checked={immediate}
                    onChange={setImmediate}
                    disabled={writeBlocked || reqBusy}
                    label="Sofort eintragen"
                  />
                </div>
              </div>
            ) : null}
            {isCompanyOwner && immediate && remainingAfter != null && remainingAfter < 0 ? (
              <p className="text-[0.82rem] text-zinc-500">
                Zu wenig Rest für direktes Eintragen — Antrag senden geht trotzdem.
              </p>
            ) : null}
            <BigButton type="submit" disabled={writeBlocked || reqBusy}>
              {reqBusy ? '…' : isCompanyOwner && immediate ? 'Direkt eintragen' : 'Antrag senden'}
            </BigButton>
            {reqMsg ? <p className="text-center text-[0.78rem] text-zinc-400">{reqMsg}</p> : null}
          </form>
        </Card>
      ) : null}

      {!loading && !isCompanyOwner && !selfId ? (
        <p className="mb-6 text-center text-sm text-zinc-500">
          Urlaub beantragen geht, sobald der Chef euch als Mitarbeiter mit Zugang angelegt hat.
        </p>
      ) : null}

      {!loading && openRequests.length > 0 ? (
        <div className="mb-6 space-y-3">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-zinc-500">Offene Anträge</p>
          {openRequests.map((r) => (
            <Card
              key={r.id}
              className="border-transparent bg-black/38 py-[1.05rem] shadow-none ring-1 ring-white/[0.06]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-[1.02rem] font-semibold text-white">{r.employeeName}</h3>
                <span className="inline-flex items-center rounded-full border border-orange-400/35 bg-orange-500/[0.08] px-2.5 py-[0.22rem] text-[9px] font-semibold uppercase tracking-[0.14em] text-orange-200/90">
                  Offen
                </span>
              </div>
              <p className="mt-1.5 text-sm text-zinc-400">
                {rangeLabel(r.fromDate, r.toDate)}
                <span className="text-zinc-500">
                  {' '}
                  · {r.weekdayCount === 1 ? '1 Werktag' : `${r.weekdayCount} Werktage`}
                </span>
              </p>
              {isCompanyOwner ? (
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    disabled={writeBlocked || decideBusy === r.id}
                    onClick={() => decide(r.id, 'approved')}
                    className="inline-flex flex-1 items-center justify-center rounded-[0.85rem] bg-orange-500/90 py-[0.5rem] text-[0.74rem] font-semibold text-zinc-950 transition hover:bg-orange-400 active:scale-[0.99] disabled:opacity-40"
                  >
                    {decideBusy === r.id ? '…' : 'Genehmigen'}
                  </button>
                  <button
                    type="button"
                    disabled={writeBlocked || decideBusy === r.id}
                    onClick={() => decide(r.id, 'rejected')}
                    className="inline-flex flex-1 items-center justify-center rounded-[0.85rem] bg-black/50 py-[0.5rem] text-[0.74rem] font-semibold text-zinc-300 ring-1 ring-white/[0.08] transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
                  >
                    Ablehnen
                  </button>
                </div>
              ) : null}
              {decideMsg[r.id] ? (
                <p className="mt-2 text-[0.78rem] text-zinc-400">{decideMsg[r.id]}</p>
              ) : null}
            </Card>
          ))}
        </div>
      ) : null}

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

      {!loading && approvedRequests.length > 0 ? (
        <div className="mt-8 space-y-3">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.12em] text-zinc-500">Genehmigt</p>
          {approvedRequests.map((r) => (
            <Card
              key={r.id}
              className="border-transparent bg-black/38 py-[1.05rem] shadow-none ring-1 ring-white/[0.06]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-[1.02rem] font-semibold text-white">{r.employeeName}</h3>
                <span className="inline-flex items-center rounded-full border border-emerald-400/30 bg-emerald-500/[0.08] px-2.5 py-[0.22rem] text-[9px] font-semibold uppercase tracking-[0.14em] text-emerald-200/90">
                  Genehmigt
                </span>
              </div>
              <p className="mt-1.5 text-sm text-zinc-400">
                {rangeLabel(r.fromDate, r.toDate)}
                <span className="text-zinc-500">
                  {' '}
                  · {r.weekdayCount === 1 ? '1 Werktag' : `${r.weekdayCount} Werktage`}
                </span>
              </p>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  )
}
