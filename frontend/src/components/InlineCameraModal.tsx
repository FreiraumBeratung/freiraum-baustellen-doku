import { useCallback, useEffect, useRef, useState } from 'react'
import { BigButton } from './ui'
import { isAndroidDevice } from '../utils/isAndroidDevice'

type InlineCameraModalProps = {
  open: boolean
  onClose: () => void
  onCapture: (file: File) => void
  /** Optional: Titel oben (Default: Baustellenfoto). */
  title?: string
  /**
   * Höhere Kamera-Auflösung anfordern (z. B. Lieferschein-Scan).
   * Default false — bestehende Aufrufe (Bericht, Feedback) unverändert.
   */
  highRes?: boolean
}

type ImageCaptureLike = {
  takePhoto: (photoSettings?: Record<string, number>) => Promise<Blob>
  getPhotoCapabilities?: () => Promise<{
    imageWidth?: { min?: number; max?: number }
    imageHeight?: { min?: number; max?: number }
  }>
}

function getImageCaptureCtor(): (new (track: MediaStreamTrack) => ImageCaptureLike) | null {
  const w = window as unknown as { ImageCapture?: new (track: MediaStreamTrack) => ImageCaptureLike }
  return w.ImageCapture ?? null
}

function videoConstraintAttempts(highRes: boolean): MediaTrackConstraints[] {
  if (!highRes) {
    return [{ facingMode: { ideal: 'environment' } }]
  }

  // Portrait zuerst: Dokumente werden hochkant fotografiert.
  // Android Chrome liefert bei Landscape-Ideals oft nur Preview (~1080p).
  const portraitFirst: MediaTrackConstraints[] = [
    {
      facingMode: { ideal: 'environment' },
      width: { ideal: 2160 },
      height: { ideal: 3840 },
    },
    {
      facingMode: { ideal: 'environment' },
      width: { ideal: 1440 },
      height: { ideal: 2560 },
    },
    {
      facingMode: { ideal: 'environment' },
      width: { ideal: 1080 },
      height: { ideal: 1920 },
    },
  ]

  const landscape: MediaTrackConstraints[] = [
    {
      facingMode: { ideal: 'environment' },
      width: { ideal: 3840 },
      height: { ideal: 2160 },
    },
    {
      facingMode: { ideal: 'environment' },
      width: { ideal: 1920 },
      height: { ideal: 1080 },
    },
  ]

  const fallback: MediaTrackConstraints[] = [{ facingMode: { ideal: 'environment' } }]

  // Android: Portrait-Constraints zuerst; iOS: Landscape + Portrait gemischt ok
  if (isAndroidDevice()) {
    return [...portraitFirst, ...landscape, ...fallback]
  }
  return [...landscape, ...portraitFirst, ...fallback]
}

async function openCameraStream(highRes: boolean): Promise<MediaStream> {
  const attempts = videoConstraintAttempts(highRes)
  let lastErr: unknown
  for (const video of attempts) {
    try {
      return await navigator.mediaDevices.getUserMedia({ video, audio: false })
    } catch (err) {
      lastErr = err
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error('Kamera nicht verfügbar')
}

/** Nach Stream-Start: maximal mögliche Video-Auflösung anfordern (highRes). */
async function upgradeTrackResolution(track: MediaStreamTrack): Promise<void> {
  try {
    const caps = track.getCapabilities?.() as
      | { width?: { max?: number }; height?: { max?: number } }
      | undefined
    if (!caps?.width?.max || !caps?.height?.max) return

    const maxW = caps.width.max
    const maxH = caps.height.max
    const settings = track.getSettings?.() ?? {}
    const curW = settings.width ?? 0
    const curH = settings.height ?? 0
    // Schon nah am Maximum → nichts tun
    if (curW >= maxW * 0.9 && curH >= maxH * 0.9) return

    await track.applyConstraints({
      width: { ideal: maxW },
      height: { ideal: maxH },
    })
  } catch {
    // Gerät unterstützt applyConstraints nicht — Preview behalten
  }
}

async function captureStillBlob(
  video: HTMLVideoElement,
  track: MediaStreamTrack | null,
  highRes: boolean,
  jpegQuality: number,
): Promise<Blob> {
  // Android/Chrome: ImageCapture.takePhoto() = echte Still-Auflösung (nicht Video-Preview).
  // iOS Safari: oft nicht verfügbar → Canvas-Fallback.
  if (highRes && track) {
    const ImageCaptureCtor = getImageCaptureCtor()
    if (ImageCaptureCtor) {
      try {
        const ic = new ImageCaptureCtor(track)
        let photoSettings: Record<string, number> | undefined
        try {
          const photoCaps = await ic.getPhotoCapabilities?.()
          const maxW = photoCaps?.imageWidth?.max
          const maxH = photoCaps?.imageHeight?.max
          if (typeof maxW === 'number' && typeof maxH === 'number' && maxW > 0 && maxH > 0) {
            photoSettings = { imageWidth: maxW, imageHeight: maxH }
          }
        } catch {
          photoSettings = undefined
        }
        const still = photoSettings ? await ic.takePhoto(photoSettings) : await ic.takePhoto()
        if (still && still.size > 0) return still
      } catch {
        // Fallback auf Video-Frame
      }
    }
  }

  const w = video.videoWidth
  const h = video.videoHeight
  if (!w || !h) throw new Error('Kein Kamerabild')

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas nicht verfügbar')
  ctx.drawImage(video, 0, 0, w, h)

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error('Aufnahme fehlgeschlagen'))),
      'image/jpeg',
      jpegQuality,
    )
  })
  return blob
}

