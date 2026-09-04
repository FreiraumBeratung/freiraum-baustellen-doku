/** Arbeitszeit-Anzeige wie im PDF: „08:00 – 13:45 | 5,75 Stunden“ (Brutto, ohne Pause). */
export function formatArbeitszeitWithHours(startTime: string, endTime: string): string {
  const start = String(startTime || '').trim() || '?'
  const end = String(endTime || '').trim() || '?'
  const base = `${start} – ${end}`
  const startMin = parseHhmm(start)
  const endMin = parseHhmm(end)
  if (startMin == null || endMin == null || endMin <= startMin) return base
  const hours = Math.round(((endMin - startMin) / 60) * 100) / 100
  const hoursDe = hours.toFixed(2).replace('.', ',')
  return `${base} | ${hoursDe} Stunden`
}

function parseHhmm(value: string): number | null {
  const m = /^(\d{1,2}):(\d{2})$/.exec(value.trim())
  if (!m) return null
  const h = Number(m[1])
  const min = Number(m[2])
  if (h > 23 || min > 59) return null
  return h * 60 + min
}
