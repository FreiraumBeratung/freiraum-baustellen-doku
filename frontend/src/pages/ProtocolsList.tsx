import { FileText, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteProtocol, listProtocols, api, type ProtocolMode, type SiteProtocol } from '../api/client'
import { Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type Project = { id: string; name: string }

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

function modeLabel(mode: ProtocolMode, seq: number | null): string {
  if (mode === 'signed' && seq) return `Begehung Nr. ${seq}`
  if (mode === 'signed') return 'Mit Unterschrift'
  return 'Schnellnotiz'
}

function previewText(p: SiteProtocol): string {
  return (p.polishedText || p.rawText || '').trim()
}

export function ProtocolsListPage() {
  const { writeBlocked } = useWriteBlocked()
  const [protocols, setProtocols] = useState<SiteProtocol[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [projFilter, setProjFilter] = useState('')
  const [month, setMonth] = useState('')
  const [msg, setMsg] = useState('')

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

  async function confirmDelete(p: SiteProtocol) {
    setMsg('')
    if (writeBlocked) return
    const ok = window.confirm('Protokoll wirklich löschen?')
    if (!ok) return
    try {
      await deleteProtocol(p.id)
      setMsg('Protokoll gelöscht.')
      window.setTimeout(() => setMsg(''), 4000)
      await load()
    } catch {
      setMsg('Protokoll konnte nicht gelöscht werden.')
      window.setTimeout(() => setMsg(''), 6000)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Protokolle" subtitle="Chronologie · gefiltert nach Projekt oder Monat" />

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

      <div className="space-y-5">
        {protocols.map((p) => {
          const text = previewText(p)
          return (
            <Card
              key={p.id}
              className="relative overflow-hidden border-transparent bg-[linear-gradient(168deg,rgba(255,255,255,0.045)_0%,transparent_56%)] px-7 py-10 shadow-none ring-1 ring-white/[0.07]"
            >
              <div className="absolute right-5 top-5 flex shrink-0 items-center gap-1 rounded-full bg-orange-500/[0.17] px-2.5 py-[0.4rem] ring-1 ring-orange-400/[0.34]">
                <FileText className="h-3.5 w-3.5 text-orange-400" aria-hidden />
                <span className="text-xs font-semibold text-orange-400">{modeLabel(p.mode, p.sequenceNumber)}</span>
              </div>

              <div className="pr-[5.25rem]">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500">
                  Datum <span className="text-orange-400/95">{formatDateDe(p.date)}</span>
                </p>
                <h3 className="mt-3 text-[1.12rem] font-semibold tracking-tight text-white">{p.projectName}</h3>
                {p.participants ? (
                  <p className="mt-2 text-sm">
                    <span className="text-zinc-500">Teilnehmer</span>{' '}
                    <span className="font-medium text-zinc-300">{p.participants}</span>
                  </p>
                ) : null}
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-black/42 px-[0.7rem] py-[0.28rem] text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500 ring-1 ring-white/[0.07]">
                    Protokoll gespeichert
                  </span>
                </div>
                <div className="mt-3 min-h-[2.375rem]">
                  {text ? (
                    <p className="line-clamp-2 text-sm leading-snug text-zinc-400">{text}</p>
                  ) : (
                    <p className="text-[0.78rem] leading-relaxed text-zinc-600">Kein Text vorhanden</p>
                  )}
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3">
                <Link
                  to={`/protokolle/${p.id}`}
                  className="inline-flex h-11 items-center justify-center rounded-2xl bg-white/[0.08] text-[0.9rem] font-semibold text-white ring-1 ring-white/[0.12] transition hover:bg-white/[0.12] focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/55 active:scale-[0.98]"
                >
                  Öffnen
                </Link>
                <button
                  type="button"
                  disabled={writeBlocked}
                  onClick={() => void confirmDelete(p)}
                  className="inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-xl border border-red-500/28 bg-red-950/35 text-[0.9rem] font-semibold text-red-300 transition hover:bg-red-950/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500/55 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Trash2 strokeWidth={2} className="h-4 w-4 shrink-0" aria-hidden /> Löschen
                </button>
              </div>
            </Card>
          )
        })}
        {protocols.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">Keine Protokolle für den gewählten Filter.</p>
        ) : null}
      </div>

      {!protocols.length ? (
        <div className="mt-8 rounded-2xl border border-dashed border-zinc-800 p-6 text-center text-sm text-zinc-500">
          Gespeicherte Protokolle erscheinen hier automatisch nach dem Speichern.
        </div>
      ) : null}
    </div>
  )
}