/** Inline-Kamera in der PWA — kein Wechsel zur nativen iOS-Kamera-App. */
export function InlineCameraModal({
  open,
  onClose,
  onCapture,
  title = 'Baustellenfoto',
  highRes = false,
}: InlineCameraModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [err, setErr] = useState('')
  const [ready, setReady] = useState(false)
  const [capturing, setCapturing] = useState(false)

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setReady(false)
  }, [])

  useEffect(() => {
    if (!open) {
      stopStream()
      setErr('')
      setCapturing(false)
      return
    }

    let cancelled = false

    async function start() {
      setErr('')
      setReady(false)
      if (!navigator.mediaDevices?.getUserMedia) {
        setErr('Kamera in diesem Browser nicht verfügbar. Bitte „Aus Galerie“ nutzen.')
        return
      }
      try {
        const stream = await openCameraStream(highRes)
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }

        if (highRes) {
          const vTrack = stream.getVideoTracks()[0]
          if (vTrack) await upgradeTrackResolution(vTrack)
        }

        streamRef.current = stream
        const video = videoRef.current
        if (video) {
          video.srcObject = stream
          await video.play()
          // Kurz warten, bis videoWidth/Height stehen (Android)
          if (highRes) {
            await new Promise<void>((r) => {
              window.setTimeout(r, 120)
            })
          }
          setReady(true)
        }
      } catch {
        setErr('Kamera-Zugriff verweigert oder nicht verfügbar. Bitte „Aus Galerie“ nutzen.')
      }
    }

    void start()
    return () => {
      cancelled = true
      stopStream()
    }
  }, [open, highRes, stopStream])

  function handleClose() {
    stopStream()
    onClose()
  }

  async function handleCapture() {
    const video = videoRef.current
    if (!video || !ready || capturing) return

    setCapturing(true)
    setErr('')
    try {
      const track = streamRef.current?.getVideoTracks()[0] ?? null
      const jpegQuality = highRes ? 0.95 : 0.92
      const blob = await captureStillBlob(video, track, highRes, jpegQuality)
      const filePrefix = highRes ? 'lieferschein' : 'baustelle'
      const ext = blob.type === 'image/png' ? 'png' : 'jpg'
      const file = new File([blob], `${filePrefix}-${Date.now()}.${ext}`, {
        type: blob.type || 'image/jpeg',
        lastModified: Date.now(),
      })
      stopStream()
      onCapture(file)
      onClose()
    } catch {
      setErr('Aufnahme fehlgeschlagen. Bitte erneut versuchen oder Galerie nutzen.')
    } finally {
      setCapturing(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[110] flex flex-col bg-zinc-950">
      <div className="safe-area-pt-min flex items-center justify-between px-4 py-3">
        <p className="text-sm font-medium text-white">{title}</p>
        <button
          type="button"
          className="rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:text-white"
          onClick={handleClose}
          disabled={capturing}
        >
          Schließen
        </button>
      </div>

      <div className="relative min-h-0 flex-1 bg-black">
        <video
          ref={videoRef}
          className="h-full w-full object-cover"
          playsInline
          muted
          autoPlay
        />
        {!ready && !err ? (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-zinc-400">
            Kamera wird gestartet…
          </div>
        ) : null}
        {capturing ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 text-sm text-white">
            Aufnahme…
          </div>
        ) : null}
      </div>

      {err ? <p className="px-4 py-2 text-center text-sm text-red-400">{err}</p> : null}

      <div className="safe-area-pb flex gap-3 px-4 py-4">
        <BigButton
          type="button"
          variant="secondary"
          className="flex-1"
          onClick={handleClose}
          disabled={capturing}
        >
          Abbrechen
        </BigButton>
        <BigButton
          type="button"
          className="flex-1"
          disabled={!ready || capturing}
          onClick={() => void handleCapture()}
        >
          {capturing ? '…' : 'Aufnahme'}
        </BigButton>
      </div>
    </div>
  )
}
