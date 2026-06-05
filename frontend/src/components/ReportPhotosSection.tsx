import { useCallback, useEffect, useRef, useState } from 'react'
import {
  deleteReportPhoto,
  listReportPhotos,
  resolveBackendPublicUrl,
  uploadReportPhoto,
  type ReportPhoto,
} from '../api/client'
import { useMobilePwaRepaint } from '../hooks/useMobilePwaRepaint'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { InlineCameraModal } from './InlineCameraModal'
import { PhotoUploadOverlay, type PhotoUploadOverlayMode } from './PhotoUploadOverlay'
import { compressImageForUpload } from '../utils/compressImage'
import { iosHardRedirectAfterPhotoUpload } from '../utils/iosPhotoRedirect'
import { isIosDevice } from '../utils/isIosDevice'
import { setPhotoUploadBusy } from '../utils/photoUploadBusy'
import { forcePwaRepaint, wakePageAfterPhotoUpload, yieldForPaint } from '../utils/pwaRepaint'
import { BigButton } from './ui'

type PhotoSource = 'gallery' | 'inline-camera'

type ReportPhotosSectionProps = {
  reportId: string | null
  /** Wenn false: Hinweis statt Upload (Bericht noch nicht gespeichert). */
  enabled: boolean
  /** Wird nach erfolgreichem Upload aufgerufen (Seite kurz „wecken“). */
  onUploadComplete?: () => void
  /** iOS: nach erfolgreichem Upload hart zur Detailseite (Kamera + Galerie). */
  iosGalleryRedirect?: boolean
  /** Toggle initial geoeffnet (z.B. nach iOS-Redirect). */
  initialOpen?: boolean
  /** In Detail-Karte eingebettet — ohne oberen Trennstrich. */
  embedded?: boolean
}

type UploadPhase = 'idle' | 'preparing' | 'uploading'

