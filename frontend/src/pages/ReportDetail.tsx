import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { api, downloadExport } from '../api/client'
import { ReportPhotosSection } from '../components/ReportPhotosSection'
import { ReportSignaturesSection } from '../components/ReportSignaturesSection'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import type { FeedbackNavState } from './Feedback'

type ReportDetailNavState = {
  openPhotos?: boolean
  photoUploadOk?: boolean
}

type ReportDoc = {
  id: string
  companyName: string
  projectName: string
  customerName: string
  date: string
  employees: string[]
  startTime: string
  endTime: string
  exportFormat: string
  rawText: string
  structured: {
    summary: string
    activities: string[]
    materials: string[]
    materialSuggestions?: string[]
    machineSuggestions?: string[]
    machineHours?: string[]
    problems: string[]
    openItems: string[]
    customerTalk: string
  }
}

export function ReportDetailPage() {
  const { id } = useParams()
  const { writeBlocked } = useWriteBlocked()
  const nav = useNavigate()
  const location = useLocation()
  const navState = (location.state ?? null) as ReportDetailNavState | null
  const searchParams = new URLSearchParams(location.search)
  const openPhotosFromQuery = searchParams.get('photos') === '1'
  const openSignaturesFromQuery = searchParams.get('signatures') === '1'
  const uploadedFromQuery = searchParams.get('uploaded') === '1'
  const [r, setR] = useState<ReportDoc | null>(null)
  const [dlBusy, setDlBusy] = useState(false)
  const [dlErr, setDlErr] = useState('')
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const abschlussRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!id) return
    api<ReportDoc>(`/api/reports/${id}`)
      .then(setR)
      .catch(() => setR(null))
  }, [id])

  useEffect(() => {
    if (!r || (!openPhotosFromQuery && !openSignaturesFromQuery)) return
    const t = window.setTimeout(() => {
      abschlussRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 350)
    return () => window.clearTimeout(t)
  }, [r, openPhotosFromQuery, openSignaturesFromQuery])

  async function dlExport(kind: 'pdf' | 'word') {
    if (!id) return
    setDlErr('')
    setDlBusy(true)
    try {
      await downloadExport(
        kind === 'pdf' ? `/api/reports/${id}/export/pdf` : `/api/reports/${id}/export/word`,
      )
    } catch {
      setDlErr('Export konnte nicht erstellt werden.')
    } finally {
      setDlBusy(false)
    }
  }

  async function sendOffice() {
    if (!id) return
    setOfficeMsg('')
    setOfficeErr('')
    setOfficeBusy(true)
    try {
      const res = await api<{ ok: boolean; simulated: boolean; message: string }>(
        `/api/reports/${id}/send-office`,
        { method: 'POST' },
      )
      const text = res.message?.trim()
      if (text) setOfficeMsg(text)
      else
        setOfficeMsg(
          res.simulated
            ? 'SMTP ist noch nicht konfiguriert. Versand wurde simuliert.'
            : 'Bericht wurde ans Büro gesendet.',
        )
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setOfficeErr(m || 'Bericht konnte nicht gesendet werden.')
    } finally {
      setOfficeBusy(false)
    }
  }

  if (!id) {
    return (
      <div>
        <PageTitle title="Bericht" subtitle="Ungültige Adresse" />
        <BigButton variant="secondary" onClick={() => nav('/berichte')}>
          Zur Liste
        </BigButton>
      </div>
    )
  }

  if (!r) {
    return (
      <div>
        <PageTitle title="Bericht" subtitle="Wird geladen…" />
        <BigButton variant="secondary" onClick={() => nav('/berichte')}>
          Zur Liste
        </BigButton>
      </div>
    )
  }

  const report = r
  const s = report.structured

  function copyAll() {
    const addList = (label: string, items: string[]) => {
      lines.push('')
      lines.push(label)
      if (items.length) items.forEach((a) => lines.push(`• ${a}`))
      else lines.push('• Keine Angabe')
    }
    const lines: string[] = [
      'TAGESBERICHT',
      `Firma: ${report.companyName}`,
      `Baustelle: ${report.projectName}`,
      `Kunde: ${report.customerName}`,
      `Datum: ${report.date}`,
      `Mitarbeiter: ${report.employees.length ? report.employees.join(', ') : 'Keine Angabe'}`,
      `Arbeitszeit: ${report.startTime} – ${report.endTime}`,
      `Format: ${report.exportFormat}`,
      '',
      'Zusammenfassung',
      s.summary?.trim() || 'Keine Zusammenfassung vorhanden',
    ]
    addList('Tätigkeiten', s.activities)
    addList('Material', s.materials)
    addList('Maschinenstunden', s.machineHours ?? [])
    addList('Probleme', s.problems)
    addList('Offene Punkte', s.openItems)
    lines.push('', 'Kundengespräch', s.customerTalk || 'Keine Angabe', '', 'Rohtext', report.rawText)
    void navigator.clipboard.writeText(lines.join('\n'))
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Tagesbericht" subtitle={report.date} />

      <Card className="mb-4 space-y-4">
        <Field k="Firma" v={report.companyName} />
        <Field k="Baustelle" v={report.projectName} />
        <Field k="Kunde" v={report.customerName} />
        <Field k="Datum" v={report.date} />
        <Field k="Mitarbeiter" v={report.employees.length ? report.employees.join(', ') : 'Keine Angabe'} />
        <Field k="Arbeitszeit" v={`${report.startTime} – ${report.endTime}`} />
        <Field k="Format" v={report.exportFormat} />
      </Card>

      <Card className="space-y-6">
        <section>
          <h3 className="text-sm font-semibold uppercase text-orange-400">Zusammenfassung</h3>
          {s.summary?.trim() ? (
            <p className="mt-2 whitespace-pre-wrap text-zinc-200">{s.summary}</p>
          ) : (
            <p className="mt-2 text-xs text-zinc-600">Keine Zusammenfassung vorhanden</p>
          )}
        </section>
        <ListSec title="Tätigkeiten" items={s.activities} />
        <ListSec title="Material" items={s.materials} />
        <ListSec title="Maschinenstunden" items={s.machineHours ?? []} />
        <ListSec title="Probleme" items={s.problems} />
        <ListSec title="Offene Punkte" items={s.openItems} />
        <section>
          <h3 className="text-sm font-semibold uppercase text-orange-400">Kundengespräch</h3>
          <p className="mt-2 whitespace-pre-wrap text-zinc-200">{s.customerTalk || 'Keine Angabe'}</p>
        </section>
        <section>
          <h3 className="text-sm font-semibold uppercase text-orange-400">Rohtext</h3>
          <p className="mt-2 whitespace-pre-wrap text-zinc-400">{report.rawText}</p>
        </section>
      </Card>

      <div ref={abschlussRef} id="bericht-abschluss" className="mt-4 scroll-mt-4">
        <Card>
          <ReportPhotosSection
            reportId={id}
            enabled
            embedded
            iosGalleryRedirect
            initialOpen={Boolean(navState?.openPhotos || openPhotosFromQuery)}
          />
          <ReportSignaturesSection
            reportId={id}
            enabled
            embedded
            customerName={report.customerName}
            initialOpen={Boolean(openSignaturesFromQuery)}
          />
        </Card>
      </div>

      <div className="mt-6 space-y-3">
        {navState?.photoUploadOk || uploadedFromQuery ? (
          <p className="text-center text-sm text-emerald-400/90">Foto übernommen.</p>
        ) : null}
        {officeMsg ? <p className="text-sm text-orange-300">{officeMsg}</p> : null}
        {officeErr ? <p className="text-sm text-red-400">{officeErr}</p> : null}
        {dlErr ? <p className="text-sm text-red-400">{dlErr}</p> : null}
        <BigButton type="button" onClick={copyAll}>
          Text kopieren
        </BigButton>
        <BigButton
          variant="secondary"
          type="button"
          onClick={() => {
            const state: FeedbackNavState = {
              category: 'Problem',
              reportId: id,
              reportLabel: `${report.projectName} · ${report.date}`,
              prefill: `Betreffender Bericht: ${report.projectName}, ${report.date}\n\n`,
            }
            nav('/feedback', { state })
          }}
        >
          Problem melden
        </BigButton>
        <BigButton
          variant="secondary"
          type="button"
          disabled={dlBusy}
          onClick={() => void dlExport('pdf')}
        >
          {dlBusy ? '…' : 'PDF herunterladen'}
        </BigButton>
        <BigButton
          variant="secondary"
          type="button"
          disabled={dlBusy}
          onClick={() => void dlExport('word')}
        >
          {dlBusy ? '…' : 'Word herunterladen'}
        </BigButton>
        <BigButton
          variant="secondary"
          type="button"
          disabled={writeBlocked || officeBusy || dlBusy}
          onClick={() => void sendOffice()}
        >
          {officeBusy ? '…' : 'Ans Büro senden'}
        </BigButton>
      </div>
    </div>
  )
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex gap-3 border-b border-zinc-800 pb-2 text-sm last:border-0">
      <span className="shrink-0 text-zinc-500">{k}</span>
      <span className="min-w-0 flex-1 text-right whitespace-pre-wrap text-white">{v}</span>
    </div>
  )
}

function ListSec({ title, items }: { title: string; items: string[] }) {
  const rows = items.length ? items : ['Keine Angabe']
  return (
    <section>
      <h3 className="text-sm font-semibold uppercase text-orange-400">{title}</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-zinc-300">
        {rows.map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
    </section>
  )
}
