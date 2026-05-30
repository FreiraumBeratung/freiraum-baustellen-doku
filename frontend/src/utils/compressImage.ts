/** Verkleinert Baustellenfotos vor dem Upload (Handy-Kamera liefert oft 6–15 MB). */

const DEFAULT_MAX_EDGE = 1920
const DEFAULT_QUALITY = 0.82
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

/**
 * Skaliert auf max. Kantenlaenge und speichert als JPEG.
 * Ziel: deutlich unter 5 MB Backend-Limit bleiben.
 */
export async function compressImageForUpload(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) {
    throw new Error('Nur Bilddateien sind erlaubt.')
  }

  // Kleine Dateien unveraendert durchreichen (spart CPU auf schwachen Geraeten).
  if (file.size <= 900 * 1024 && (file.type === 'image/jpeg' || file.type === 'image/webp')) {
    return file
  }

  const img = await loadImageFromFile(file)
  const { w, h } = scaledSize(img.naturalWidth || img.width, img.naturalHeight || img.height, DEFAULT_MAX_EDGE)

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Bildverarbeitung nicht verfügbar.')
  ctx.drawImage(img, 0, 0, w, h)

  let quality = DEFAULT_QUALITY
  let blob = await canvasToBlob(canvas, quality)
  while (blob.size > TARGET_MAX_BYTES && quality > 0.45) {
    quality -= 0.08
    blob = await canvasToBlob(canvas, quality)
  }

  if (blob.size > TARGET_MAX_BYTES) {
    throw new Error('Foto ist auch nach Verkleinerung zu groß. Bitte ein anderes Bild wählen.')
  }

  return new File([blob], outputName(file.name), { type: 'image/jpeg', lastModified: Date.now() })
}
