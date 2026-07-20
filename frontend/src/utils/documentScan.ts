/** Soft-Scan für Lieferschein: Ecken + Perspektivkorrektur (reine Browser-JS, keine Extra-Deps). */

export type Point = { x: number; y: number }

export type Quad = {
  tl: Point
  tr: Point
  br: Point
  bl: Point
}

export function defaultInsetQuad(width: number, height: number, insetRatio = 0.07): Quad {
  const ix = Math.max(8, width * insetRatio)
  const iy = Math.max(8, height * insetRatio)
  return {
    tl: { x: ix, y: iy },
    tr: { x: width - ix, y: iy },
    br: { x: width - ix, y: height - iy },
    bl: { x: ix, y: height - iy },
  }
}

export function loadImageElement(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Bild konnte nicht geladen werden.'))
    }
    img.src = url
  })
}

function dist(a: Point, b: Point): number {
  const dx = a.x - b.x
  const dy = a.y - b.y
  return Math.hypot(dx, dy)
}

/** Ausgabegröße: A4-ähnlich, lange Kante begrenzt. */
export function outputSizeForQuad(quad: Quad, maxEdge = 2400): { w: number; h: number } {
  const top = dist(quad.tl, quad.tr)
  const bottom = dist(quad.bl, quad.br)
  const left = dist(quad.tl, quad.bl)
  const right = dist(quad.tr, quad.br)
  const avgW = (top + bottom) / 2
  const avgH = (left + right) / 2
  if (avgW <= 0 || avgH <= 0) return { w: 1654, h: 2339 }

  const longest = Math.max(avgW, avgH)
  const scale = Math.min(1, maxEdge / longest)
  let w = Math.round(avgW * scale)
  let h = Math.round(avgH * scale)
  w = Math.max(400, Math.min(maxEdge, w))
  h = Math.max(400, Math.min(maxEdge, h))
  return { w, h }
}

/**
 * Grobe Dokument-Erkennung: hellstes großes Blob → 4 Extremecken.
 * Fallback: inset-Rechteck. Nur Best-Effort.
 */
export function detectDocumentQuad(img: HTMLImageElement): Quad {
  const srcW = img.naturalWidth || img.width
  const srcH = img.naturalHeight || img.height
  if (srcW < 32 || srcH < 32) return defaultInsetQuad(srcW, srcH)

  const maxSide = 420
  const scale = Math.min(1, maxSide / Math.max(srcW, srcH))
  const w = Math.max(1, Math.round(srcW * scale))
  const h = Math.max(1, Math.round(srcH * scale))

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) return defaultInsetQuad(srcW, srcH)
  ctx.drawImage(img, 0, 0, w, h)
  const { data } = ctx.getImageData(0, 0, w, h)

  const gray = new Float32Array(w * h)
  let sum = 0
  for (let i = 0, p = 0; i < gray.length; i++, p += 4) {
    const g = 0.299 * data[p]! + 0.587 * data[p + 1]! + 0.114 * data[p + 2]!
    gray[i] = g
    sum += g
  }
  const mean = sum / gray.length
  // Papier meist heller als Hintergrund
  const thresh = Math.min(245, mean + 18)

  const mask = new Uint8Array(w * h)
  for (let i = 0; i < gray.length; i++) {
    mask[i] = gray[i]! >= thresh ? 1 : 0
  }

  // Größte zusammenhängende Komponente (4-Nachbar)
  const label = new Int32Array(w * h)
  let bestCount = 0
  let bestLabel = 0
  let nextLabel = 1
  const stack: number[] = []

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const start = y * w + x
      if (!mask[start] || label[start]) continue
      const id = nextLabel++
      let count = 0
      stack.length = 0
      stack.push(start)
      label[start] = id
      while (stack.length) {
        const i = stack.pop()!
        count++
        const cx = i % w
        const cy = (i / w) | 0
        const nbs = [i - 1, i + 1, i - w, i + w]
        for (const n of nbs) {
          if (n < 0 || n >= w * h) continue
          const nx = n % w
          const ny = (n / w) | 0
          if (Math.abs(nx - cx) + Math.abs(ny - cy) !== 1) continue
          if (!mask[n] || label[n]) continue
          label[n] = id
          stack.push(n)
        }
      }
      if (count > bestCount) {
        bestCount = count
        bestLabel = id
      }
    }
  }

  // Zu klein / kein Papier erkannt
  if (bestCount < w * h * 0.08) {
    return defaultInsetQuad(srcW, srcH)
  }

  let tlScore = Infinity
  let trScore = -Infinity
  let brScore = -Infinity
  let blScore = Infinity
  let tl: Point = { x: 0, y: 0 }
  let tr: Point = { x: w - 1, y: 0 }
  let br: Point = { x: w - 1, y: h - 1 }
  let bl: Point = { x: 0, y: h - 1 }

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (label[y * w + x] !== bestLabel) continue
      const s1 = x + y
      const s2 = x - y
      if (s1 < tlScore) {
        tlScore = s1
        tl = { x, y }
      }
      if (s2 > trScore) {
        trScore = s2
        tr = { x, y }
      }
      if (s1 > brScore) {
        brScore = s1
        br = { x, y }
      }
      if (s2 < blScore) {
        blScore = s2
        bl = { x, y }
      }
    }
  }

  const inv = 1 / scale
  const quad: Quad = {
    tl: { x: tl.x * inv, y: tl.y * inv },
    tr: { x: tr.x * inv, y: tr.y * inv },
    br: { x: br.x * inv, y: br.y * inv },
    bl: { x: bl.x * inv, y: bl.y * inv },
  }

  // Sanity: Ecken nicht degeneriert
  const areaApprox = Math.abs(
    (quad.tr.x - quad.tl.x) * (quad.bl.y - quad.tl.y) - (quad.bl.x - quad.tl.x) * (quad.tr.y - quad.tl.y),
  )
  if (areaApprox < srcW * srcH * 0.05) {
    return defaultInsetQuad(srcW, srcH)
  }
  return clampQuad(quad, srcW, srcH)
}

