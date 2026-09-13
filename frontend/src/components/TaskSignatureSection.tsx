import { useCallback, useEffect, useState } from 'react'
import {
  deleteTaskSignature,
  listTaskSignature,
  resolveBackendPublicUrl,
  uploadTaskSignature,
  type ReportSignature,
} from '../api/client'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { SignaturePad } from './SignaturePad'

export function TaskSignatureSection({
  taskId,
  signedByLabel,
  onChanged,
}: {
  taskId: string
  signedByLabel?: string
  onChanged?: () => void
}) {
  const { writeBlocked } = useWriteBlocked()
  const [signature, setSignature] = useState<ReportSignature | null>(null)
  const [open, setOpen] = useState(false)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [padKey, setPadKey] = useState(0)

  const refresh = useCallback(async () => {
    const res = await listTaskSignature(taskId)
    setSignature(res.signature)
  }, [taskId])

  useEffect(() => {
    setErr('')
    void refresh().catch(() => setErr('Unterschrift konnte nicht geladen werden.'))
  }, [refresh])

  async function handleConfirm(file: File) {
    if (writeBlocked || busy) return
    setBusy(true)
    setErr('')
    try {
      const res = await uploadTaskSignature(taskId, file, signedByLabel)
      setSignature(res.signature)
      setPadKey((k) => k + 1)
      onChanged?.()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Unterschrift fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  async function handleRedo() {
    if (writeBlocked || busy) return
    setBusy(true)
    setErr('')
    try {
      await deleteTaskSignature(taskId)
      setSignature(null)
      setPadKey((k) => k + 1)
      onChanged?.()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Unterschrift konnte nicht entfernt werden.')
    } finally {
      setBusy(false)
    }
  }

  const src = signature ? resolveBackendPublicUrl(signature.url) ?? signature.url ?? '' : ''

  return (
    <div className="border-t border-white/[0.06] pt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 text-left"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold uppercase tracking-wide text-orange-400">
          Unterschrift (optional){signature ? ' (1)' : ''}
        </span>
        <span className="text-xs text-zinc-500">{open ? '▲' : '▼'}</span>
      </button>
      {open ? (
        <div className="mt-3 space-y-3">
          {signature && src ? (
            <div className="rounded-xl border border-zinc-700 bg-zinc-950/60 p-3">
              <div className="flex items-start justify-between gap-3">
                <p className="text-xs text-zinc-400">
                  {signature.signedByLabel ? `${signature.signedByLabel} · ` : ''}Unterschrift erfasst
                </p>
                <button
                  type="button"
                  disabled={busy || writeBlocked}
                  onClick={() => void handleRedo()}
                  className="shrink-0 rounded-lg border border-zinc-600 px-2.5 py-1.5 text-xs text-zinc-300 hover:border-orange-500/60 hover:text-orange-200 disabled:opacity-40"
                >
                  Erneut
                </button>
              </div>
              <img
                src={src}
                alt="Unterschrift zur Aufgabe"
                className="mt-3 w-full rounded-lg border border-zinc-700 bg-white object-contain"
                style={{ maxHeight: '120px' }}
              />
            </div>
          ) : (
            <SignaturePad
              key={padKey}
              title="Abnahme / Nachweis"
              hint="Optional — hier mit dem Finger unterschreiben."
              disabled={busy || writeBlocked}
              onConfirm={(file) => void handleConfirm(file)}
            />
          )}
          {err ? <p className="text-sm text-red-400">{err}</p> : null}
        </div>
      ) : null}
    </div>
  )
}
