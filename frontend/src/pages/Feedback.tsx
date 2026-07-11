import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { InlineCameraModal } from '../components/InlineCameraModal'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'
import { sendFeedback, type FeedbackCategory } from '../api/client'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

const CATEGORY_OPTIONS: FeedbackCategory[] = ['Problem', 'Verbesserung', 'Lob']
const MAX_FEEDBACK_PHOTOS = 3

export type FeedbackNavState = {
  category?: FeedbackCategory
  reportId?: string
  reportLabel?: string
  prefill?: string
}

type PendingPhoto = {
  id: string
  file: File
  previewUrl: string
}

function appVersionLabel(): string {
  const v = (import.meta.env.VITE_APP_VERSION as string | undefined)?.trim()
  return v || 'web'
}

export function FeedbackPage() {
  const location = useLocation()
  const navState = (location.state ?? null) as FeedbackNavState | null
  const { writeBlocked } = useWriteBlocked()
  const [category, setCategory] = useState<FeedbackCategory>(navState?.category ?? 'Verbesserung')
  const [text, setText] = useState(navState?.prefill ?? '')
  const [reportId, setReportId] = useState(navState?.reportId ?? '')
  const [reportLabel, setReportLabel] = useState(navState?.reportLabel ?? '')
  const [photos, setPhotos] = useState<PendingPhoto[]>([])
  const [cameraOpen, setCameraOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastSentAt, setLastSentAt] = useState<string | null>(null)
  const galleryRef = useRef<HTMLInputElement>(null)
  const photosRef = useRef(photos)
  photosRef.current = photos
  const charsLeft = useMemo(() => 1000 - text.length, [text.length])

  useEffect(() => {
    return () => {
      photosRef.current.forEach((p) => URL.revokeObjectURL(p.previewUrl))
    }
  }, [])

  function addPhoto(file: File) {
    if (photos.length >= MAX_FEEDBACK_PHOTOS) return
    const id = crypto.randomUUID()
    setPhotos((prev) => [
      ...prev,
      { id, file, previewUrl: URL.createObjectURL(file) },
    ])
  }

  function removePhoto(id: string) {
    setPhotos((prev) => {
      const target = prev.find((p) => p.id === id)
      if (target) URL.revokeObjectURL(target.previewUrl)
      return prev.filter((p) => p.id !== id)
    })
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (writeBlocked || busy) return
    const msg = text.trim()
    if (msg.length < 3) {
      setError('Bitte mindestens 3 Zeichen eingeben.')
      setMessage(null)
      return
    }
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const res = await sendFeedback({
        category,
        message: msg,
        page: window.location.pathname,
        appVersion: appVersionLabel(),
        reportId: reportId || undefined,
        files: photos.map((p) => p.file),
      })
      const sentAt = new Date()
      setLastSentAt(
        `${sentAt.toLocaleDateString('de-DE')} um ${sentAt.toLocaleTimeString('de-DE', {
          hour: '2-digit',
          minute: '2-digit',
        })}`,
      )
      setMessage(res.message || 'Danke! Feedback wurde gesendet.')
      setText('')
      setCategory('Verbesserung')
      setReportId('')
      setReportLabel('')
      photos.forEach((p) => URL.revokeObjectURL(p.previewUrl))
      setPhotos([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Feedback konnte nicht gesendet werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageTitle title="Feedback" subtitle="Direkt aus der App senden" />

      <Card className="border-transparent bg-black/40 py-8 shadow-none ring-1 ring-white/[0.08]">
        <form onSubmit={onSubmit} className="space-y-5">
          {reportId ? (
            <div className="rounded-xl border border-orange-500/25 bg-orange-500/[0.08] px-3 py-2.5 text-sm text-orange-100/90">
              <p className="font-medium">Verknüpfter Bericht</p>
              <p className="mt-1 text-orange-200/80">{reportLabel || reportId}</p>
              <button
                type="button"
                className="mt-2 text-xs text-orange-300/80 underline"
                onClick={() => {
                  setReportId('')
                  setReportLabel('')
                }}
                disabled={busy || writeBlocked}
              >
                Verknüpfung entfernen
              </button>
            </div>
          ) : null}

          <div>
            <p className="text-sm text-zinc-400">Kategorie</p>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {CATEGORY_OPTIONS.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setCategory(opt)}
                  className={`min-h-11 rounded-xl border px-2 text-sm font-semibold transition ${
                    category === opt
                      ? 'border-orange-500/55 bg-orange-500/15 text-orange-200'
                      : 'border-white/[0.1] bg-black/45 text-zinc-300 hover:border-zinc-500/60 hover:text-zinc-100'
                  }`}
                  disabled={busy || writeBlocked}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          <label className="block">
            <span className="text-sm text-zinc-400">Dein Feedback</span>
            <textarea
              className="mt-2 min-h-[180px] w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              placeholder="Was war gut, was war schlecht, was sollten wir verbessern?"
              value={text}
              onChange={(e) => setText(e.target.value.slice(0, 1000))}
              disabled={busy || writeBlocked}
            />
            <p className="mt-2 text-right text-xs text-zinc-500">{charsLeft} Zeichen übrig</p>
          </label>

          <div>
            <p className="text-sm text-zinc-400">Screenshots / Fotos (optional)</p>
            <p className="mt-1 text-xs text-zinc-500">
              Bis zu {MAX_FEEDBACK_PHOTOS} Bilder — z. B. Screenshot vom Handy, wenn etwas falsch erkannt wurde.
            </p>
            {photos.length > 0 ? (
              <div className="mt-3 grid grid-cols-3 gap-2">
                {photos.map((p) => (
                  <div key={p.id} className="relative aspect-square overflow-hidden rounded-xl ring-1 ring-white/[0.1]">
                    <img src={p.previewUrl} alt="" className="h-full w-full object-cover" />
                    <button
                      type="button"
                      aria-label="Foto entfernen"
                      className="absolute right-1 top-1 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-sm text-white"
                      onClick={() => removePhoto(p.id)}
                      disabled={busy || writeBlocked}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            ) : null}
            {photos.length < MAX_FEEDBACK_PHOTOS ? (
              <div className="mt-3 flex flex-wrap gap-2">
                <BigButton
                  type="button"
                  variant="secondary"
                  className="min-h-11 flex-1 px-3 text-sm"
                  disabled={busy || writeBlocked}
                  onClick={() => setCameraOpen(true)}
                >
                  Foto aufnehmen
                </BigButton>
                <BigButton
                  type="button"
                  variant="secondary"
                  className="min-h-11 flex-1 px-3 text-sm"
                  disabled={busy || writeBlocked}
                  onClick={() => galleryRef.current?.click()}
                >
                  Aus Galerie
                </BigButton>
                <input
                  ref={galleryRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/*"
                  className="sr-only"
                  multiple
                  onChange={(e) => {
                    const list = e.target.files
                    if (!list) return
                    let remaining = MAX_FEEDBACK_PHOTOS - photos.length
                    for (const file of Array.from(list)) {
                      if (remaining <= 0) break
                      addPhoto(file)
                      remaining -= 1
                    }
                    e.target.value = ''
                  }}
                  disabled={busy || writeBlocked}
                />
              </div>
            ) : null}
          </div>

          {message ? <p className="text-sm text-orange-300">{message}</p> : null}
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          {lastSentAt ? <p className="text-xs text-zinc-500">Feedback gesendet am {lastSentAt}</p> : null}

          <BigButton type="submit" disabled={busy || writeBlocked}>
            {busy ? 'Wird gesendet…' : 'Feedback senden'}
          </BigButton>
        </form>
      </Card>

      <InlineCameraModal
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onCapture={(file) => addPhoto(file)}
      />

      <div className="mt-8">
        <PoweredBy />
      </div>
    </div>
  )
}
