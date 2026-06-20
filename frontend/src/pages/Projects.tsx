import { Download, Layers, RotateCcw, Send } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, downloadExport } from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type Project = {
  id: string
  name: string
  customer: string
  address: string
  contactPerson: string
  note: string
  status: 'aktiv' | 'pausiert' | 'abgeschlossen'
  currentRunId?: string | null
  runStartedAt?: string | null
  lastClosedRunId?: string | null
}

function formatDateTimeDe(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const statusLabel: Record<Project['status'], string> = {
  aktiv: 'Aktiv',
  pausiert: 'Pausiert',
  abgeschlossen: 'Abgeschlossen',
}

const statusTone: Record<Project['status'], string> = {
  aktiv:
    'border border-orange-400/45 bg-orange-500/[0.1] text-orange-300/95 shadow-[0_0_22px_-14px_rgba(249,115,22,0.38)]',
  pausiert: 'border border-amber-500/44 bg-amber-500/[0.09] text-amber-200/95',
  abgeschlossen: 'border border-zinc-600/75 bg-zinc-800/90 text-zinc-400',
}

export function ProjectsPage() {
  const { writeBlocked } = useWriteBlocked()
  const [rows, setRows] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [customer, setCustomer] = useState('')
  const [address, setAddress] = useState('')
  const [contactPerson, setContactPerson] = useState('')
  const [note, setNote] = useState('')
  const [busyRunId, setBusyRunId] = useState<string | null>(null)
  const [runMsg, setRunMsg] = useState<Record<string, string>>({})

  async function load() {
    const r = await api<{ projects: Project[] }>('/api/projects')
    setRows(r.projects)
  }

  useEffect(() => {
    load().catch(() => {})
  }, [])

  async function add(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || writeBlocked) return
    await api<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify({
        name: name.trim(),
        customer,
        address,
        contactPerson,
        note,
        status: 'aktiv',
      }),
    })
    setName('')
    setCustomer('')
    setAddress('')
    setContactPerson('')
    setNote('')
    load()
  }

  async function cycleStatus(p: Project) {
    if (writeBlocked) return
    const order: Project['status'][] = ['aktiv', 'pausiert', 'abgeschlossen']
    const idx = order.indexOf(p.status)
    const next = order[(idx + 1) % order.length]
    await api(`/api/projects/${p.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: next }),
    })
    load()
  }

  async function closeRun(p: Project) {
    if (writeBlocked) return
    setBusyRunId(p.id)
    setRunMsg((m) => ({ ...m, [p.id]: '' }))
    try {
      await api(`/api/projects/${p.id}/close-run`, { method: 'POST' })
      setRunMsg((m) => ({ ...m, [p.id]: 'Baustelle abgeschlossen — Gesamtbericht ist bereit.' }))
      await load()
    } catch {
      setRunMsg((m) => ({ ...m, [p.id]: 'Abschließen fehlgeschlagen.' }))
    } finally {
      setBusyRunId(null)
    }
  }

  async function downloadCollective(p: Project, kind: 'pdf' | 'word') {
    setBusyRunId(p.id)
    setRunMsg((m) => ({ ...m, [p.id]: '' }))
    try {
      await downloadExport(`/api/projects/${p.id}/collective-report/export/${kind}`)
    } catch {
      setRunMsg((m) => ({ ...m, [p.id]: 'Gesamtbericht konnte nicht erstellt werden.' }))
    } finally {
      setBusyRunId(null)
    }
  }

  async function sendCollective(p: Project) {
    if (writeBlocked) return
    setBusyRunId(p.id)
    setRunMsg((m) => ({ ...m, [p.id]: '' }))
    try {
      const res = await api<{ ok: boolean; message: string }>(
        `/api/projects/${p.id}/collective-report/send-office`,
        { method: 'POST' },
      )
      setRunMsg((m) => ({ ...m, [p.id]: res.message?.trim() || 'Gesamtbericht ans Büro gesendet.' }))
    } catch (ex) {
      const msg = ex instanceof Error ? ex.message : ''
      setRunMsg((m) => ({ ...m, [p.id]: msg || 'Gesamtbericht konnte nicht gesendet werden.' }))
    } finally {
      setBusyRunId(null)
    }
  }

  async function reactivate(p: Project) {
    if (writeBlocked) return
    setBusyRunId(p.id)
    try {
      await api(`/api/projects/${p.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'aktiv' }) })
      await load()
    } finally {
      setBusyRunId(null)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Baustellen" subtitle="Aktive Projekte erscheinen im Tagesbericht" />

      <Card className="mb-8 border-transparent bg-black/44 py-10 shadow-none ring-1 ring-white/[0.08]">
        <form onSubmit={add} className="space-y-2.5">
          <label className="block min-w-0">
            <span className="text-xs tracking-wide text-zinc-400">Baustellenname</span>
            <input
              className="mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </label>
          <label className="block min-w-0">
            <span className="text-xs tracking-wide text-zinc-400">Kunde</span>
            <input
              className="mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42"
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
            />
          </label>
          <label className="block min-w-0">
            <span className="text-xs tracking-wide text-zinc-400">Adresse</span>
            <input
              className="mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </label>
          <label className="block min-w-0">
            <span className="text-xs tracking-wide text-zinc-400">Ansprechpartner vor Ort</span>
            <input
              className="mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42"
              value={contactPerson}
              onChange={(e) => setContactPerson(e.target.value)}
            />
          </label>
          <label className="block min-w-0">
            <span className="text-xs tracking-wide text-zinc-400">Notiz</span>
            <textarea
              className="mt-1 min-h-[72px] w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-2 text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <BigButton type="submit" disabled={writeBlocked}>Baustelle anlegen</BigButton>
        </form>
      </Card>

      <div className="space-y-4">
        {rows.map((p) => (
          <Card key={p.id} className="border-transparent bg-black/38 py-[1.15rem] shadow-none ring-1 ring-white/[0.06] backdrop-blur-sm">
            <div className="flex flex-col gap-2.5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[1.05rem] font-semibold text-white">{p.name}</h3>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-[0.22rem] text-[9px] font-semibold uppercase tracking-[0.14em] ${statusTone[p.status]}`}>
                      {statusLabel[p.status]}
                    </span>
                  </div>
                  {p.customer ? <div className="mt-1.5 text-sm text-zinc-400">{p.customer}</div> : null}
                  {p.contactPerson ? (
                    <div className="text-xs tracking-wide text-zinc-600">{p.contactPerson}</div>
                  ) : null}
                  <div className="text-xs text-zinc-500">{p.address}</div>
                </div>
              </div>

              {p.note ? (
                <p className="rounded-[1rem] bg-black/52 px-[0.875rem] py-[0.625rem] text-[0.805rem] text-zinc-300 ring-1 ring-white/[0.06]">{p.note}</p>
              ) : null}

              <button
                type="button"
                disabled={writeBlocked}
                onClick={() => cycleStatus(p)}
                className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-[1rem] bg-black/50 py-[0.7rem] text-[0.78rem] font-semibold uppercase tracking-[0.1em] text-orange-400/98 ring-1 ring-white/[0.08] transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
              >
                <RotateCcw strokeWidth={2} className="h-4 w-4 opacity-95" aria-hidden />
                nächsten Status wählen
              </button>

              {p.currentRunId || p.lastClosedRunId ? (
                <div className="mt-1 rounded-[1rem] border border-orange-400/25 bg-orange-500/[0.06] px-[0.875rem] py-[0.8rem]">
                  <div className="flex items-center gap-2 text-[0.74rem] font-semibold uppercase tracking-[0.1em] text-orange-300/95">
                    <Layers strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
                    Folgebericht
                  </div>
                  {p.currentRunId ? (
                    <p className="mt-1.5 text-[0.8rem] text-zinc-400">
                      Läuft{p.runStartedAt ? ` seit ${formatDateTimeDe(p.runStartedAt)}` : ''} — neue Tagesberichte
                      werden gesammelt.
                    </p>
                  ) : (
                    <p className="mt-1.5 text-[0.8rem] text-zinc-400">
                      Durchlauf abgeschlossen — Gesamtbericht verfügbar.
                    </p>
                  )}

                  {p.currentRunId ? (
                    <button
                      type="button"
                      disabled={writeBlocked || busyRunId === p.id}
                      onClick={() => closeRun(p)}
                      className="mt-2.5 inline-flex w-full items-center justify-center gap-2 rounded-[0.9rem] bg-orange-500/90 py-[0.65rem] text-[0.78rem] font-semibold text-zinc-950 transition hover:bg-orange-400 active:scale-[0.99] disabled:opacity-40"
                    >
                      {busyRunId === p.id ? '…' : 'Baustelle abschließen & Gesamtbericht'}
                    </button>
                  ) : null}

                  <button
                    type="button"
                    disabled={writeBlocked || busyRunId === p.id}
                    onClick={() => sendCollective(p)}
                    className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-[0.9rem] bg-black/55 py-[0.65rem] text-[0.78rem] font-semibold text-orange-300/95 ring-1 ring-orange-400/30 transition hover:bg-black/65 active:scale-[0.99] disabled:opacity-40"
                  >
                    <Send strokeWidth={2} className="h-4 w-4" aria-hidden />
                    Gesamtbericht ans Büro senden
                  </button>

                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      disabled={busyRunId === p.id}
                      onClick={() => downloadCollective(p, 'pdf')}
                      className="inline-flex items-center justify-center gap-1.5 rounded-[0.9rem] bg-black/50 py-[0.6rem] text-[0.76rem] font-semibold text-zinc-200 ring-1 ring-white/[0.08] transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
                    >
                      <Download strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
                      PDF
                    </button>
                    <button
                      type="button"
                      disabled={busyRunId === p.id}
                      onClick={() => downloadCollective(p, 'word')}
                      className="inline-flex items-center justify-center gap-1.5 rounded-[0.9rem] bg-black/50 py-[0.6rem] text-[0.76rem] font-semibold text-zinc-200 ring-1 ring-white/[0.08] transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
                    >
                      <Download strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
                      Word
                    </button>
                  </div>
                  {runMsg[p.id] ? (
                    <p className="mt-2 text-[0.78rem] text-zinc-300">{runMsg[p.id]}</p>
                  ) : null}
                </div>
              ) : null}

              {p.status === 'abgeschlossen' ? (
                <button
                  type="button"
                  disabled={writeBlocked || busyRunId === p.id}
                  onClick={() => reactivate(p)}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-[1rem] bg-black/50 py-[0.7rem] text-[0.78rem] font-semibold uppercase tracking-[0.1em] text-emerald-300/95 ring-1 ring-emerald-400/25 transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
                >
                  <RotateCcw strokeWidth={2} className="h-4 w-4" aria-hidden />
                  Baustelle reaktivieren
                </button>
              ) : null}
            </div>
          </Card>
        ))}
        {rows.length === 0 ? <p className="text-center text-sm text-zinc-500">Noch keine Baustellen.</p> : null}
      </div>
    </div>
  )
}
