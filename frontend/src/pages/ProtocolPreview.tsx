import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  api,
  createProtocol,
  downloadExport,
  resolveBackendPublicUrl,
  type SiteProtocol,
} from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { ReportPhotosSection } from '../components/ReportPhotosSection'
import { ReportSignaturesSection } from '../components/ReportSignaturesSection'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import type { ProtocolPreviewState } from './ProtocolNew'

const textareaClass =
  'mt-2 w-full min-w-0 resize-y rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none placeholder:text-zinc-600 focus:border-orange-500 min-h-[10rem]'

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

export function ProtocolPreviewPage() {
  const nav = useNavigate()
  const location = useLocation()
  const st = location.state as ProtocolPreviewState | null
  const { writeBlocked } = useWriteBlocked()

  const [companyName, setCompanyName] = useState('')
  const [contactPerson, setContactPerson] = useState('')
  const [logoUrl, setLogoUrl] = useState<string | null>(null)
  const [draftText, setDraftText] = useState('')
  const [savedProtocol, setSavedProtocol] = useState<SiteProtocol | null>(null)
  const [saveBusy, setSaveBusy] = useState(false)
  const [saveErr, setSaveErr] = useState('')
  const [saveMsg, setSaveMsg] = useState('')
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const [dlBusy, setDlBusy] = useState(false)
  const [dlErr, setDlErr] = useState('')
  const [moreOpen, setMoreOpen] = useState(false)
  const [pageWakeKey, setPageWakeKey] = useState(0)

  const savedId = savedProtocol?.id ?? null
  const mode = st?.mode ?? 'quick'
  const modeTitle =
    mode === 'signed' ? 'Begehungsprotokoll' : mode === 'thoughts' ? 'Gedankensammlung' : 'Schnellnotiz'
  const entrepreneurName = contactPerson || companyName
  const partnerName = savedProtocol?.participants?.trim() || st?.participants?.trim() || ''
  const isThoughts = mode === 'thoughts'

  useEffect(() => {
    if (!st) {
      nav('/protokoll', { replace: true })
      return
    }
    setDraftText((st.polishedText || st.rawText).trim())
    api<{ companyName: string; contactPerson?: string; logoUrl: string | null }>('/api/company-profile')
      .then((p) => {
        setCompanyName(p.companyName?.trim() || 'Ihre Firma')
        setContactPerson(p.contactPerson?.trim() || '')
        setLogoUrl(p.logoUrl)
      })
      .catch(() => setCompanyName('Ihre Firma'))
  }, [st, nav])

  const initialText = useMemo(() => {
    if (!st) return ''
    return (st.polishedText || st.rawText).trim()
  }, [st])

  const dirty = useMemo(() => {
    if (!st) return false
    return draftText.trim() !== initialText
  }, [draftText, initialText, st])

  if (!st) return null

  async function saveProtocol() {
    if (!st) return
    setSaveBusy(true)
    setSaveErr('')
    setSaveMsg('')
    try {
      const doc = await createProtocol({
        projectId: st.projectId,
        projectName: st.projectName,
        customerName: st.customerName,
        date: st.date,
        mode: st.mode,
        rawText: st.rawText,
        polishedText: draftText.trim() || st.rawText,
        participants: st.participants,
        exportFormat: st.exportFormat,
      })
      setSavedProtocol(doc)
      const nr =
        doc.mode === 'signed' && doc.sequenceNumber
          ? ` (Nr. ${doc.sequenceNumber})`
          : ''
      setSaveMsg(
        doc.mode === 'thoughts'
          ? 'Zur Tages-Sammlung hinzugefügt. Weiter einsprechen oder abends ans Büro senden.'
          : `Protokoll gespeichert${nr}.`,
      )
    } catch (ex) {
      setSaveErr(ex instanceof Error ? ex.message : 'Protokoll konnte nicht gespeichert werden.')
    } finally {
      setSaveBusy(false)
    }
  }

  async function sendOffice() {
    if (!savedId) return
    setOfficeMsg('')
    setOfficeErr('')
    setOfficeBusy(true)
    try {
      const res = await api<{ ok: boolean; simulated: boolean; message: string }>(
        `/api/protocols/${savedId}/send-office`,
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
      if (isThoughts) {
        setSavedProtocol((prev) =>
          prev ? { ...prev, officeSentAt: new Date().toISOString() } : prev,
        )
      }
    } catch (ex) {
      setOfficeErr(ex instanceof Error ? ex.message : 'Protokoll konnte nicht gesendet werden.')
    } finally {
      setOfficeBusy(false)
    }
  }

  async function doDownloadPdf() {
    if (!savedId) return
    setDlErr('')
    setDlBusy(true)
    try {
      await downloadExport(`/api/protocols/${savedId}/export/pdf`)
    } catch {
      setDlErr('PDF konnte nicht erstellt werden.')
    } finally {
      setDlBusy(false)
    }
  }

  return (
    <div key={`protocol-preview-${pageWakeKey}`} className="overflow-x-hidden">
      <PageTitle
        title="Protokoll"
        subtitle={
          savedId
            ? isThoughts
              ? 'Tages-Sammlung'
              : 'Unterschrift & Versand'
            : `${modeTitle} — prüfen`
        }
      />

      {!savedId ? (
        <p className="mb-2 text-center text-sm text-zinc-500">
          {isThoughts
            ? 'Text prüfen — dann zur Tages-Sammlung hinzufügen. Ans Büro erst am Abend.'
            : 'Text prüfen und bei Bedarf anpassen — danach speichern.'}
        </p>
      ) : null}
      {dirty && !savedId ? (
        <p className="mb-3 text-center text-sm text-amber-400">Text geändert — vor dem Speichern prüfen</p>
      ) : null}

      {logoUrl ? (
        <div className="mb-4 flex justify-center">
          <img
            src={resolveBackendPublicUrl(logoUrl) ?? logoUrl}
            alt=""
            className="h-14 w-auto object-contain opacity-90"
          />
        </div>
      ) : null}

      <Card className="mb-4 space-y-4">
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Firma</span>
            <span className="text-right font-medium text-white">{companyName}</span>
          </div>
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">{isThoughts ? 'Bezug' : 'Baustelle'}</span>
            <span className="text-right text-white">
              {isThoughts ? 'Ohne Baustelle' : st.projectName}
            </span>
          </div>
          {!isThoughts && st.customerName ? (
            <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
              <span className="text-zinc-500">Kunde</span>
              <span className="text-right text-white">{st.customerName}</span>
            </div>
          ) : null}
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Datum</span>
            <span className="text-right text-white">{formatDateDe(st.date)}</span>
          </div>
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Art</span>
            <span className="text-right text-white">{modeTitle}</span>
          </div>
          {st.participants ? (
            <div className="flex gap-3 border-b border-zinc-800 pb-2">
              <span className="shrink-0 text-zinc-500">Teilnehmer</span>
              <span className="min-w-0 flex-1 text-right text-white">{st.participants}</span>
            </div>
          ) : null}
        </div>

        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">Inhalt</h3>
          {!savedId ? (
            <textarea
              className={textareaClass}
              value={draftText}
              disabled={writeBlocked}
              onChange={(e) => setDraftText(e.target.value)}
            />
          ) : (
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-200">
              {savedProtocol?.polishedText?.trim() || savedProtocol?.rawText || draftText}
            </p>
          )}
        </section>

        {savedId && mode === 'signed' ? (
          <>
            <ReportPhotosSection
              reportId={null}
              protocolId={savedId}
              enabled
              iosGalleryRedirect
              onUploadComplete={() => setPageWakeKey((k) => k + 1)}
            />
            <ReportSignaturesSection
              reportId={null}
              protocolId={savedId}
              enabled
              entrepreneurName={entrepreneurName}
              partnerName={partnerName}
            />
          </>
        ) : null}

        {savedId && mode === 'quick' ? (
          <p className="border-t border-zinc-800 pt-4 text-xs text-zinc-500">
            Schnellnotiz — ohne Unterschrift. Direkt ans Büro senden oder PDF laden.
          </p>
        ) : null}

        {savedId && mode === 'thoughts' ? (
          <p className="border-t border-zinc-800 pt-4 text-xs text-zinc-500">
            {savedProtocol?.officeSentAt
              ? 'Bereits ans Büro gesendet. Weitere Einträge am selben Tag starten eine neue Sammlung.'
              : 'Tages-Sammlung — ohne Baustelle. Weiter einsprechen oder einmalig ans Büro senden.'}
          </p>
        ) : null}
      </Card>

      <div className="mt-6 space-y-3">
        {!savedId ? (
          <BigButton type="button" disabled={writeBlocked || saveBusy} onClick={() => void saveProtocol()}>
            {saveBusy
              ? '…'
              : isThoughts
                ? 'Zur Tages-Sammlung hinzufügen'
                : 'Protokoll speichern'}
          </BigButton>
        ) : null}

        {saveErr ? <p className="text-center text-sm text-red-400">{saveErr}</p> : null}
        {saveMsg ? <p className="text-center text-sm text-emerald-400/90">{saveMsg}</p> : null}
        {officeMsg ? <p className="text-center text-sm text-orange-300">{officeMsg}</p> : null}
        {officeErr ? <p className="text-center text-sm text-red-400">{officeErr}</p> : null}

        {savedId ? (
          <>
            {isThoughts && !savedProtocol?.officeSentAt ? (
              <BigButton
                type="button"
                disabled={writeBlocked || officeBusy || dlBusy}
                onClick={() =>
                  nav('/protokoll/neu', {
                    replace: true,
                    state: { mode: 'thoughts', date: st.date },
                  })
                }
              >
                Weiter einsprechen
              </BigButton>
            ) : null}

            <BigButton
              type="button"
              variant={isThoughts && !savedProtocol?.officeSentAt ? 'secondary' : undefined}
              disabled={writeBlocked || officeBusy || dlBusy || Boolean(isThoughts && savedProtocol?.officeSentAt)}
              onClick={() => void sendOffice()}
            >
              {officeBusy
                ? '…'
                : isThoughts && savedProtocol?.officeSentAt
                  ? 'Bereits ans Büro gesendet'
                  : 'Ans Büro senden'}
            </BigButton>

            <div className="overflow-hidden rounded-2xl ring-1 ring-white/[0.08]">
              <button
                type="button"
                aria-expanded={moreOpen}
                onClick={() => setMoreOpen((o) => !o)}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-medium text-zinc-400 transition hover:bg-white/[0.04]"
              >
                <span>Weitere Optionen</span>
                <span className="text-zinc-500">{moreOpen ? '▴' : '▾'}</span>
              </button>
              {moreOpen ? (
                <div className="space-y-2 border-t border-white/[0.06] px-3 py-3">
                  <BigButton
                    variant="secondary"
                    type="button"
                    disabled={dlBusy || officeBusy}
                    onClick={() => void doDownloadPdf()}
                  >
                    {dlBusy ? '…' : 'PDF herunterladen'}
                  </BigButton>
                </div>
              ) : null}
            </div>
          </>
        ) : null}
        {dlErr ? <p className="text-center text-sm text-red-400">{dlErr}</p> : null}

        {savedId ? (
          <div className="pt-2 text-center">
            <Link className="text-sm font-medium text-orange-400 hover:underline" to="/protokolle">
              Zu den gespeicherten Protokollen
            </Link>
          </div>
        ) : (
          <div className="pt-2 text-center">
            <button
              type="button"
              className="text-sm font-medium text-zinc-500 hover:text-zinc-300"
              onClick={() => nav('/protokoll/neu', { state: { mode: st.mode, date: st.date } })}
            >
              Zurück zur Erfassung
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
