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

/** Netto-Stunden (Brutto minus Pause), Anzeige wie Backend-PDF. */
export function formatArbeitszeitNettoWithHours(
  startTime: string,
  endTime: string,
  breakMinutes = 0,
): string {
  const start = String(startTime || '').trim() || '?'
  const end = String(endTime || '').trim() || '?'
  const base = `${start} – ${end}`
  const startMin = parseHhmm(start)
  const endMin = parseHhmm(end)
  if (startMin == null || endMin == null || endMin <= startMin) return base
  const br = Math.max(0, Number(breakMinutes) || 0)
  const net = Math.round(((endMin - startMin - br) / 60) * 100) / 100
  if (net < 0) return base
  const hoursDe = net.toFixed(2).replace('.', ',')
  const pause = br > 0 ? ` (Pause ${br} Min.)` : ''
  return `${base} | ${hoursDe} Stunden${pause}`
}

export type EmployeeTimeDisplayRow = {
  employeeId: string
  startTime: string
  endTime: string
  breakMinutes: number
}

/** Arbeitszeit-Feld: bei Einzelzeiten Mitarbeiterzeilen, sonst Sammelzeit. */
export function formatArbeitszeitField(opts: {
  startTime: string
  endTime: string
  breakMinutes?: number
  employees?: string[]
  employeeIds?: string[]
  employeeTimes?: EmployeeTimeDisplayRow[] | null
}): string {
  const times = Array.isArray(opts.employeeTimes) ? opts.employeeTimes : []
  if (times.length > 0) {
    const ids = Array.isArray(opts.employeeIds) ? opts.employeeIds : []
    const names = Array.isArray(opts.employees) ? opts.employees : []
    const nameById = new Map(ids.map((id, i) => [id, names[i] || id]))
    return times
      .map((row) => {
        const name = nameById.get(row.employeeId) || row.employeeId
        return `${name}: ${formatArbeitszeitNettoWithHours(row.startTime, row.endTime, row.breakMinutes)}`
      })
      .join('\n')
  }
  return formatArbeitszeitWithHours(opts.startTime, opts.endTime)
}

function parseHhmm(value: string): number | null {
  const m = /^(\d{1,2}):(\d{2})$/.exec(value.trim())
  if (!m) return null
  const h = Number(m[1])
  const min = Number(m[2])
  if (h > 23 || min > 59) return null
  return h * 60 + min
}
