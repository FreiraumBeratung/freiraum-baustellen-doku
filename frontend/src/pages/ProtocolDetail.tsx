import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { api, downloadExport, type SiteProtocol } from '../api/client'
import { ReportPhotosSection } from '../components/ReportPhotosSection'
import { ReportSignaturesSection } from '../components/ReportSignaturesSection'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type ProtocolDetailNavState = {
  openPhotos?: boolean
  photoUploadOk?: boolean
}

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

function modeTitle(p: SiteProtocol): string {
  if (p.mode === 'signed' && p.sequenceNumber) return `Begehungsprotokoll Nr. ${p.sequenceNumber}`
  if (p.mode === 'signed') return 'Protokoll mit Unterschrift'
  return 'Schnellnotiz'
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2 text-sm last:border-0">
      <span className="text-zinc-500">{k}</span>
      <span className="text-right text-white">{v}</span>
    </div>
  )
}

export function ProtocolDetailPage() {
  const { id } = useParams()
  const { writeBlocked } = useWriteBlocked()
  const nav = useNavigate()
  const location = useLocation()
  const navState = (location.state ?? null) as ProtocolDetailNavState | null
  const searchParams = new URLSearchParams(location.search)
  const openPhotosFromQuery = searchParams.get('photos') === '1'
  const openSignaturesFromQuery = searchParams.get('signatures') === '1'
  const uploadedFromQuery = searchParams.get('uploaded') === '1'
  const [p, setP] = useState<SiteProtocol | null>(null)
  const [contactPerson, setContactPerson] = useState('')
  const [profileCompanyName, setProfileCompanyName] = useState('')
  const [dlBusy, setDlBusy] = useState(false)
  const [dlErr, setDlErr] = useState('')
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const abschlussRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!id) return
    api<SiteProtocol>(`/api/protocols/${id}`)
      .then(setP)
      .catch(() => setP(null))
    api<{ companyName: string; contactPerson?: string }>('/api/company-profile')
      .then((prof) => {
        setProfileCompanyName(prof.companyName?.trim() || '')
        setContactPerson(prof.contactPerson?.trim() || '')
      })
      .catch(() => {})
  }, [id])

  useEffect(() => {
    if (!p || (!openPhotosFromQuery && !openSignaturesFromQuery)) return
    const t = window.setTimeout(() => {
      abschlussRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 350)
    return () => window.clearTimeout(t)
  }, [p, openPhotosFromQuery, openSignaturesFromQuery])

  async function dlPdf() {
    if (!id) return
    setDlErr('')
    setDlBusy(true)
    try {
      await downloadExport(`/api/protocols/${id}/export/pdf`)
    } catch {
      setDlErr('PDF konnte nicht erstellt werden.')
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
        `/api/protocols/${id}/send-office`,
        { method: 'POST' },
      )
      const text = res.message?.trim()
      if (text) setOfficeMsg(text)
      else
        setOfficeMsg(
          res.simulated
            ? 'SMTP ist noch nicht konfiguriert. Versand wurde simuliert.'
            : 'Protokoll wurde ans Büro gesendet.',
        )
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setOfficeErr(m || 'Protokoll konnte nicht gesendet werden.')
    } finally {
      setOfficeBusy(false)
    }
  }

  if (!id) {
    return (
      <div>
        <PageTitle title="Protokoll" subtitle="Ungültige Adresse" />
        <BigButton variant="secondary" onClick={() => nav('/protokolle')}>
          Zur Liste
        </BigButton>
      </div>
    )
  }

  if (!p) {
    return (
      <div>
        <PageTitle title="Protokoll" subtitle="Wird geladen…" />
        <BigButton variant="secondary" onClick={() => nav('/protokolle')}>
          Zur Liste
        </BigButton>
      </div>
    )
  }

  const body = (p.polishedText || p.rawText || '').trim()
  const entrepreneurName = contactPerson || profileCompanyName || ''
  const partnerName = p.participants?.trim() || ''

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Protokoll" subtitle={modeTitle(p)} />

      <Card className="mb-4 space-y-1">
        <Field k="Baustelle" v={p.projectName} />
        {p.customerName ? <Field k="Kunde" v={p.customerName} /> : null}
        <Field k="Datum" v={formatDateDe(p.date)} />
        <Field k="Art" v={modeTitle(p)} />
        {p.participants ? <Field k="Teilnehmer" v={p.participants} /> : null}
      </Card>

      <Card className="mb-4">
        <h3 className="text-sm font-semibold uppercase text-orange-400">Inhalt</h3>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-200">{body || '—'}</p>
      </Card>

      {p.mode === 'signed' ? (
        <div ref={abschlussRef} id="protokoll-abschluss" className="mt-4 scroll-mt-4">
          <Card>
            <ReportPhotosSection
              reportId={null}
              protocolId={id}
              enabled
              embedded
              iosGalleryRedirect
              initialOpen={Boolean(navState?.openPhotos || openPhotosFromQuery)}
            />
            <ReportSignaturesSection
              reportId={null}
              protocolId={id}
              enabled
              embedded
              entrepreneurName={entrepreneurName}
              partnerName={partnerName}
              initialOpen={Boolean(openSignaturesFromQuery)}
            />
          </Card>
        </div>
      ) : null}

      <div className="mt-6 space-y-3">
        {navState?.photoUploadOk || uploadedFromQuery ? (
          <p className="text-center text-sm text-emerald-400/90">Foto übernommen.</p>
        ) : null}
        {officeMsg ? <p className="text-center text-sm text-orange-300">{officeMsg}</p> : null}
        {officeErr ? <p className="text-center text-sm text-red-400">{officeErr}</p> : null}
        {dlErr ? <p className="text-center text-sm text-red-400">{dlErr}</p> : null}
        <BigButton type="button" disabled={writeBlocked || officeBusy || dlBusy} onClick={() => void sendOffice()}>
          {officeBusy ? '…' : 'Ans Büro senden'}
        </BigButton>
        <BigButton variant="secondary" type="button" disabled={dlBusy || officeBusy} onClick={() => void dlPdf()}>
          {dlBusy ? '…' : 'PDF herunterladen'}
        </BigButton>
        <BigButton variant="secondary" type="button" onClick={() => nav('/protokolle')}>
          Zur Liste
        </BigButton>
      </div>
    </div>
  )
}
