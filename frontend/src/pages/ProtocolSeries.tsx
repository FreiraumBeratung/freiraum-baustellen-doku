import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  api,
  deleteProtocol,
  downloadExport,
  listProtocols,
  THOUGHTS_PROJECT_ID,
  THOUGHTS_PROJECT_NAME,
  type SiteProtocol,
} from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

function previewText(p: SiteProtocol): string {
  return (p.polishedText || p.rawText || '').trim()
}

function seqRange(signed: SiteProtocol[]): string {
  const nums = signed.map((p) => p.sequenceNumber).filter((n): n is number => typeof n === 'number' && n > 0)
  if (!nums.length) return ''
  const lo = Math.min(...nums)
  const hi = Math.max(...nums)
  return lo === hi ? `Nr. ${lo}` : `Nr. ${lo}–${hi}`
}

export function ProtocolSeriesPage() {
  const { projectId } = useParams()
  const nav = useNavigate()
  const { writeBlocked } = useWriteBlocked()
  const [signed, setSigned] = useState<SiteProtocol[]>([])
  const [quick, setQuick] = useState<SiteProtocol[]>([])
  const [thoughts, setThoughts] = useState<SiteProtocol[]>([])
  const [projectName, setProjectName] = useState('')
  const [msg, setMsg] = useState('')
  const [dlBusy, setDlBusy] = useState(false)
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const isThoughtsBucket = projectId === THOUGHTS_PROJECT_ID

  const load = useCallback(async () => {
    if (!projectId) return
    const r = await listProtocols({ projectId })
    const all = r.protocols
    const s = all
      .filter((p) => p.mode === 'signed')
      .sort((a, b) => (a.sequenceNumber || 0) - (b.sequenceNumber || 0))
    const q = all.filter((p) => p.mode === 'quick')
    const t = all
      .filter((p) => p.mode === 'thoughts' || p.projectId === THOUGHTS_PROJECT_ID)
      .sort((a, b) => b.date.localeCompare(a.date) || b.createdAt.localeCompare(a.createdAt))
    setSigned(s)
    setQuick(q)
    setThoughts(t)
    setProjectName(
      projectId === THOUGHTS_PROJECT_ID
        ? THOUGHTS_PROJECT_NAME
        : s[0]?.projectName || q[0]?.projectName || t[0]?.projectName || 'Baustelle',
    )
  }, [projectId])

  useEffect(() => {
    load().catch(() => {})
  }, [load])

  async function confirmDelete(p: SiteProtocol) {
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
    }
  }

  async function downloadCollective() {
    if (!projectId) return
    setDlBusy(true)
    try {
      await downloadExport(`/api/projects/${encodeURIComponent(projectId)}/collective-protocol/export/pdf`)
    } catch {
      setOfficeErr('Gesamtprotokoll konnte nicht erstellt werden.')
    } finally {
      setDlBusy(false)
    }
  }

  async function sendCollective() {
    if (!projectId) return
    setOfficeMsg('')
    setOfficeErr('')
    setOfficeBusy(true)
    try {
      const res = await api<{ ok: boolean; simulated: boolean; message: string }>(
        `/api/projects/${encodeURIComponent(projectId)}/collective-protocol/send-office`,
        { method: 'POST' },
      )
      setOfficeMsg(res.message?.trim() || 'Gesamtprotokoll wurde ans Büro gesendet.')
    } catch (ex) {
      setOfficeErr(ex instanceof Error ? ex.message : 'Versand fehlgeschlagen.')
    } finally {
      setOfficeBusy(false)
    }
  }

  if (!projectId) {
    return (
      <div>
        <PageTitle title="Protokolle" subtitle="Ungültige Baustelle" />
        <BigButton variant="secondary" onClick={() => nav('/protokolle')}>
          Zur Liste
        </BigButton>
      </div>
    )
  }

  const range = seqRange(signed)

  return (
    <div className="overflow-x-hidden">
      <PageTitle
        title={projectName}
        subtitle={isThoughtsBucket ? 'Ohne Baustellenbezug · ans Büro senden' : 'Begehungen & Schnellnotizen'}
      />

      {!isThoughtsBucket && signed.length ? (
        <Card className="mb-5 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-white">
                {signed.length} {signed.length === 1 ? 'Begehung' : 'Begehungen'}
                {range ? ` (${range})` : ''}
              </p>
              <p className="mt-1 text-xs text-zinc-500">Chronologisch — einzeln öffnen oder als Gesamtprotokoll</p>
            </div>
            <span className="rounded-full bg-orange-500/15 px-2.5 py-1 text-xs font-semibold text-orange-300 ring-1 ring-orange-400/30">
              Gesamt
            </span>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <BigButton type="button" disabled={dlBusy || officeBusy} onClick={() => void downloadCollective()}>
              {dlBusy ? '…' : 'Gesamtprotokoll PDF'}
            </BigButton>
            <BigButton
              variant="secondary"
              type="button"
              disabled={dlBusy || officeBusy || writeBlocked}
              onClick={() => void sendCollective()}
            >
              {officeBusy ? '…' : 'Gesamt ans Büro'}
            </BigButton>
          </div>
          {officeMsg ? <p className="text-sm text-orange-300">{officeMsg}</p> : null}
          {officeErr ? <p className="text-sm text-red-400">{officeErr}</p> : null}
        </Card>
      ) : null}

      {msg ? <p className="mb-3 text-sm text-orange-300">{msg}</p> : null}

      {!isThoughtsBucket ? (
        <div className="space-y-3">
          {signed.map((p) => {
            const text = previewText(p)
            return (
              <Card key={p.id} className="px-5 py-4">
                <div className="flex items-start gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold uppercase tracking-wide text-orange-400">
                      Begehung Nr. {p.sequenceNumber ?? '—'} · {formatDateDe(p.date)}
                    </p>
                    {p.participants ? (
                      <p className="mt-1 text-xs text-zinc-500">Teilnehmer: {p.participants}</p>
                    ) : null}
                    {text ? <p className="mt-2 line-clamp-2 text-sm text-zinc-400">{text}</p> : null}
                  </div>
                  <Link
                    to={`/protokolle/${p.id}`}
                    className="shrink-0 rounded-xl bg-white/[0.08] px-3 py-2 text-xs font-semibold text-white ring-1 ring-white/[0.1]"
                  >
                    Öffnen
                  </Link>
                </div>
                <button
                  type="button"
                  disabled={writeBlocked}
                  onClick={() => void confirmDelete(p)}
                  className="mt-3 text-xs font-medium text-red-400/90 hover:text-red-300 disabled:opacity-40"
                >
                  Löschen
                </button>
              </Card>
            )
          })}
        </div>
      ) : null}

      {!isThoughtsBucket && quick.length ? (
        <section className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">Schnellnotizen</h2>
          <div className="space-y-2">
            {quick.map((p) => (
              <Card key={p.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm text-zinc-300">{formatDateDe(p.date)}</p>
                  <p className="line-clamp-1 text-xs text-zinc-500">{previewText(p) || '—'}</p>
                </div>
                <Link to={`/protokolle/${p.id}`} className="shrink-0 text-xs font-semibold text-orange-400">
                  Öffnen
                </Link>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      {thoughts.length ? (
        <section className={isThoughtsBucket ? 'mt-0' : 'mt-8'}>
          {!isThoughtsBucket ? (
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">Gedankensammlung</h2>
          ) : null}
          <div className="space-y-2">
            {thoughts.map((p) => (
              <Card key={p.id} className="px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm text-zinc-300">{formatDateDe(p.date)}</p>
                    <p className="line-clamp-2 text-xs text-zinc-500">{previewText(p) || '—'}</p>
                  </div>
                  <Link to={`/protokolle/${p.id}`} className="shrink-0 text-xs font-semibold text-orange-400">
                    Öffnen
                  </Link>
                </div>
                <button
                  type="button"
                  disabled={writeBlocked}
                  onClick={() => void confirmDelete(p)}
                  className="mt-2 text-xs font-medium text-red-400/90 hover:text-red-300 disabled:opacity-40"
                >
                  Löschen
                </button>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      {!signed.length && !quick.length && !thoughts.length ? (
        <p className="text-center text-sm text-zinc-500">
          {isThoughtsBucket ? 'Noch keine Gedankensammlung.' : 'Keine Protokolle für diese Baustelle.'}
        </p>
      ) : null}

      <div className="mt-8">
        <button
          type="button"
          onClick={() => nav('/protokolle')}
          className="text-sm font-medium text-zinc-500 hover:text-zinc-300"
        >
          ← Zur Protokollliste
        </button>
      </div>
    </div>
  )
}
