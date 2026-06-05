import { ChevronDown, ChevronRight, Download, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, downloadExport } from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type TimeAccount = {
  employeeId: string
  employeeName: string
  active: boolean
  hoursBalanceStart: number
  hoursBalanceStartDate: string | null
  bookedHoursTotal: number
  currentBalance: number
  weekHours: number
  monthHours: number
  entryCount: number
}

type TimeEntry = {
  id: string
  source: 'report' | 'manual'
  reportId: string | null
  employeeId: string
  employeeName: string
  date: string
  projectName: string
  startTime: string
  endTime: string
  breakMinutes: number
  hours: number
  note: string
}

function currentMonthValue(): string {
  return new Date().toISOString().slice(0, 7)
}

function fmtHours(h: number): string {
  return `${h.toLocaleString('de-DE', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} h`
}

function fmtDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!m) return iso
  return `${m[3]}.${m[2]}.${m[1]}`
}

function balanceTone(balance: number): string {
  if (balance > 0) return 'text-emerald-400'
  if (balance < 0) return 'text-amber-400'
  return 'text-zinc-300'
}

function parseHoursInput(raw: string): number | null {
  const s = raw.trim().replace(',', '.').replace(/−/g, '-')
  if (!s) return 0
  const n = Number(s)
  if (!Number.isFinite(n)) return null
  return Math.round(n * 100) / 100
}

function hoursToInput(h: number): string {
  if (h === 0) return ''
  return String(h).replace('.', ',')
}

function hasStartBalance(acct: TimeAccount): boolean {
  return acct.hoursBalanceStart !== 0 || Boolean(acct.hoursBalanceStartDate)
}

type StartBalanceDraft = { hours: string; date: string }

