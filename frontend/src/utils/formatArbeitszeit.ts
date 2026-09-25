function hoursDe(value: number): string {
  return value.toFixed(2).replace('.', ',')
}

function workerCount(employees?: string[], employeeIds?: string[]): number {
  const nNames = Array.isArray(employees) ? employees.filter((x) => String(x || '').trim()).length : 0
  const nIds = Array.isArray(employeeIds) ? employeeIds.filter((x) => String(x || '').trim()).length : 0
  return Math.max(nNames, nIds)
}

/** Arbeitszeit-Anzeige wie im PDF: „08:00 – 13:45 | 5,75 Stunden“ (Brutto × Mitarbeiterzahl). */
export function formatArbeitszeitWithHours(startTime: string, endTime: string, workerCountValue = 1): string {
  const start = String(startTime || '').trim() || '?'
  const end = String(endTime || '').trim() || '?'
  const base = `${start} – ${end}`
  const startMin = parseHhmm(start)
  const endMin = parseHhmm(end)
  if (startMin == null || endMin == null || endMin <= startMin) return base
  const n = workerCountValue > 0 ? Math.floor(workerCountValue) : 1
  const hours = Math.round(((endMin - startMin) / 60) * n * 100) / 100
  return `${base} | ${hoursDe(hours)} Stunden`
}

/** Netto-Stunden (Brutto minus Pause), Anzeige wie Backend-PDF — ohne Pausenklammer. */
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
  return `${base} | ${hoursDe(net)} Stunden`
}

export type EmployeeTimeDisplayRow = {
  employeeId: string
  startTime: string
  endTime: string
  breakMinutes: number
}

function netHours(startTime: string, endTime: string, breakMinutes = 0): number | null {
  const startMin = parseHhmm(String(startTime || '').trim())
  const endMin = parseHhmm(String(endTime || '').trim())
  if (startMin == null || endMin == null || endMin <= startMin) return null
  const br = Math.max(0, Number(breakMinutes) || 0)
  const net = Math.round(((endMin - startMin - br) / 60) * 100) / 100
  return net < 0 ? null : net
}

/** Arbeitszeit-Feld im Tagesbericht: Gesamtstunden aller Mitarbeiter. */
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
    let total = 0
    let any = false
    for (const row of times) {
      const net = netHours(row.startTime, row.endTime, row.breakMinutes)
      if (net == null) continue
      total += net
      any = true
    }
    if (any) {
      const start = String(opts.startTime || '').trim() || '?'
      const end = String(opts.endTime || '').trim() || '?'
      return `${start} – ${end} | ${hoursDe(Math.round(total * 100) / 100)} Stunden`
    }
  }
  return formatArbeitszeitWithHours(opts.startTime, opts.endTime, workerCount(opts.employees, opts.employeeIds))
}

function parseHhmm(value: string): number | null {
  const m = /^(\d{1,2}):(\d{2})$/.exec(value.trim())
  if (!m) return null
  const h = Number(m[1])
  const min = Number(m[2])
  if (h > 23 || min > 59) return null
  return h * 60 + min
}
