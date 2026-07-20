/** Verkleinert Baustellenfotos vor dem Upload (Handy-Kamera liefert oft 6–15 MB). */

const DEFAULT_MAX_EDGE = 1920
const DEFAULT_QUALITY = 0.82
/** Lieferschein: mehr Pixel + höhere JPEG-Qualität für Lesbarkeit. */
const DELIVERY_MAX_EDGE = 3200
const DELIVERY_QUALITY = 0.9
const TARGET_MAX_BYTES = 4.5 * 1024 * 1024

function loadImageFromFile(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Bild konnte nicht gelesen werden.'))
    }
    img.src = url
  })
}

function scaledSize(width: number, height: number, maxEdge: number): { w: number; h: number } {
  const longest = Math.max(width, height)
  if (longest <= maxEdge) return { w: width, h: height }
  const scale = maxEdge / longest
  return {
    w: Math.max(1, Math.round(width * scale)),
    h: Math.max(1, Math.round(height * scale)),
  }
}

function canvasToBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) resolve(blob)
        else reject(new Error('Bild konnte nicht komprimiert werden.'))
      },
      'image/jpeg',
      quality,
    )
  })
}

function outputName(original: string): string {
  const base = original.replace(/\.[^.]+$/, '').trim() || 'baustelle'
  return `${base}.jpg`
}

async function compressImageWithOptions(
  file: File,
  opts: {
    maxEdge: number
    quality: number
    /** Kleine JPEGs nur durchreichen, wenn die Kante schon groß genug ist. */
    passThroughMinEdge: number
    defaultBaseName: string
  },
): Promise<File> {
  if (!file.type.startsWith('image/')) {
    throw new Error('Nur Bilddateien sind erlaubt.')
  }

  const img = await loadImageFromFile(file)
  const srcW = img.naturalWidth || img.width
  const srcH = img.naturalHeight || img.height
  const longest = Math.max(srcW, srcH)

  // Kleine Dateien nur durchreichen, wenn die Auflösung schon passt (kein VGA-„Pass“).
  if (
    file.size <= 900 * 1024 &&
    (file.type === 'image/jpeg' || file.type === 'image/webp') &&
    longest >= opts.passThroughMinEdge
  ) {
    return file
  }

  const { w, h } = scaledSize(srcW, srcH, opts.maxEdge)

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Bildverarbeitung nicht verfügbar.')
  ctx.drawImage(img, 0, 0, w, h)

  let quality = opts.quality
  let blob = await canvasToBlob(canvas, quality)
  while (blob.size > TARGET_MAX_BYTES && quality > 0.45) {
    quality -= 0.08
    blob = await canvasToBlob(canvas, quality)
  }

  if (blob.size > TARGET_MAX_BYTES) {
    throw new Error('Foto ist auch nach Verkleinerung zu groß. Bitte ein anderes Bild wählen.')
  }

  const name =
    file.name && file.name.includes('.')
      ? outputName(file.name)
      : `${opts.defaultBaseName}.jpg`

  return new File([blob], name, { type: 'image/jpeg', lastModified: Date.now() })
}

/**
 * Skaliert auf max. Kantenlaenge und speichert als JPEG.
 * Ziel: deutlich unter 5 MB Backend-Limit bleiben.
 */
export async function compressImageForUpload(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) {
    throw new Error('Nur Bilddateien sind erlaubt.')
  }

  // Wie bisher: kleine JPEGs unverändert durchreichen (Berichte/Feedback).
  if (file.size <= 900 * 1024 && (file.type === 'image/jpeg' || file.type === 'image/webp')) {
    return file
  }

  return compressImageWithOptions(file, {
    maxEdge: DEFAULT_MAX_EDGE,
    quality: DEFAULT_QUALITY,
    passThroughMinEdge: 0,
    defaultBaseName: 'baustelle',
  })
}

/**
 * Lieferschein-Scan: höhere Auflösung/Qualität als normale Baustellenfotos.
 * Bestehende Bericht-/Feedback-Kompression bleibt unverändert.
 */
export async function compressImageForDeliveryNoteUpload(file: File): Promise<File> {
  return compressImageWithOptions(file, {
    maxEdge: DELIVERY_MAX_EDGE,
    quality: DELIVERY_QUALITY,
    // VGA/Preview (z. B. 640) nie als „fertig“ durchreichen
    passThroughMinEdge: 1600,
    defaultBaseName: 'lieferschein',
  })
}