function clampQuad(q: Quad, w: number, h: number): Quad {
  const clamp = (p: Point): Point => ({
    x: Math.min(w - 1, Math.max(0, p.x)),
    y: Math.min(h - 1, Math.max(0, p.y)),
  })
  return { tl: clamp(q.tl), tr: clamp(q.tr), br: clamp(q.br), bl: clamp(q.bl) }
}

/** Homographie 3x3 (zeilenweise) aus 4 Punktpaaren. */
function computeHomography(src: Point[], dst: Point[]): Float64Array | null {
  // Löst Ah = b für h (8 Freiheitsgrade)
  const A: number[][] = []
  const b: number[] = []
  for (let i = 0; i < 4; i++) {
    const s = src[i]!
    const d = dst[i]!
    A.push([s.x, s.y, 1, 0, 0, 0, -d.x * s.x, -d.x * s.y])
    b.push(d.x)
    A.push([0, 0, 0, s.x, s.y, 1, -d.y * s.x, -d.y * s.y])
    b.push(d.y)
  }

  const h = solveLinearSystem(A, b)
  if (!h) return null
  const H = new Float64Array(9)
  for (let i = 0; i < 8; i++) H[i] = h[i]!
  H[8] = 1
  return H
}

function solveLinearSystem(A: number[][], b: number[]): number[] | null {
  const n = b.length
  const M = A.map((row, i) => [...row, b[i]!])

  for (let col = 0; col < n; col++) {
    let pivot = col
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(M[r]![col]!) > Math.abs(M[pivot]![col]!)) pivot = r
    }
    if (Math.abs(M[pivot]![col]!) < 1e-10) return null
    if (pivot !== col) {
      const tmp = M[col]!
      M[col] = M[pivot]!
      M[pivot] = tmp
    }
    const div = M[col]![col]!
    for (let c = col; c <= n; c++) M[col]![c]! /= div
    for (let r = 0; r < n; r++) {
      if (r === col) continue
      const f = M[r]![col]!
      for (let c = col; c <= n; c++) M[r]![c]! -= f * M[col]![c]!
    }
  }
  return M.map((row) => row[n]!)
}

