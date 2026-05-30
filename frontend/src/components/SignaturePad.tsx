import { useCallback, useEffect, useRef, useState } from 'react'
import { BigButton } from './ui'

type SignaturePadProps = {
  title: string
  hint?: string
  disabled?: boolean
  /** Wird mit PNG-Datei aufgerufen, wenn der Nutzer „Übernehmen“ tippt. */
  onConfirm: (file: File) => void
  className?: string
}

const PAD_HEIGHT_PX = 220
const INK_COLOR = '#111827'
const BASE_LINE_WIDTH = 2.6

function fileFromCanvas(canvas: HTMLCanvasElement): Promise<File> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error('Signatur konnte nicht erzeugt werden.'))
          return
        }
        resolve(new File([blob], 'signature.png', { type: 'image/png' }))
      },
      'image/png',
      1,
    )
  })
}

/** Touch-Unterschriftenfeld im Stil eines digitalen Kassen-Pads. */
export function SignaturePad({
  title,
  hint = 'Hier mit dem Finger unterschreiben',
  disabled = false,
  onConfirm,
  className = '',
}: SignaturePadProps) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const drawingRef = useRef(false)
  const hasInkRef = useRef(false)
  const lastPointRef = useRef<{ x: number; y: number } | null>(null)
  const [hasInk, setHasInk] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const syncCanvasSize = useCallback(() => {
    const wrap = wrapRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return

    const dpr = Math.max(1, window.devicePixelRatio || 1)
    const width = Math.max(280, wrap.clientWidth)
    const height = PAD_HEIGHT_PX
    canvas.width = Math.round(width * dpr)
    canvas.height = Math.round(height * dpr)
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`

    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)
    ctx.strokeStyle = INK_COLOR
    ctx.lineWidth = BASE_LINE_WIDTH
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
  }, [])

  useEffect(() => {
    syncCanvasSize()
    const wrap = wrapRef.current
    if (!wrap || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(() => {
      if (!hasInkRef.current) syncCanvasSize()
    })
    ro.observe(wrap)
    return () => ro.disconnect()
  }, [syncCanvasSize])

  const markInk = useCallback(() => {
    if (!hasInkRef.current) {
      hasInkRef.current = true
      setHasInk(true)
    }
  }, [])

  const getPoint = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current!
    const rect = canvas.getBoundingClientRect()
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    }
  }, [])

  const drawLine = useCallback((from: { x: number; y: number }, to: { x: number; y: number }) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.beginPath()
    ctx.moveTo(from.x, from.y)
    ctx.lineTo(to.x, to.y)
    ctx.stroke()
    markInk()
  }, [markInk])

  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (disabled || busy) return
      e.preventDefault()
      e.currentTarget.setPointerCapture(e.pointerId)
      drawingRef.current = true
      const point = getPoint(e.clientX, e.clientY)
      lastPointRef.current = point
      setErr('')
    },
    [busy, disabled, getPoint],
  )

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!drawingRef.current || disabled || busy) return
      e.preventDefault()
      const point = getPoint(e.clientX, e.clientY)
      const last = lastPointRef.current
      if (last) drawLine(last, point)
      lastPointRef.current = point
    },
    [busy, disabled, drawLine, getPoint],
  )

  const handlePointerUp = useCallback((e: React.PointerEvent<HTMLCanvasElement>) => {
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId)
    }
    drawingRef.current = false
    lastPointRef.current = null
  }, [])

  const clearPad = useCallback(() => {
    hasInkRef.current = false
    setHasInk(false)
    setErr('')
    syncCanvasSize()
  }, [syncCanvasSize])

  async function handleConfirm() {
    const canvas = canvasRef.current
    if (!canvas || !hasInkRef.current || disabled || busy) return
    setBusy(true)
    setErr('')
    try {
      const file = await fileFromCanvas(canvas)
      onConfirm(file)
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Signatur konnte nicht übernommen werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className={`space-y-3 ${className}`.trim()}>
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">{title}</h3>
        {hint ? <p className="mt-1 text-xs text-zinc-500">{hint}</p> : null}
      </div>

      <div
        ref={wrapRef}
        className="overflow-hidden rounded-xl border border-zinc-600 bg-zinc-950 p-2 shadow-inner"
      >
        <div className="relative rounded-lg bg-white">
          <canvas
            ref={canvasRef}
            className="block w-full touch-none select-none"
            aria-label={title}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            onPointerLeave={handlePointerUp}
          />
          <div
            className="pointer-events-none absolute inset-x-4 bottom-5 border-b-2 border-zinc-300"
            aria-hidden
          />
          {!hasInk ? (
            <p className="pointer-events-none absolute inset-0 flex items-center justify-center px-4 text-center text-sm text-zinc-400">
              Unterschrift
            </p>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <BigButton
          type="button"
          variant="secondary"
          className="!py-2 text-sm sm:flex-1"
          disabled={disabled || busy || !hasInk}
          onClick={clearPad}
        >
          Löschen
        </BigButton>
        <BigButton
          type="button"
          className="!py-2 text-sm sm:flex-1"
          disabled={disabled || busy || !hasInk}
          onClick={() => void handleConfirm()}
        >
          {busy ? '…' : 'Übernehmen'}
        </BigButton>
      </div>

      {err ? <p className="text-sm text-red-400">{err}</p> : null}
    </section>
  )
}
