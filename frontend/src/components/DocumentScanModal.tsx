import { useCallback, useEffect, useRef, useState } from 'react'
import { BigButton } from './ui'
import {
  canvasToJpegFile,
  defaultInsetQuad,
  detectDocumentQuad,
  loadImageElement,
  outputSizeForQuad,
  warpDocumentToCanvas,
  type Point,
  type Quad,
} from '../utils/documentScan'

type CornerKey = keyof Quad

type DocumentScanModalProps = {
  open: boolean
  file: File | null
  onCancel: () => void
  /** Perspektivkorrigierter Scan. */
  onAcceptScan: (file: File) => void
  /** Originalfoto ohne Zuschnitt. */
  onAcceptOriginal: (file: File) => void
}

const CORNER_KEYS: CornerKey[] = ['tl', 'tr', 'br', 'bl']

export function DocumentScanModal({
  open,
  file,
  onCancel,
  onAcceptScan,
  onAcceptOriginal,
}: DocumentScanModalProps) {
  const imgRef = useRef<HTMLImageElement | null>(null)
  const stageRef = useRef<HTMLDivElement>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [natural, setNatural] = useState({ w: 1, h: 1 })
  const [quad, setQuad] = useState<Quad | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [hint, setHint] = useState('Ecken ziehen, dann als Scan übernehmen.')
  const dragKey = useRef<CornerKey | null>(null)

  useEffect(() => {
    if (!open || !file) {
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return null
      })
      setQuad(null)
      setErr('')
      setBusy(false)
      return
    }

    let cancelled = false
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    setErr('')
    setHint('Dokument wird erkannt…')

    void (async () => {
      try {
        const img = await loadImageElement(file)
        if (cancelled) return
        imgRef.current = img
        const w = img.naturalWidth || img.width
        const h = img.naturalHeight || img.height
        setNatural({ w, h })
        setQuad(detectDocumentQuad(img))
        setHint('Ecken bei Bedarf nachziehen, dann übernehmen.')
      } catch {
        if (!cancelled) {
          setErr('Bild konnte nicht geladen werden.')
          setHint('')
        }
      }
    })()

    return () => {
      cancelled = true
      URL.revokeObjectURL(url)
    }
  }, [open, file])

  const clientToImage = useCallback(
    (clientX: number, clientY: number): Point | null => {
      const stage = stageRef.current
      const imgEl = stage?.querySelector('img')
      if (!imgEl) return null
      const rect = imgEl.getBoundingClientRect()
      if (rect.width <= 0 || rect.height <= 0) return null
      const x = ((clientX - rect.left) / rect.width) * natural.w
      const y = ((clientY - rect.top) / rect.height) * natural.h
      return {
        x: Math.min(natural.w, Math.max(0, x)),
        y: Math.min(natural.h, Math.max(0, y)),
      }
    },
    [natural.h, natural.w],
  )

  useEffect(() => {
    if (!open) return

    function onMove(e: PointerEvent) {
      const key = dragKey.current
      if (!key) return
      const p = clientToImage(e.clientX, e.clientY)
      if (!p) return
      setQuad((prev) => (prev ? { ...prev, [key]: p } : prev))
    }

    function onUp() {
      dragKey.current = null
    }

    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    window.addEventListener('pointercancel', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      window.removeEventListener('pointercancel', onUp)
    }
  }, [open, clientToImage])

  function resetCorners() {
    setQuad(defaultInsetQuad(natural.w, natural.h))
    setHint('Ecken zurückgesetzt — bei Bedarf nachziehen.')
  }

  function redetect() {
    if (!imgRef.current) return
    setQuad(detectDocumentQuad(imgRef.current))
    setHint('Automatik erneut ausgeführt — Ecken prüfen.')
  }

  async function acceptScan() {
    if (!file || !quad || !imgRef.current || busy) return
    setBusy(true)
    setErr('')
    try {
      const { w, h } = outputSizeForQuad(quad, 2400)
      const canvas = warpDocumentToCanvas(imgRef.current, quad, w, h)
      const out = await canvasToJpegFile(canvas, `scan-${Date.now()}.jpg`, 0.92)
      onAcceptScan(out)
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Scan fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  if (!open || !file) return null

  const toCss = (p: Point) => ({
    left: `${(p.x / natural.w) * 100}%`,
    top: `${(p.y / natural.h) * 100}%`,
  })

  return (
    <div className="fixed inset-0 z-[120] flex flex-col bg-zinc-950">
      <div className="safe-area-pt-min flex items-center justify-between px-4 py-3">
        <p className="text-sm font-medium text-white">Dokument zuschneiden</p>
        <button
          type="button"
          className="rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:text-white"
          onClick={onCancel}
          disabled={busy}
        >
          Abbrechen
        </button>
      </div>

      <div ref={stageRef} className="relative mx-3 min-h-0 flex-1 overflow-hidden rounded-xl bg-black">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt="Scan-Vorschau"
            className="h-full w-full object-contain"
            draggable={false}
          />
        ) : null}

        {quad && previewUrl ? (
          <CornerOverlay
            natural={natural}
            quad={quad}
            toCss={toCss}
            onCornerDown={(key) => {
              dragKey.current = key
            }}
          />
        ) : null}
      </div>

      <div className="safe-area-pb space-y-2 px-4 py-3">
        {hint ? <p className="text-center text-xs text-zinc-400">{hint}</p> : null}
        {err ? <p className="text-center text-sm text-red-300">{err}</p> : null}

        <div className="flex gap-2">
          <BigButton type="button" variant="secondary" className="min-h-11 flex-1 text-sm" disabled={busy} onClick={redetect}>
            Auto
          </BigButton>
          <BigButton
            type="button"
            variant="secondary"
            className="min-h-11 flex-1 text-sm"
            disabled={busy}
            onClick={resetCorners}
          >
            Zurücksetzen
          </BigButton>
        </div>

        <BigButton type="button" disabled={busy || !quad} onClick={() => void acceptScan()}>
          {busy ? 'Wird verarbeitet…' : 'Als Scan übernehmen'}
        </BigButton>
        <BigButton type="button" variant="secondary" disabled={busy} onClick={() => onAcceptOriginal(file)}>
          Ohne Zuschnitt
        </BigButton>
      </div>
    </div>
  )
}

