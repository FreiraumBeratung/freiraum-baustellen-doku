/** Bevorzugt audio/webm; Safari/Edge können audio/mp4 o. Ä. liefern. */

export function pickMediaRecorderMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined') return undefined
  if (typeof MediaRecorder.isTypeSupported !== 'function') return undefined
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/mp4;codecs=mp4a.40.2',
  ]
  for (const m of candidates) {
    if (MediaRecorder.isTypeSupported(m)) return m
  }
  return undefined
}

export function inferExtensionFromMime(mime: string): string {
  const m = (mime || '').toLowerCase()
  if (m.includes('webm')) return 'webm'
  if (m.includes('ogg')) return 'ogg'
  if (m.includes('wav')) return 'wav'
  if (m.includes('mp3') || (m.includes('mpeg') && m.includes('audio'))) return 'mp3'
  if (m.includes('mp4') || m.includes('aac') || m.includes('m4a')) return 'm4a'
  return 'webm'
}

export function browserSupportsMediaRecording(): boolean {
  return Boolean(
    typeof navigator !== 'undefined' &&
      typeof navigator.mediaDevices?.getUserMedia === 'function' &&
      typeof MediaRecorder !== 'undefined',
  )
}
