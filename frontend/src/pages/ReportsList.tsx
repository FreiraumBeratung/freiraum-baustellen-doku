import { FileText, Pencil, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { buildReportPreviewStateFromDoc, type ReportDocForEdit } from '../utils/reportEditState'
import { formatDateDe } from '../utils/formatDateDe'
import { formatBaustelleLabel } from '../utils/siteSpot'

type ReportRow = {
  id: string
  date: string
  projectName: string
  employees: string[]
  exportFormat: string
  structured: { summary?: string }
  projectId: string
  siteSpot?: string
}

type Project = { id: string; name: string }

export function ReportsListPage() {
  const nav = useNavigate()
  const { writeBlocked } = useWriteBlocked()
  const [reports, setReports] = useState<ReportRow[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [projFilter, setProjFilter] = useState('')
  const [month, setMonth] = useState('')
  const [msg, setMsg] = useState('')
  const [editBusyId, setEditBusyId] = useState<string | null>(null)

  const query = useMemo(() => {
    const p = new URLSearchParams()
    if (projFilter) p.set('projectId', projFilter)
    if (month && month.length === 7) p.set('month', `${month}-01`)
    const qs = p.toString()
    return qs ? `?${qs}` : ''
  }, [projFilter, month])

  const load = useCallback(async () => {
    const r = await api<{ reports: ReportRow[] }>(`/api/reports${query}`)
    setReports(r.reports)
  }, [query])

  useEffect(() => {
    api<{ projects: Project[] }>('/api/projects').then((r) => setProjects(r.projects))
  }, [])

  useEffect(() => {
    load().catch(() => {})
  }, [load])

  async function confirmDelete(rep: ReportRow) {
    setMsg('')
    if (writeBlocked) return
    const ok = window.confirm('Bericht wirklich löschen?')
    if (!ok) return
    try {
      await api<{ ok?: boolean }>(`/api/reports/${encodeURIComponent(rep.id)}`, { method: 'DELETE' })
      setMsg('Bericht gelöscht.')
      window.setTimeout(() => setMsg(''), 4000)
      await load()
    } catch {
      setMsg('Bericht konnte nicht gelöscht werden.')
      window.setTimeout(() => setMsg(''), 6000)
    }
  }

  async function openEdit(rep: ReportRow) {
    setMsg('')
    if (writeBlocked) return
    setEditBusyId(rep.id)
    try {
      const doc = await api<ReportDocForEdit>(`/api/reports/${encodeURIComponent(rep.id)}`)
      nav('/bericht/vorschau', { state: buildReportPreviewStateFromDoc(doc) })
    } catch {
      setMsg('Bericht konnte nicht zum Bearbeiten geladen werden.')
      window.setTimeout(() => setMsg(''), 6000)
    } finally {
      setEditBusyId(null)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Berichte" subtitle="Chronologie · gefiltert nach Projekt oder Monat" />

      <div className="mb-5 space-y-3.5">
        <label className="block">
          <span className="text-sm text-zinc-400">Baustelle</span>
          <select
            className="mt-1 w-full min-w-0 rounded-2xl border border-white/[0.09] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/35"
            value={projFilter}
            onChange={(e) => setProjFilter(e.target.value)}
          >
            <option value="">Alle</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm text-zinc-400">
            Monat <span className="font-normal text-zinc-600">optional</span>
          </span>
          <input
            type="month"
            className="mt-1 w-full min-w-0 rounded-2xl border border-white/[0.09] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/35"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
          />
          {month ? (
            <button
              type="button"
              className="mt-2 text-sm font-medium text-orange-400 hover:underline"
              onClick={() => setMonth('')}
            >
              Alle Monate anzeigen
            </button>
          ) : null}
        </label>
      </div>

      {msg ? (
        <p className={`mb-3 text-sm ${msg.includes('Konnte nicht') ? 'text-red-400' : 'text-orange-300'}`}>{msg}</p>
      ) : null}

      <div className="space-y-3">
        {reports.map((rep) => {
          const hasSummary = Boolean(rep.structured?.summary?.trim())

          return (
            <Card
              key={rep.id}
              className="border-white/[0.08] bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(24,24,27,0.5))] px-5 py-4 shadow-none ring-1 ring-white/[0.05]"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <h3 className="text-[1.05rem] font-semibold tracking-tight text-white">
                    {formatBaustelleLabel(rep.projectName, rep.siteSpot)}
                  </h3>
                  <p className="mt-1 truncate text-sm text-zinc-400">
                    {formatDateDe(rep.date)}
                    {rep.employees.length ? ` · ${rep.employees.join(', ')}` : ''}
                  </p>
                </div>
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-orange-500/[0.14] px-2.5 py-[0.28rem] ring-1 ring-orange-400/30">
                  <FileText className="h-3.5 w-3.5 text-orange-400" aria-hidden />
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-orange-300">
                    {rep.exportFormat}
                  </span>
                </span>
              </div>
              {hasSummary ? (
                <p className="mt-2 line-clamp-1 text-sm leading-snug text-zinc-500">{rep.structured.summary}</p>
              ) : null}

              <div className="mt-4 grid grid-cols-3 gap-2">
                <Link
                  to={`/berichte/${rep.id}`}
                  className="inline-flex h-11 items-center justify-center rounded-2xl bg-white/[0.08] text-[0.82rem] font-semibold text-white ring-1 ring-white/[0.12] transition hover:bg-white/[0.12] focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/55 active:scale-[0.98]"
                >
                  Öffnen
                </Link>
                <button
                  type="button"
                  disabled={writeBlocked || editBusyId === rep.id}
                  onClick={() => void openEdit(rep)}
                  className="inline-flex h-11 cursor-pointer items-center justify-center gap-1.5 rounded-2xl border border-orange-500/30 bg-orange-500/[0.12] text-[0.82rem] font-semibold text-orange-300 transition hover:bg-orange-500/[0.18] focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/55 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Pencil strokeWidth={2} className="h-3.5 w-3.5 shrink-0" aria-hidden />
                  {editBusyId === rep.id ? '…' : 'Bearbeiten'}
                </button>
                <button
                  type="button"
                  disabled={writeBlocked || editBusyId === rep.id}
                  onClick={() => void confirmDelete(rep)}
                  className="inline-flex h-11 cursor-pointer items-center justify-center gap-1.5 rounded-xl border border-red-500/28 bg-red-950/35 text-[0.82rem] font-semibold text-red-300 transition hover:bg-red-950/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500/55 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Trash2 strokeWidth={2} className="h-3.5 w-3.5 shrink-0" aria-hidden /> Löschen
                </button>
              </div>
            </Card>
          )
        })}
        {reports.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">Keine Berichte für den gewählten Filter.</p>
        ) : null}
      </div>

      {!reports.length && projects.length === 0 ? (
        <div className="mt-8 rounded-2xl border border-dashed border-zinc-800 p-6 text-center text-sm text-zinc-500">
          Sobald erste Berichte geschrieben sind, erscheinen sie automatisch hier.
        </div>
      ) : null}
    </div>
  )
}
