import { useCallback, useEffect, useState } from 'react'
import {
  deleteProtocolSignature,
  deleteReportSignature,
  listProtocolSignatures,
  listReportSignatures,
  resolveBackendPublicUrl,
  uploadProtocolSignature,
  uploadReportSignature,
  type ReportSignature,
  type SignatureRole,
} from '../api/client'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { SignaturePad } from './SignaturePad'

type ReportSignaturesSectionProps = {
  reportId: string | null
  protocolId?: string | null
  /** Wenn false: Hinweis statt Unterschrift (Bericht noch nicht gespeichert). */
  enabled: boolean
  /** Optional fuer signedByLabel bei Kunden-Signatur. */
  customerName?: string
  /** In Detail-Karte eingebettet — ohne oberen Trennstrich. */
  embedded?: boolean
  /** Toggle initial geoeffnet (z.B. per URL ?signatures=1). */
  initialOpen?: boolean
}

type ActiveStep = 'customer' | 'employee' | 'complete'

function stepFromSignatures(customer: ReportSignature | null, employee: ReportSignature | null): ActiveStep {
  if (!customer) return 'customer'
  if (!employee) return 'employee'
  return 'complete'
}

function SignaturePreview({
  label,
  signature,
  busy,
  onRedo,
}: {
  label: string
  signature: ReportSignature
  busy: boolean
  onRedo: () => void
}) {
  const src = resolveBackendPublicUrl(signature.url) ?? signature.url ?? ''
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-950/60 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-400/90">{label}</p>
          <p className="mt-1 text-xs text-zinc-500">Unterschrift erfasst</p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={onRedo}
          className="shrink-0 rounded-lg border border-zinc-600 px-2.5 py-1.5 text-xs text-zinc-300 hover:border-orange-500/60 hover:text-orange-200 disabled:opacity-40"
        >
          Erneut
        </button>
      </div>
      {src ? (
        <img
          src={src}
          alt={`${label} Unterschrift`}
          className="mt-3 w-full rounded-lg border border-zinc-700 bg-white object-contain"
          style={{ maxHeight: '120px' }}
        />
      ) : null}
    </div>
  )
}

