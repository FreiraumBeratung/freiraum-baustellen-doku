import { ChevronRight, FileText, Lightbulb } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  listProtocols,
  api,
  THOUGHTS_PROJECT_ID,
  THOUGHTS_PROJECT_NAME,
  type SiteProtocol,
} from '../api/client'
import { Card, PageTitle } from '../components/ui'

type Project = { id: string; name: string }

type ProtocolGroup = {
  projectId: string
  projectName: string
  signed: SiteProtocol[]
  quick: SiteProtocol[]
  thoughts: SiteProtocol[]
  latestDate: string
  isThoughts: boolean
}

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

function seqRange(signed: SiteProtocol[]): string {
  const nums = signed.map((p) => p.sequenceNumber).filter((n): n is number => typeof n === 'number' && n > 0)
  if (!nums.length) return ''
  const lo = Math.min(...nums)
  const hi = Math.max(...nums)
  return lo === hi ? `Nr. ${lo}` : `Nr. ${lo}–${hi}`
}

function groupProtocols(protocols: SiteProtocol[]): ProtocolGroup[] {
  const map = new Map<string, ProtocolGroup>()
  for (const p of protocols) {
    const isThoughts = p.mode === 'thoughts' || p.projectId === THOUGHTS_PROJECT_ID
    const pid = isThoughts ? THOUGHTS_PROJECT_ID : p.projectId || 'unknown'
    let g = map.get(pid)
    if (!g) {
      g = {
        projectId: pid,
        projectName: isThoughts ? THOUGHTS_PROJECT_NAME : p.projectName || 'Baustelle',
        signed: [],
        quick: [],
        thoughts: [],
        latestDate: '',
        isThoughts,
      }
      map.set(pid, g)
    }
    if (p.mode === 'signed') g.signed.push(p)
    else if (p.mode === 'thoughts' || isThoughts) g.thoughts.push(p)
    else g.quick.push(p)
    if (p.date && p.date > g.latestDate) g.latestDate = p.date
  }
  for (const g of map.values()) {
    g.signed.sort((a, b) => (a.sequenceNumber || 0) - (b.sequenceNumber || 0))
    g.quick.sort((a, b) => b.date.localeCompare(a.date))
    g.thoughts.sort((a, b) => b.date.localeCompare(a.date) || b.createdAt.localeCompare(a.createdAt))
  }
  return Array.from(map.values()).sort((a, b) => {
    if (a.isThoughts !== b.isThoughts) return a.isThoughts ? -1 : 1
    return b.latestDate.localeCompare(a.latestDate)
  })
}

export function ProtocolsListPage() {
  const [protocols, setProtocols] = useState<SiteProtocol[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [projFilter, setProjFilter] = useState('')
  const [month, setMonth] = useState('')

  const query = useMemo(
    () => ({
      projectId: projFilter || undefined,
      month: month || undefined,
    }),
    [projFilter, month],
  )

  const load = useCallback(async () => {
    const r = await listProtocols(query)
    setProtocols(r.protocols)
  }, [query])

  useEffect(() => {
    api<{ projects: Project[] }>('/api/projects').then((r) => setProjects(r.projects))
  }, [])

  useEffect(() => {
    load().catch(() => {})
  }, [load])

  const groups = useMemo(() => groupProtocols(protocols), [protocols])
  const hasThoughts = useMemo(
    () => protocols.some((p) => p.mode === 'thoughts' || p.projectId === THOUGHTS_PROJECT_ID),
    [protocols],
  )

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Protokolle" subtitle="Nach Baustelle · Begehungen gebündelt" />

      <div className="mb-5 space-y-3.5">
        <label className="block">
          <span className="text-sm text-zinc-400">Baustelle</span>
          <select
            className="mt-1 w-full min-w-0 rounded-2xl border border-white/[0.09] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/35"
            value={projFilter}
            onChange={(e) => setProjFilter(e.target.value)}
          >
            <option value="">Alle</option>
            {hasThoughts || projFilter === THOUGHTS_PROJECT_ID ? (
              <option value={THOUGHTS_PROJECT_ID}>{THOUGHTS_PROJECT_NAME}</option>
            ) : null}
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

      <div className="space-y-4">
        {groups.map((g) => {
          const range = seqRange(g.signed)
          const visitLabel =
            g.signed.length === 1 ? '1 Begehung' : `${g.signed.length} Begehungen`
          const quickLabel =
            g.quick.length === 1 ? '1 Schnellnotiz' : `${g.quick.length} Schnellnotizen`
          const thoughtsLabel =
            g.thoughts.length === 1 ? '1 Eintrag' : `${g.thoughts.length} Einträge`

          return (
            <Card
              key={g.projectId}
              className="overflow-hidden border-transparent bg-[linear-gradient(168deg,rgba(255,255,255,0.045)_0%,transparent_56%)] px-6 py-6 shadow-none ring-1 ring-white/[0.07]"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="text-[1.1rem] font-semibold tracking-tight text-white">{g.projectName}</h3>
                  <p className="mt-2 text-sm text-zinc-500">
                    {g.isThoughts
                      ? 'Ohne Baustellenbezug'
                      : g.latestDate
                        ? `Zuletzt: ${formatDateDe(g.latestDate)}`
                        : 'Kein Datum'}
                  </p>
                </div>
                {g.isThoughts ? (
                  <Lightbulb className="h-5 w-5 shrink-0 text-orange-400/80" aria-hidden />
                ) : (
                  <FileText className="h-5 w-5 shrink-0 text-orange-400/80" aria-hidden />
                )}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {g.signed.length ? (
                  <span className="rounded-full bg-orange-500/15 px-3 py-1 text-xs font-semibold text-orange-300 ring-1 ring-orange-400/25">
                    {visitLabel}
                    {range ? ` (${range})` : ''}
                  </span>
                ) : null}
                {g.quick.length ? (
                  <span className="rounded-full bg-black/40 px-3 py-1 text-xs font-medium text-zinc-400 ring-1 ring-white/[0.08]">
                    {quickLabel}
                  </span>
                ) : null}
                {g.thoughts.length ? (
                  <span className="rounded-full bg-orange-500/10 px-3 py-1 text-xs font-medium text-orange-200/90 ring-1 ring-orange-400/20">
                    {thoughtsLabel}
                  </span>
                ) : null}
              </div>

              <Link
                to={`/protokolle/baustelle/${encodeURIComponent(g.projectId)}`}
                className="mt-5 flex h-11 items-center justify-between rounded-2xl bg-white/[0.08] px-4 text-sm font-semibold text-white ring-1 ring-white/[0.12] transition hover:bg-white/[0.12] active:scale-[0.99]"
              >
                <span>
                  {g.isThoughts
                    ? 'Gedankensammlung öffnen'
                    : g.signed.length
                      ? 'Begehungen & Gesamtprotokoll'
                      : 'Protokolle anzeigen'}
                </span>
                <ChevronRight className="h-4 w-4 text-zinc-500" aria-hidden />
              </Link>
            </Card>
          )
        })}
        {groups.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">Keine Protokolle für den gewählten Filter.</p>
        ) : null}
      </div>

      {!groups.length ? (
        <div className="mt-8 rounded-2xl border border-dashed border-zinc-800 p-6 text-center text-sm text-zinc-500">
          Gespeicherte Protokolle erscheinen hier automatisch nach dem Speichern.
        </div>
      ) : null}
    </div>
  )
}