function applyH(H: Float64Array, x: number, y: number): Point {
  const w = H[6]! * x + H[7]! * y + H[8]!
  if (Math.abs(w) < 1e-12) return { x: 0, y: 0 }
  return {
    x: (H[0]! * x + H[1]! * y + H[2]!) / w,
    y: (H[3]! * x + H[4]! * y + H[5]!) / w,
  }
}

function sampleBilinear(
  data: Uint8ClampedArray,
  w: number,
  h: number,
  x: number,
  y: number,
): [number, number, number] {
  if (x < 0 || y < 0 || x >= w - 1 || y >= h - 1) {
    const cx = Math.min(w - 1, Math.max(0, Math.round(x)))
    const cy = Math.min(h - 1, Math.max(0, Math.round(y)))
    const i = (cy * w + cx) * 4
    return [data[i]!, data[i + 1]!, data[i + 2]!]
  }
  const x0 = Math.floor(x)
  const y0 = Math.floor(y)
  const x1 = x0 + 1
  const y1 = y0 + 1
  const fx = x - x0
  const fy = y - y0
  const i00 = (y0 * w + x0) * 4
  const i10 = (y0 * w + x1) * 4
  const i01 = (y1 * w + x0) * 4
  const i11 = (y1 * w + x1) * 4
  const r =
    data[i00]! * (1 - fx) * (1 - fy) +
    data[i10]! * fx * (1 - fy) +
    data[i01]! * (1 - fx) * fy +
    data[i11]! * fx * fy
  const g =
    data[i00 + 1]! * (1 - fx) * (1 - fy) +
    data[i10 + 1]! * fx * (1 - fy) +
    data[i01 + 1]! * (1 - fx) * fy +
    data[i11 + 1]! * fx * fy
  const b =
    data[i00 + 2]! * (1 - fx) * (1 - fy) +
    data[i10 + 2]! * fx * (1 - fy) +
    data[i01 + 2]! * (1 - fx) * fy +
    data[i11 + 2]! * fx * fy
  return [r, g, b]
}

/**
 * Perspektivkorrektur: Zielrechteck ← Quell-Quad.
 */
export function warpDocumentToCanvas(
  img: HTMLImageElement,
  quad: Quad,
  outW: number,
  outH: number,
): HTMLCanvasElement {
  const srcW = img.naturalWidth || img.width
  const srcH = img.naturalHeight || img.height
  const srcCanvas = document.createElement('canvas')
  srcCanvas.width = srcW
  srcCanvas.height = srcH
  const sctx = srcCanvas.getContext('2d', { willReadFrequently: true })
  if (!sctx) throw new Error('Canvas nicht verfügbar')
  sctx.drawImage(img, 0, 0)
  const srcData = sctx.getImageData(0, 0, srcW, srcH).data

  const srcPts = [quad.tl, quad.tr, quad.br, quad.bl]
  const dstPts = [
    { x: 0, y: 0 },
    { x: outW - 1, y: 0 },
    { x: outW - 1, y: outH - 1 },
    { x: 0, y: outH - 1 },
  ]
  // Dest → Source: Homographie von Ziel nach Quelle
  const H = computeHomography(dstPts, srcPts)
  if (!H) throw new Error('Perspektive konnte nicht berechnet werden.')

  const out = document.createElement('canvas')
  out.width = outW
  out.height = outH
  const octx = out.getContext('2d')
  if (!octx) throw new Error('Canvas nicht verfügbar')
  const outImg = octx.createImageData(outW, outH)
  const od = outImg.data

  for (let y = 0; y < outH; y++) {
    for (let x = 0; x < outW; x++) {
      const p = applyH(H, x, y)
      const [r, g, b] = sampleBilinear(srcData, srcW, srcH, p.x, p.y)
      const i = (y * outW + x) * 4
      od[i] = r
      od[i + 1] = g
      od[i + 2] = b
      od[i + 3] = 255
    }
  }
  octx.putImageData(outImg, 0, 0)
  return out
}

export function canvasToJpegFile(canvas: HTMLCanvasElement, filename: string, quality = 0.92): Promise<File> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error('Scan konnte nicht gespeichert werden.'))
          return
        }
        resolve(new File([blob], filename, { type: 'image/jpeg', lastModified: Date.now() }))
      },
      'image/jpeg',
      quality,
    )
  })
}
