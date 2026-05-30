import { useCallback, useEffect, useState } from 'react'
import {
  deleteReportSignature,
  listReportSignatures,
  resolveBackendPublicUrl,
  uploadReportSignature,
  type ReportSignature,
  type SignatureRole,
} from '../api/client'
import { SignaturePad } from './SignaturePad'

type ReportSignaturesSectionProps = {
  reportId: string | null
  /** Wenn false: Hinweis statt Unterschrift (Bericht noch nicht gespeichert). */
  enabled: boolean
  /** Optional fuer signedByLabel bei Kunden-Signatur. */
  customerName?: string
  /** In Detail-Karte eingebettet — ohne oberen Trennstrich. */
  embedded?: boolean
  /** Toggle initial geoeffnet (z.B. nach iOS-Foto-Redirect). */
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
  enabled,
  customerName,
  embedded = false,
  initialOpen = false,
}: ReportSignaturesSectionProps) {
  const [customer, setCustomer] = useState<ReportSignature | null>(null)
  const [employee, setEmployee] = useState<ReportSignature | null>(null)
  const [open, setOpen] = useState(initialOpen)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [statusLine, setStatusLine] = useState('')
  const [padKey, setPadKey] = useState(0)

  const count = Number(Boolean(customer)) + Number(Boolean(employee))
  const step = stepFromSignatures(customer, employee)

  const refresh = useCallback(async () => {
    if (!reportId || !enabled) return
    const res = await listReportSignatures(reportId)
    setCustomer(res.signatures.customer)
    setEmployee(res.signatures.employee)
  }, [reportId, enabled])

  useEffect(() => {
    if (!reportId || !enabled) {
      setCustomer(null)
      setEmployee(null)
      if (!enabled) setOpen(false)
      return
    }
    setErr('')
    void refresh().catch(() => {
      setErr('Unterschriften konnten nicht geladen werden.')
    })
  }, [reportId, enabled, refresh])

  useEffect(() => {
    if (initialOpen && enabled) setOpen(true)
  }, [initialOpen, enabled])

  useEffect(() => {
    if (count > 0 && enabled) setOpen(true)
  }, [count, enabled])

  async function handleUpload(role: SignatureRole, file: File) {
    if (!reportId || !enabled || busy) return
    setBusy(true)
    setErr('')
    setStatusLine('Unterschrift wird gespeichert…')
    try {
      const label = role === 'customer' ? customerName?.trim() : undefined
      const res = await uploadReportSignature(reportId, role, file, label || undefined)
      setCustomer(res.signatures.customer)
      setEmployee(res.signatures.employee)
      setPadKey((k) => k + 1)
      setStatusLine(role === 'customer' ? 'Kundenunterschrift übernommen.' : 'Mitarbeiter-Unterschrift übernommen.')
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Unterschrift konnte nicht gespeichert werden.')
      setStatusLine('')
    } finally {
      setBusy(false)
    }
  }

  async function handleRedo(role: SignatureRole) {
    if (!reportId || busy) return
    setBusy(true)
    setErr('')
    setStatusLine('')
    try {
      const res = await deleteReportSignature(reportId, role)
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
        <p className="mt-2 text-xs text-zinc-500">Bericht zuerst speichern, dann Unterschriften erfassen.</p>
      ) : null}

      {enabled && open ? (
        <div className="mt-3 space-y-4">
          <p className="text-xs text-zinc-500">
            Optional — zuerst Kunde, dann Baustellenleitung oder Mitarbeiter. Beide Schritte sind freiwillig.
          </p>

          {customer ? (
            <SignaturePreview
              label="Kunde"
              signature={customer}
              busy={busy}
              onRedo={() => void handleRedo('customer')}
            />
          ) : step === 'customer' ? (
            <SignaturePad
              key={`customer-pad-${padKey}`}
              title="Kundenunterschrift"
              hint="Bitte das Gerät an den Kunden übergeben — hier unterschreiben."
              disabled={busy}
              onConfirm={(file) => void handleUpload('customer', file)}
            />
          ) : null}

          {customer && !employee && step === 'employee' ? (
            <SignaturePad
              key={`employee-pad-${padKey}`}
              title="Baustellenleitung / Mitarbeiter"
              hint="Jetzt selbst unterschreiben oder an die Baustellenleitung übergeben."
              disabled={busy}
              onConfirm={(file) => void handleUpload('employee', file)}
            />
          ) : null}

          {employee ? (
            <SignaturePreview
              label="Baustellenleitung / Mitarbeiter"
              signature={employee}
              busy={busy}
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
