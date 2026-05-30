import { useCallback, useEffect, useRef, useState } from 'react'
import { BigButton } from './ui'

type InlineCameraModalProps = {
  open: boolean
  onClose: () => void
  onCapture: (file: File) => void
}

/** Inline-Kamera in der PWA — kein Wechsel zur nativen iOS-Kamera-App. */
export function InlineCameraModal({ open, onClose, onCapture }: InlineCameraModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [err, setErr] = useState('')
  const [ready, setReady] = useState(false)

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setReady(false)
  }, [])

  useEffect(() => {
    if (!open) {
      stopStream()
      setErr('')
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
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        })
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        const video = videoRef.current
        if (video) {
          video.srcObject = stream
          await video.play()
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
  }, [open, stopStream])

  function handleClose() {
    stopStream()
    onClose()
  }

  function handleCapture() {
    const video = videoRef.current
    if (!video || !ready) return
    const w = video.videoWidth
    const h = video.videoHeight
    if (!w || !h) return

    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, w, h)

    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const file = new File([blob], `baustelle-${Date.now()}.jpg`, {
          type: 'image/jpeg',
          lastModified: Date.now(),
        })
        stopStream()
        onCapture(file)
        onClose()
      },
      'image/jpeg',
      0.92,
    )
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[110] flex flex-col bg-zinc-950">
      <div className="safe-area-pt-min flex items-center justify-between px-4 py-3">
        <p className="text-sm font-medium text-white">Baustellenfoto</p>
        <button
          type="button"
          className="rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:text-white"
          onClick={handleClose}
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
      </div>

      {err ? <p className="px-4 py-2 text-center text-sm text-red-400">{err}</p> : null}

      <div className="safe-area-pb flex gap-3 px-4 py-4">
        <BigButton type="button" variant="secondary" className="flex-1" onClick={handleClose}>
          Abbrechen
        </BigButton>
        <BigButton type="button" className="flex-1" disabled={!ready} onClick={handleCapture}>
          Aufnahme
        </BigButton>
      </div>
    </div>
  )
}