function StartBalanceEditor({
  acct,
  onSaved,
  onCancel,
}: {
  acct: TimeAccount
  onSaved: () => void
  onCancel?: () => void
}) {
  const { writeBlocked } = useWriteBlocked()
  const [draft, setDraft] = useState<StartBalanceDraft>(() => ({
    hours: hoursToInput(acct.hoursBalanceStart),
    date: acct.hoursBalanceStartDate ?? '',
  }))
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  useEffect(() => {
    setDraft({
      hours: hoursToInput(acct.hoursBalanceStart),
      date: acct.hoursBalanceStartDate ?? '',
    })
    setMsg('')
    setErr('')
  }, [acct.employeeId, acct.hoursBalanceStart, acct.hoursBalanceStartDate])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (writeBlocked) return
    setMsg('')
    setErr('')
    const hours = parseHoursInput(draft.hours)
    if (hours === null) {
      setErr('Bitte gültige Stundenzahl eingeben (z. B. 12,5 oder -4).')
      return
    }
    if (hours !== 0 && !draft.date) {
      setErr('Bitte „Stand zum Datum“ angeben, wenn der Startsaldo nicht 0 ist.')
      return
    }
    setBusy(true)
    try {
      await api(`/api/employees/${encodeURIComponent(acct.employeeId)}`, {
        method: 'PATCH',
        body: JSON.stringify({
          hoursBalanceStart: hours,
          hoursBalanceStartDate: hours !== 0 ? draft.date : '',
        }),
      })
      setMsg('Startsaldo gespeichert.')
      onSaved()
      onCancel?.()
    } catch {
      setErr('Startsaldo konnte nicht gespeichert werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      className="mb-4 rounded-xl border border-orange-500/20 bg-orange-500/[0.04] p-4"
      onSubmit={save}
      onClick={(e) => e.stopPropagation()}
    >
      <p className="text-sm font-medium text-white">Startsaldo übernehmen</p>
      <p className="mt-1 text-xs leading-relaxed text-zinc-500">
        Bestehendes Stundenkonto beim Einstieg — z. B. +12,5 h Überstunden oder −4 h Minusstunden.
      </p>
      <div className="mt-3 grid gap-3">
        <label className="block min-w-0">
          <span className="text-xs text-zinc-400">Stunden</span>
          <input
            type="text"
            inputMode="text"
            autoComplete="off"
            className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
            placeholder="0 oder z. B. 12,5 oder -4"
            value={draft.hours}
            onChange={(ev) => setDraft((d) => ({ ...d, hours: ev.target.value }))}
          />
        </label>
        <label className="block min-w-0">
          <span className="text-xs text-zinc-400">Stand zum Datum</span>
          <input
            type="date"
            className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
            value={draft.date}
            onChange={(ev) => setDraft((d) => ({ ...d, date: ev.target.value }))}
          />
        </label>
      </div>
      {err ? <p className="mt-2 text-xs text-red-400">{err}</p> : null}
      {msg ? <p className="mt-2 text-xs text-emerald-400">{msg}</p> : null}
      <div className="mt-3 flex flex-col gap-2">
        <BigButton type="submit" className="min-h-11 text-sm" disabled={busy || writeBlocked}>
          {busy ? 'Speichern…' : 'Startsaldo speichern'}
        </BigButton>
        {onCancel ? (
          <button
            type="button"
            className="text-sm text-zinc-500 hover:text-zinc-300"
            onClick={onCancel}
          >
            Abbrechen
          </button>
        ) : null}
      </div>
    </form>
  )
}

function StartBalanceSection({ acct, onSaved }: { acct: TimeAccount; onSaved: () => void }) {
  const [editing, setEditing] = useState(() => !hasStartBalance(acct))

  useEffect(() => {
    if (!hasStartBalance(acct)) setEditing(true)
  }, [acct.employeeId, acct.hoursBalanceStart, acct.hoursBalanceStartDate])

  if (!editing && hasStartBalance(acct)) {
    return (
      <div className="mb-4 rounded-xl border border-white/[0.06] bg-black/25 px-4 py-3">
        <p className="text-sm text-zinc-300">
          Startsaldo {fmtHours(acct.hoursBalanceStart)}
          {acct.hoursBalanceStartDate ? ` · Stand ${fmtDate(acct.hoursBalanceStartDate)}` : ''}
        </p>
        <button
          type="button"
          className="mt-2 text-xs font-medium text-orange-400 hover:underline"
          onClick={() => setEditing(true)}
        >
          Startsaldo bearbeiten
        </button>
      </div>
    )
  }

  return (
    <StartBalanceEditor
      acct={acct}
      onSaved={onSaved}
      onCancel={() => setEditing(false)}
    />
  )
}

type CorrectionDraft = { hours: string; date: string; note: string }

function ManualCorrectionForm({
  acct,
  onSaved,
}: {
  acct: TimeAccount
  onSaved: () => void
}) {
  const { writeBlocked } = useWriteBlocked()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<CorrectionDraft>({ hours: '', date: '', note: '' })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (writeBlocked) return
    setErr('')
    const hours = parseHoursInput(draft.hours)
    if (hours === null || hours === 0) {
      setErr('Bitte Stunden angeben (z. B. -1 oder 0,5).')
      return
    }
    if (!draft.date) {
      setErr('Bitte Datum wählen.')
      return
    }
    if (draft.note.trim().length < 2) {
      setErr('Bitte kurzen Grund angeben.')
      return
    }
    setBusy(true)
    try {
      await api('/api/time-entries', {
        method: 'POST',
        body: JSON.stringify({
          employeeId: acct.employeeId,
          date: draft.date,
          hours,
          note: draft.note.trim(),
        }),
      })
      setDraft({ hours: '', date: '', note: '' })
      setOpen(false)
      onSaved()
    } catch {
      setErr('Korrektur konnte nicht gespeichert werden.')
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        disabled={writeBlocked}
        className="mb-4 w-full rounded-xl border border-dashed border-zinc-700 py-2.5 text-sm text-zinc-400 hover:border-orange-500/40 hover:text-orange-300 disabled:opacity-40"
        onClick={(e) => {
          e.stopPropagation()
          setOpen(true)
        }}
      >
        + Manuelle Korrektur
      </button>
    )
  }

  return (
    <form
      className="mb-4 rounded-xl border border-zinc-700/80 bg-black/35 p-4"
      onSubmit={submit}
      onClick={(e) => e.stopPropagation()}
    >
      <p className="text-sm font-medium text-white">Manuelle Korrektur</p>
      <p className="mt-1 text-xs text-zinc-500">z. B. −1 h bei früherem Feierabend</p>
      <div className="mt-3 grid gap-3">
        <label className="block min-w-0">
          <span className="text-xs text-zinc-400">Stunden (+/−)</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {(['-1', '-0,5', '0,5', '1'] as const).map((preset) => (
              <button
                key={preset}
                type="button"
                className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-200 hover:border-orange-500/40 hover:text-orange-200"
                onClick={() => setDraft((d) => ({ ...d, hours: preset }))}
              >
                {preset} h
              </button>
            ))}
          </div>
          <input
            type="text"
            inputMode="text"
            autoComplete="off"
            className="mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
            placeholder="z. B. -1 (Minus über ABC-Tastatur)"
            value={draft.hours}
            onChange={(ev) => setDraft((d) => ({ ...d, hours: ev.target.value }))}
          />
        </label>
        <label className="block min-w-0">
          <span className="text-xs text-zinc-400">Datum</span>
          <input
            type="date"
            className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
            value={draft.date}
            onChange={(ev) => setDraft((d) => ({ ...d, date: ev.target.value }))}
          />
        </label>
        <label className="block min-w-0">
          <span className="text-xs text-zinc-400">Grund</span>
          <input
            type="text"
            className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
            placeholder="Früher Feierabend"
            value={draft.note}
            onChange={(ev) => setDraft((d) => ({ ...d, note: ev.target.value }))}
          />
        </label>
      </div>
      {err ? <p className="mt-2 text-xs text-red-400">{err}</p> : null}
      <div className="mt-3 flex flex-col gap-2">
        <BigButton type="submit" className="min-h-11 text-sm" disabled={busy || writeBlocked}>
          {busy ? 'Speichern…' : 'Korrektur buchen'}
        </BigButton>
        <button
          type="button"
          className="text-sm text-zinc-500 hover:text-zinc-300"
          onClick={() => setOpen(false)}
        >
          Abbrechen
        </button>
      </div>
    </form>
  )
}