function CornerOverlay({
  natural,
  quad,
  toCss,
  onCornerDown,
}: {
  natural: { w: number; h: number }
  quad: Quad
  toCss: (p: Point) => { left: string; top: string }
  onCornerDown: (key: CornerKey) => void
}) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [box, setBox] = useState<{ left: number; top: number; width: number; height: number } | null>(null)

  useEffect(() => {
    const parent = wrapRef.current?.parentElement
    const img = parent?.querySelector('img')
    if (!parent || !img) return

    function measure() {
      if (!parent || !img) return
      const pr = parent.getBoundingClientRect()
      const ir = img.getBoundingClientRect()
      setBox({
        left: ir.left - pr.left,
        top: ir.top - pr.top,
        width: ir.width,
        height: ir.height,
      })
    }

    measure()
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(measure) : null
    ro?.observe(parent)
    ro?.observe(img)
    window.addEventListener('resize', measure)
    return () => {
      ro?.disconnect()
      window.removeEventListener('resize', measure)
    }
  }, [natural.w, natural.h, quad])

  return (
    <div ref={wrapRef} className="pointer-events-none absolute inset-0">
      {box ? (
        <div
          className="absolute"
          style={{ left: box.left, top: box.top, width: box.width, height: box.height }}
        >
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox={`0 0 ${natural.w} ${natural.h}`}
            preserveAspectRatio="none"
          >
            <polygon
              points={`${quad.tl.x},${quad.tl.y} ${quad.tr.x},${quad.tr.y} ${quad.br.x},${quad.br.y} ${quad.bl.x},${quad.bl.y}`}
              fill="rgba(249,115,22,0.2)"
              stroke="rgb(251,146,60)"
              strokeWidth={Math.max(natural.w, natural.h) * 0.004}
            />
          </svg>
          {CORNER_KEYS.map((key) => {
            const pos = toCss(quad[key])
            return (
              <button
                key={key}
                type="button"
                aria-label={`Ecke ${key}`}
                className="pointer-events-auto absolute z-10 h-11 w-11 -translate-x-1/2 -translate-y-1/2 touch-none rounded-full border-2 border-orange-300 bg-orange-500/90 shadow-lg"
                style={pos}
                onPointerDown={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
                  onCornerDown(key)
                }}
              />
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
