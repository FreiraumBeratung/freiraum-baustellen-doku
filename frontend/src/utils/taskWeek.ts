/** Lokale Kalenderwoche (Mo–So), ohne UTC-Verschiebung. */

const WEEKDAY_SHORT = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'] as const
const WEEKDAY_LONG = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'] as const

export function toIsoLocal(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function parseIsoLocal(iso: string): Date {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || '').trim())
  if (!m) return new Date()
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 12, 0, 0, 0)
}

export function todayIsoLocal(): string {
  return toIsoLocal(new Date())
}

export function addDaysIso(iso: string, days: number): string {
  const d = parseIsoLocal(iso)
  d.setDate(d.getDate() + days)
  return toIsoLocal(d)
}

export function startOfWeekMonday(iso: string): string {
  const d = parseIsoLocal(iso)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return toIsoLocal(d)
}

export function weekDates(weekStart: string): string[] {
  return Array.from({ length: 7 }, (_, i) => addDaysIso(weekStart, i))
}

export function weekdayShort(iso: string): string {
  const d = parseIsoLocal(iso)
  const idx = d.getDay() === 0 ? 6 : d.getDay() - 1
  return WEEKDAY_SHORT[idx] || 'Mo'
}

export function weekdayLong(iso: string): string {
  const d = parseIsoLocal(iso)
  const idx = d.getDay() === 0 ? 6 : d.getDay() - 1
  return WEEKDAY_LONG[idx] || 'Montag'
}

export function formatDayMonth(iso: string): string {
  const d = parseIsoLocal(iso)
  return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.`
}

export function isoWeekNumber(iso: string): number {
  const d = parseIsoLocal(iso)
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const dayNr = (target.getDay() + 6) % 7
  target.setDate(target.getDate() - dayNr + 3)
  const firstThursday = new Date(target.getFullYear(), 0, 4)
  const firstDayNr = (firstThursday.getDay() + 6) % 7
  firstThursday.setDate(firstThursday.getDate() - firstDayNr + 3)
  return 1 + Math.round((target.getTime() - firstThursday.getTime()) / 604800000)
}

export function weekLabel(weekStart: string): string {
  const end = addDaysIso(weekStart, 6)
  return `KW ${isoWeekNumber(weekStart)} · ${formatDayMonth(weekStart)}–${formatDayMonth(end)}`
}