function TimeEntryRow({
  entry,
  onDelete,
}: {
  entry: TimeEntry
  onDelete: () => void
}) {
  const { writeBlocked } = useWriteBlocked()
  const [busy, setBusy] = useState(false)
  const isReport = entry.source === 'report' && entry.reportId

  async function remove() {
    if (writeBlocked) return
    const msg = isReport
      ? 'Buchung aus Tagesbericht entfernen? Der Bericht behält die ursprüngliche Arbeitszeit.'
      : 'Korrektur wirklich entfernen?'
    if (!window.confirm(msg)) return
    setBusy(true)
    try {
      await api(`/api/time-entries/${encodeURIComponent(entry.id)}`, { method: 'DELETE' })
      onDelete()
    } catch {
      window.alert('Buchung konnte nicht entfernt werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className="rounded-xl border border-white/[0.06] bg-black/35 px-3 py-2.5 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-white">{fmtDate(entry.date)}</span>
            <span
              className={`rounded-md px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                entry.source === 'manual'
                  ? 'bg-amber-500/15 text-amber-300'
                  : 'bg-zinc-800 text-zinc-500'
              }`}
            >
              {entry.source === 'manual' ? 'Korrektur' : 'Bericht'}
            </span>
          </div>
          <p className={`mt-1 ${entry.hours < 0 ? 'text-amber-300/90' : 'text-orange-300/90'}`}>
            {fmtHours(entry.hours)}
          </p>
          <p className="mt-1 text-zinc-400">{entry.projectName || 'Baustelle'}</p>
          {entry.note ? <p className="mt-1 text-xs text-zinc-500">{entry.note}</p> : null}
          {entry.startTime && entry.endTime ? (
            <p className="mt-0.5 text-xs text-zinc-600">
              {entry.startTime}–{entry.endTime}
              {entry.breakMinutes ? ` · Pause ${entry.breakMinutes} Min.` : null}
            </p>
          ) : null}
          {entry.reportId ? (
            <Link
              to={`/berichte/${encodeURIComponent(entry.reportId)}`}
              className="mt-2 inline-block text-xs font-medium text-orange-400 hover:underline"
            >
              Zum Bericht
            </Link>
          ) : null}
        </div>
        <button
          type="button"
          className="shrink-0 rounded-lg border border-zinc-700 p-2 text-zinc-500 hover:border-red-500/40 hover:text-red-400 disabled:opacity-40"
          aria-label="Buchung entfernen"
          disabled={busy || writeBlocked}
          onClick={remove}
        >
          <Trash2 className="h-4 w-4" aria-hidden />
        </button>
      </div>
    </li>
  )
}

export function TimeAccountsPage() {
  const [month, setMonth] = useState(currentMonthValue)
  const [accounts, setAccounts] = useState<TimeAccount[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [entriesByEmployee, setEntriesByEmployee] = useState<Record<string, TimeEntry[]>>({})
  const [entriesLoading, setEntriesLoading] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [exportBusy, setExportBusy] = useState<'xlsx' | 'csv' | false>(false)
  const [exportMsg, setExportMsg] = useState('')
  const [err, setErr] = useState('')

  const monthQuery = month && month.length === 7 ? `?month=${encodeURIComponent(month)}` : ''

  const loadAccounts = useCallback(async () => {
    setLoading(true)
    setErr('')
    try {
      const r = await api<{ accounts: TimeAccount[]; month: string }>(`/api/time-accounts${monthQuery}`)
      setAccounts(r.accounts ?? [])
    } catch {
      setErr('Stundenkonten konnten nicht geladen werden.')
      setAccounts([])
    } finally {
      setLoading(false)
    }
  }, [monthQuery])

  useEffect(() => {
    loadAccounts().catch(() => {})
  }, [loadAccounts])

  const reloadEmployeeData = useCallback(
    async (empId: string) => {
      await loadAccounts()
      const qs = new URLSearchParams({ employeeId: empId })
      if (month && month.length === 7) qs.set('month', month)
      try {
        const r = await api<{ entries: TimeEntry[] }>(`/api/time-entries?${qs.toString()}`)
        setEntriesByEmployee((prev) => ({ ...prev, [empId]: r.entries ?? [] }))
      } catch {
        setEntriesByEmployee((prev) => ({ ...prev, [empId]: [] }))
      }
    },
    [loadAccounts, month],
  )

  async function toggleEmployee(empId: string) {
    if (expandedId === empId) {
      setExpandedId(null)
      return
    }
    setExpandedId(empId)
    if (entriesByEmployee[empId]) return

    setEntriesLoading(empId)
    try {
      const qs = new URLSearchParams({ employeeId: empId })
      if (month && month.length === 7) qs.set('month', month)
      const r = await api<{ entries: TimeEntry[] }>(`/api/time-entries?${qs.toString()}`)
      setEntriesByEmployee((prev) => ({ ...prev, [empId]: r.entries ?? [] }))
    } catch {
      setEntriesByEmployee((prev) => ({ ...prev, [empId]: [] }))
    } finally {
      setEntriesLoading(null)
    }
  }

  useEffect(() => {
    setEntriesByEmployee({})
    setExpandedId(null)
  }, [month])

  const activeAccounts = accounts.filter((a) => a.active || a.entryCount > 0 || a.hoursBalanceStart !== 0)

  async function exportFile(kind: 'xlsx' | 'csv') {
    if (!month || month.length !== 7) return
    setExportBusy(kind)
    setExportMsg('')
    try {
      await downloadExport(`/api/time-accounts/export/${kind}?month=${encodeURIComponent(month)}`)
      setExportMsg(
        kind === 'xlsx'
          ? 'Excel exportiert — Datei öffnet sich direkt in Excel.'
          : 'CSV exportiert — für ERP-Import geeignet.',
      )
      window.setTimeout(() => setExportMsg(''), 5000)
    } catch {
      setExportMsg('Export fehlgeschlagen.')
      window.setTimeout(() => setExportMsg(''), 6000)
    } finally {
      setExportBusy(false)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle
        title="Stundenkonto"
        subtitle="Saldo und Buchungen aus Tagesberichten — automatisch beim Speichern"
      />

      <label className="mb-3 block">
        <span className="text-sm text-zinc-400">Monat</span>
        <input
          type="month"
          className="mt-1 w-full min-w-0 rounded-2xl border border-white/[0.09] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/35"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
        />
      </label>

      <div className="mb-2 grid grid-cols-2 gap-2">
        <button
          type="button"
          disabled={Boolean(exportBusy) || !month}
          className="flex min-h-12 items-center justify-center gap-2 rounded-2xl border border-orange-500/35 bg-orange-500/[0.08] text-sm font-semibold text-orange-200 transition hover:bg-orange-500/[0.14] disabled:opacity-40"
          onClick={() => exportFile('xlsx')}
        >
          <Download className="h-4 w-4 shrink-0" aria-hidden />
          {exportBusy === 'xlsx' ? '…' : 'Excel'}
        </button>
        <button
          type="button"
          disabled={Boolean(exportBusy) || !month}
          className="flex min-h-12 items-center justify-center gap-2 rounded-2xl border border-zinc-700 bg-zinc-900/60 text-sm font-semibold text-zinc-200 transition hover:bg-zinc-800 disabled:opacity-40"
          onClick={() => exportFile('csv')}
        >
          <Download className="h-4 w-4 shrink-0" aria-hidden />
          {exportBusy === 'csv' ? '…' : 'CSV'}
        </button>
      </div>
      <p className="mb-5 text-center text-xs text-zinc-600">
        Excel für Büro &amp; Buchhaltung · CSV für ERP-Import
      </p>
      {exportMsg ? <p className="mb-4 text-center text-sm text-emerald-400/90">{exportMsg}</p> : null}

      {err ? <p className="mb-4 text-center text-sm text-red-400">{err}</p> : null}
      {loading ? <p className="text-center text-zinc-500">Laden…</p> : null}

      {!loading && activeAccounts.length === 0 ? (
        <Card>
          <p className="text-center text-sm leading-relaxed text-zinc-500">
            Noch keine Stunden gebucht. Speichern Sie einen Tagesbericht mit Mitarbeitern und Arbeitszeit — die
            Buchung erfolgt automatisch.
          </p>
        </Card>
      ) : null}

      <div className="space-y-3">
        {activeAccounts.map((acct) => {
          const open = expandedId === acct.employeeId
          const entries = entriesByEmployee[acct.employeeId] ?? []
          const busy = entriesLoading === acct.employeeId

          return (
            <Card key={acct.employeeId} className="p-0 overflow-hidden">
              <button
                type="button"
                className="flex w-full items-start gap-3 px-5 py-4 text-left transition hover:bg-white/[0.03]"
                onClick={() => toggleEmployee(acct.employeeId)}
                aria-expanded={open}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                    <span className="font-semibold text-white">{acct.employeeName || 'Unbenannt'}</span>
                    {!acct.active ? <span className="text-xs text-zinc-600">inaktiv</span> : null}
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                    <div>
                      <span className="text-zinc-500">Saldo </span>
                      <span className={`font-medium ${balanceTone(acct.currentBalance)}`}>
                        {fmtHours(acct.currentBalance)}
                      </span>
                    </div>
                    <div>
                      <span className="text-zinc-500">Monat </span>
                      <span className="text-zinc-200">{fmtHours(acct.monthHours)}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500">Woche </span>
                      <span className="text-zinc-200">{fmtHours(acct.weekHours)}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500">Buchungen </span>
                      <span className="text-zinc-200">{acct.entryCount}</span>
                    </div>
                  </div>
                  {acct.hoursBalanceStart !== 0 || acct.hoursBalanceStartDate ? (
                    <p className="mt-2 text-xs text-zinc-600">
                      Startsaldo {fmtHours(acct.hoursBalanceStart)}
                      {acct.hoursBalanceStartDate ? ` · Stand ${fmtDate(acct.hoursBalanceStartDate)}` : ''}
                      {' · '}gebucht {fmtHours(acct.bookedHoursTotal)}
                    </p>
                  ) : null}
                </div>
                {open ? (
                  <ChevronDown className="mt-1 h-5 w-5 shrink-0 text-zinc-500" aria-hidden />
                ) : (
                  <ChevronRight className="mt-1 h-5 w-5 shrink-0 text-zinc-500" aria-hidden />
                )}
              </button>

              {open ? (
                <div className="border-t border-white/[0.06] px-5 py-4">
                  <StartBalanceSection acct={acct} onSaved={() => loadAccounts()} />
                  <ManualCorrectionForm acct={acct} onSaved={() => reloadEmployeeData(acct.employeeId)} />
                  <p className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-600">Buchungen</p>
                  {busy ? <p className="text-sm text-zinc-500">Buchungen laden…</p> : null}
                  {!busy && entries.length === 0 ? (
                    <p className="text-sm text-zinc-500">Keine Buchungen in diesem Zeitraum.</p>
                  ) : null}
                  <ul className="space-y-2">
                    {entries.map((entry) => (
                      <TimeEntryRow
                        key={entry.id}
                        entry={entry}
                        onDelete={() => reloadEmployeeData(acct.employeeId)}
                      />
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