export function ReportSignaturesSection({
  reportId,
  protocolId = null,
  enabled,
  customerName,
  embedded = false,
  initialOpen = false,
}: ReportSignaturesSectionProps) {
  const entityId = protocolId || reportId
  const isProtocol = Boolean(protocolId)
  const { writeBlocked } = useWriteBlocked()
  const signaturesEnabled = enabled && !writeBlocked
  const [customer, setCustomer] = useState<ReportSignature | null>(null)
  const [employee, setEmployee] = useState<ReportSignature | null>(null)
  const [open, setOpen] = useState(initialOpen)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [statusLine, setStatusLine] = useState('')
  const [padKey, setPadKey] = useState(0)

  const count = Number(Boolean(customer)) + Number(Boolean(employee))
  const step = stepFromSignatures(customer, employee)
  const labelCustomer = isProtocol ? 'Unternehmer' : 'Kunde'
  const labelEmployee = isProtocol ? 'Gesprächspartner' : 'Baustellenleitung / Mitarbeiter'
  const padTitleCustomer = isProtocol ? 'Unterschrift Unternehmer' : 'Kundenunterschrift'
  const padTitleEmployee = isProtocol ? 'Unterschrift Gesprächspartner' : 'Baustellenleitung / Mitarbeiter'
  const hintCustomer = isProtocol
    ? 'Bitte als Unternehmer hier unterschreiben.'
    : 'Bitte das Gerät an den Kunden übergeben — hier unterschreiben.'
  const hintEmployee = isProtocol
    ? 'Bitte als Gesprächspartner unterschreiben oder das Gerät übergeben.'
    : 'Jetzt selbst unterschreiben oder an die Baustellenleitung übergeben.'

  const refresh = useCallback(async () => {
    if (!entityId || !enabled) return
    const res = isProtocol ? await listProtocolSignatures(entityId) : await listReportSignatures(entityId)
    setCustomer(res.signatures.customer)
    setEmployee(res.signatures.employee)
  }, [entityId, enabled, isProtocol])

  useEffect(() => {
    if (!entityId || !enabled) {
      setCustomer(null)
      setEmployee(null)
      if (!enabled) setOpen(false)
      return
    }
    setErr('')
    void refresh().catch(() => {
      setErr('Unterschriften konnten nicht geladen werden.')
    })
  }, [entityId, enabled, refresh])

  useEffect(() => {
    if (initialOpen && enabled) setOpen(true)
  }, [initialOpen, enabled])

  useEffect(() => {
    if (count > 0 && enabled) setOpen(true)
  }, [count, enabled])

  async function handleUpload(role: SignatureRole, file: File) {
    if (!entityId || !signaturesEnabled || busy) return
    setBusy(true)
    setErr('')
    setStatusLine('Unterschrift wird gespeichert…')
    try {
      const label = role === 'customer' ? customerName?.trim() : undefined
      const res = isProtocol
        ? await uploadProtocolSignature(entityId, role, file, label || undefined)
        : await uploadReportSignature(entityId, role, file, label || undefined)
      setCustomer(res.signatures.customer)
      setEmployee(res.signatures.employee)
      setPadKey((k) => k + 1)
      setStatusLine(
        role === 'customer'
          ? isProtocol
            ? 'Unterschrift Unternehmer übernommen.'
            : 'Kundenunterschrift übernommen.'
          : isProtocol
            ? 'Unterschrift Gesprächspartner übernommen.'
            : 'Mitarbeiter-Unterschrift übernommen.',
      )
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Unterschrift konnte nicht gespeichert werden.')
      setStatusLine('')
    } finally {
      setBusy(false)
    }
  }

  async function handleRedo(role: SignatureRole) {
    if (!entityId || busy || writeBlocked) return
    setBusy(true)
    setErr('')
    setStatusLine('')
    try {
      const res = isProtocol
        ? await deleteProtocolSignature(entityId, role)
        : await deleteReportSignature(entityId, role)
      setCustomer(res.signatures.customer)
      setEmployee(res.signatures.employee)
      setPadKey((k) => k + 1)
      setStatusLine('')
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Unterschrift konnte nicht entfernt werden.')
    } finally {
      setBusy(false)
    }
  }

  const sectionClass = embedded ? 'pt-4' : 'border-t border-zinc-800 pt-4'

  return (
    <section className={sectionClass}>
      <button
        type="button"
        disabled={!enabled}
        onClick={() => enabled && setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 text-left disabled:cursor-default disabled:opacity-60"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold uppercase tracking-wide text-orange-400">
          Unterschriften
          {enabled ? ` (${count}/2)` : ''}
        </span>
        {enabled ? <span className="text-xs text-zinc-500">{open ? '▲' : '▼'}</span> : null}
      </button>

      {!enabled ? (
        <p className="mt-2 text-xs text-zinc-500">
          {isProtocol ? 'Protokoll zuerst speichern, dann Unterschriften erfassen.' : 'Bericht zuerst speichern, dann Unterschriften erfassen.'}
        </p>
      ) : null}

      {enabled && open ? (
        <div className="mt-3 space-y-4">
          <p className="text-xs text-zinc-500">
            {isProtocol
              ? 'Optional — zuerst Unternehmer, dann Gesprächspartner. Beide Schritte sind freiwillig.'
              : 'Optional — zuerst Kunde, dann Baustellenleitung oder Mitarbeiter. Beide Schritte sind freiwillig.'}
          </p>

          {writeBlocked ? (
            <p className="text-xs text-amber-400/90">Neue Unterschriften sind bei pausiertem Zugang nicht möglich.</p>
          ) : null}

          {customer ? (
            <SignaturePreview
              label={labelCustomer}
              signature={customer}
              busy={busy || writeBlocked}
              onRedo={() => void handleRedo('customer')}
            />
          ) : step === 'customer' && signaturesEnabled ? (
            <SignaturePad
              key={`customer-pad-${padKey}`}
              title={padTitleCustomer}
              hint={hintCustomer}
              disabled={busy}
              onConfirm={(file) => void handleUpload('customer', file)}
            />
          ) : null}

          {customer && !employee && step === 'employee' && signaturesEnabled ? (
            <SignaturePad
              key={`employee-pad-${padKey}`}
              title={padTitleEmployee}
              hint={hintEmployee}
              disabled={busy}
              onConfirm={(file) => void handleUpload('employee', file)}
            />
          ) : null}

          {employee ? (
            <SignaturePreview
              label={labelEmployee}
              signature={employee}
              busy={busy || writeBlocked}
              onRedo={() => void handleRedo('employee')}
            />
          ) : null}

          {step === 'complete' ? (
            <p className="text-sm text-emerald-400/90">Beide Unterschriften erfasst.</p>
          ) : null}

          {!busy && statusLine && !err ? <p className="text-sm text-emerald-400/90">{statusLine}</p> : null}
          {busy && statusLine ? <p className="text-sm text-zinc-400">{statusLine}</p> : null}
          {err ? <p className="text-sm text-red-400">{err}</p> : null}
        </div>
      ) : null}
    </section>
  )
}