export function ReportPhotosSection({
  reportId,
  enabled,
  onUploadComplete,
  iosGalleryRedirect = false,
  initialOpen = false,
  embedded = false,
}: ReportPhotosSectionProps) {
  useMobilePwaRepaint()
  const { writeBlocked } = useWriteBlocked()
  const uploadsEnabled = enabled && !writeBlocked

  const [photos, setPhotos] = useState<ReportPhoto[]>([])
  const [maxPhotos, setMaxPhotos] = useState(10)
  const [open, setOpen] = useState(initialOpen)
  const [phase, setPhase] = useState<UploadPhase>('idle')
  const [overlayMode, setOverlayMode] = useState<PhotoUploadOverlayMode>('off')
  const [statusLine, setStatusLine] = useState('')
  const [err, setErr] = useState('')
  const [inlineCameraOpen, setInlineCameraOpen] = useState(false)
  const galleryRef = useRef<HTMLInputElement>(null)
  const pickerPendingRef = useRef(false)
  const processingRef = useRef(false)
  const pickerCancelTimerRef = useRef<number | null>(null)

  const clearPickerCancelTimer = useCallback(() => {
    if (pickerCancelTimerRef.current != null) {
      window.clearTimeout(pickerCancelTimerRef.current)
      pickerCancelTimerRef.current = null
    }
  }, [])

  const busy = overlayMode !== 'off' || phase !== 'idle' || inlineCameraOpen
  const count = photos.length
  const atLimit = count >= maxPhotos

  const beginOverlay = useCallback((message: string) => {
    setOverlayMode('active')
    setPhase('preparing')
    setStatusLine(message)
    setPhotoUploadBusy(true)
    forcePwaRepaint()
  }, [])

  const closeOverlaySoft = useCallback(
    async (opts: { success?: boolean; message?: string; source?: PhotoSource } = {}) => {
      const shouldIosHardRedirect =
        Boolean(opts.success) &&
        iosGalleryRedirect &&
        isIosDevice() &&
        reportId &&
        (opts.source === 'gallery' || opts.source === 'inline-camera')

      if (shouldIosHardRedirect) {
        setPhase('idle')
        setStatusLine(opts.message ?? 'Foto übernommen.')
        setOverlayMode('success')
        await yieldForPaint(600)
        setPhotoUploadBusy(false)
        iosHardRedirectAfterPhotoUpload(reportId)
        return
      }

      if (opts.success) {
        setPhase('idle')
        setStatusLine(opts.message ?? 'Foto übernommen.')
        setOverlayMode('success')
        await yieldForPaint(520)
      }
      setOverlayMode('closing')
      await yieldForPaint(340)
      setOverlayMode('off')
      setPhase('idle')
      setPhotoUploadBusy(false)

      await wakePageAfterPhotoUpload()
      if (opts.success) {
        onUploadComplete?.()
      }
      forcePwaRepaint()
    },
    [iosGalleryRedirect, onUploadComplete, reportId],
  )

  const abortOverlay = useCallback(async () => {
    setStatusLine('')
    setOverlayMode('closing')
    await yieldForPaint(280)
    setOverlayMode('off')
    setPhase('idle')
    setPhotoUploadBusy(false)
    forcePwaRepaint()
  }, [])

  const refresh = useCallback(async () => {
    if (!reportId || !enabled) return
    const res = await listReportPhotos(reportId)
    setPhotos(res.photos)
    setMaxPhotos(res.maxPhotos)
  }, [reportId, enabled])

  useEffect(() => {
    if (initialOpen && enabled) setOpen(true)
  }, [initialOpen, enabled])

  useEffect(() => {
    if (!reportId || !enabled) {
      setPhotos([])
      if (!initialOpen) setOpen(false)
      return
    }
    setErr('')
    void refresh().catch(() => {
      setErr('Fotos konnten nicht geladen werden.')
    })
  }, [reportId, enabled, refresh, initialOpen])

  useEffect(() => {
    if (count > 0 && enabled) setOpen(true)
  }, [count, enabled])

  useEffect(() => {
    return () => {
      clearPickerCancelTimer()
      pickerPendingRef.current = false
      processingRef.current = false
      setPhotoUploadBusy(false)
    }
  }, [clearPickerCancelTimer])

  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState !== 'visible') return
      if (!pickerPendingRef.current || processingRef.current) return
      beginOverlay('Foto wird übernommen…')
      forcePwaRepaint()
      clearPickerCancelTimer()
      pickerCancelTimerRef.current = window.setTimeout(() => {
        if (!processingRef.current && pickerPendingRef.current) {
          pickerPendingRef.current = false
          void abortOverlay()
        }
      }, 5000)
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [abortOverlay, beginOverlay, clearPickerCancelTimer])

  function openInlineCamera() {
    if (busy || atLimit || writeBlocked) return
    setInlineCameraOpen(true)
  }

  function openGalleryPicker() {
    if (busy || atLimit || writeBlocked) return
    pickerPendingRef.current = true
    window.setTimeout(() => galleryRef.current?.click(), 80)
  }

  async function processFiles(files: File[], source: PhotoSource) {
    if (!reportId || !uploadsEnabled || !files.length || processingRef.current) return

    processingRef.current = true
    pickerPendingRef.current = false
    clearPickerCancelTimer()
    setErr('')

    beginOverlay('Foto wird übernommen…')

    try {
      await yieldForPaint(200)
      forcePwaRepaint()

      let currentCount = photos.length
      for (let i = 0; i < files.length; i++) {
        if (currentCount >= maxPhotos) break

        setPhase('preparing')
        setStatusLine(
          files.length > 1
            ? `Foto ${i + 1}/${files.length} wird vorbereitet…`
            : 'Foto wird vorbereitet…',
        )
        await yieldForPaint(60)

        const prepared = await compressImageForUpload(files[i]!)
        setPhase('uploading')
        setStatusLine(
          files.length > 1
            ? `Foto ${i + 1}/${files.length} wird hochgeladen…`
            : 'Foto wird hochgeladen…',
        )

        const res = await uploadReportPhoto(reportId, prepared)
        setPhotos(res.photos)
        setMaxPhotos(res.maxPhotos)
        currentCount = res.count
      }

      await closeOverlaySoft({ success: true, message: 'Foto übernommen.', source })
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Foto konnte nicht hochgeladen werden.')
      setStatusLine('')
      await abortOverlay()
    } finally {
      processingRef.current = false
      pickerPendingRef.current = false
      if (galleryRef.current) galleryRef.current.value = ''
    }
  }

  function handleGalleryFiles(fileList: FileList | null) {
    if (!reportId || !uploadsEnabled || processingRef.current) return
    if (!fileList?.length) {
      pickerPendingRef.current = false
      clearPickerCancelTimer()
      if (!processingRef.current) void abortOverlay()
      return
    }
    void processFiles(Array.from(fileList), 'gallery')
  }

  function handleInlineCapture(file: File) {
    void processFiles([file], 'inline-camera')
  }

  async function removePhoto(photoId: string) {
    if (!reportId || busy || writeBlocked) return
    setErr('')
    setStatusLine('')
    beginOverlay('Foto wird entfernt…')
    setPhase('uploading')
    try {
      const res = await deleteReportPhoto(reportId, photoId)
      setPhotos((prev) => prev.filter((p) => p.id !== photoId))
      if (res.count === 0) setOpen(false)
      await closeOverlaySoft({ success: true, message: 'Foto entfernt.', source: 'inline-camera' })
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Foto konnte nicht entfernt werden.')
      await abortOverlay()
    }
  }

  const overlayMessage =
    statusLine ||
    (phase === 'uploading' ? 'Foto wird hochgeladen…' : 'Foto wird übernommen…')

  const sectionClass = embedded ? 'pt-0' : 'border-t border-zinc-800 pt-4'

  return (
    <>
      <InlineCameraModal
        open={inlineCameraOpen}
        onClose={() => setInlineCameraOpen(false)}
        onCapture={handleInlineCapture}
      />
      <PhotoUploadOverlay mode={overlayMode} message={overlayMessage} />

      <section className={sectionClass}>
        <button
          type="button"
          disabled={!enabled}
          onClick={() => enabled && setOpen((v) => !v)}
          className="flex w-full items-center justify-between gap-2 text-left disabled:cursor-default disabled:opacity-60"
          aria-expanded={open}
        >
          <span className="text-sm font-semibold uppercase tracking-wide text-orange-400">
            Baustellenfotos
            {enabled ? ` (${count}/${maxPhotos})` : ''}
          </span>
          {enabled ? (
            <span className="text-xs text-zinc-500">{open ? '▲' : '▼'}</span>
          ) : null}
        </button>

        {!enabled ? (
          <p className="mt-2 text-xs text-zinc-500">Bericht zuerst speichern, dann Fotos hinzufügen.</p>
        ) : null}

        {enabled && open ? (
          <div className="mt-3 space-y-3">
            <p className="text-xs text-zinc-500">
              Baustelle und Arbeit dokumentieren — max. {maxPhotos} Fotos. Große Bilder werden automatisch
              verkleinert.
            </p>

            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                ref={galleryRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/*"
                multiple
                className="sr-only"
                disabled={busy || atLimit || writeBlocked}
                onChange={(e) => handleGalleryFiles(e.target.files)}
              />
              <BigButton
                type="button"
                variant="secondary"
                className="!py-2 text-sm"
                disabled={busy || atLimit || writeBlocked}
                onClick={openInlineCamera}
              >
                {busy ? '…' : 'Foto aufnehmen'}
              </BigButton>
              <BigButton
                type="button"
                variant="secondary"
                className="!py-2 text-sm"
                disabled={busy || atLimit || writeBlocked}
                onClick={openGalleryPicker}
              >
                {busy ? '…' : 'Aus Galerie'}
              </BigButton>
            </div>

            {writeBlocked ? (
              <p className="text-xs text-amber-400/90">Neue Fotos sind bei pausiertem Zugang nicht möglich.</p>
            ) : null}

            {atLimit ? (
              <p className="text-xs text-amber-400/90">Maximum erreicht ({maxPhotos} Fotos).</p>
            ) : null}

            {photos.length ? (
              <ul className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                {photos.map((photo) => {
                  const src = resolveBackendPublicUrl(photo.url) ?? photo.url ?? ''
                  return (
                    <li
                      key={photo.id}
                      className="relative aspect-square overflow-hidden rounded-lg border border-zinc-700 bg-zinc-950"
                    >
                      {src ? (
                        <img
                          src={src}
                          alt={photo.originalFilename || 'Baustellenfoto'}
                          className="h-full w-full object-cover"
                          loading="lazy"
                          decoding="async"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-xs text-zinc-600">Foto</div>
                      )}
                      <button
                        type="button"
                        disabled={busy || writeBlocked}
                        aria-label="Foto entfernen"
                        className="absolute right-1 top-1 rounded-md bg-black/70 px-1.5 py-0.5 text-xs text-zinc-200 hover:bg-red-900/80 disabled:opacity-40"
                        onClick={() => void removePhoto(photo.id)}
                      >
                        ✕
                      </button>
                    </li>
                  )
                })}
              </ul>
            ) : (
              <p className="text-sm text-zinc-500">Noch keine Fotos.</p>
            )}

            {overlayMode === 'off' && !busy && statusLine && !err ? (
              <p className="text-sm text-emerald-400/90">{statusLine}</p>
            ) : null}

            {err ? <p className="text-sm text-red-400">{err}</p> : null}
          </div>
        ) : null}
      </section>
    </>
  )
}
