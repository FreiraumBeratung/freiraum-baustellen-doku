/** Optionale Einzel-Arbeitszeiten je Mitarbeiter (leer = alle wie Bericht). */

export type EmployeeTimeSlot = {
  employeeId: string
  startTime: string
  endTime: string
  breakMinutes: number
}

export function defaultEmployeeTimeSlot(
  employeeId: string,
  startTime: string,
  endTime: string,
  breakMinutes: number,
): EmployeeTimeSlot {
  return {
    employeeId,
    startTime,
    endTime,
    breakMinutes,
  }
}

export function buildEmployeeTimesPayload(
  enabled: boolean,
  employeeIds: string[],
  byId: Record<string, EmployeeTimeSlot>,
  fallback: { startTime: string; endTime: string; breakMinutes: number },
): EmployeeTimeSlot[] {
  if (!enabled || employeeIds.length < 2) return []
  return employeeIds.map((id) => {
    const slot = byId[id]
    if (slot) {
      return {
        employeeId: id,
        startTime: slot.startTime || fallback.startTime,
        endTime: slot.endTime || fallback.endTime,
        breakMinutes:
          typeof slot.breakMinutes === 'number' ? slot.breakMinutes : fallback.breakMinutes,
      }
    }
    return defaultEmployeeTimeSlot(id, fallback.startTime, fallback.endTime, fallback.breakMinutes)
  })
}

export function employeeTimesToMap(list: EmployeeTimeSlot[] | undefined | null): Record<string, EmployeeTimeSlot> {
  const out: Record<string, EmployeeTimeSlot> = {}
  if (!Array.isArray(list)) return out
  for (const item of list) {
    const id = String(item?.employeeId || '').trim()
    if (!id) continue
    out[id] = {
      employeeId: id,
      startTime: String(item.startTime || '08:00'),
      endTime: String(item.endTime || '16:30'),
      breakMinutes: typeof item.breakMinutes === 'number' ? item.breakMinutes : 45,
    }
  }
  return out
}
