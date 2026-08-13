import type { ReportPreviewState, StructuredPayload } from '../pages/ReportNew'

/** API-Bericht → Vorschau-State inkl. existingReportId (Edit-Modus). */
export type ReportDocForEdit = {
  id: string
  projectId?: string
  projectName?: string
  customerName?: string
  date?: string
  employees?: string[]
  employeeIds?: string[]
  startTime?: string
  endTime?: string
  breakMinutes?: number
  exportFormat?: string
  rawText?: string
  notes?: string
  runId?: string | null
  structured?: Partial<StructuredPayload> & {
    materialSuggestions?: string[]
    machineSuggestions?: string[]
    machineHours?: string[]
  }
}

export function buildReportPreviewStateFromDoc(doc: ReportDocForEdit): ReportPreviewState {
  const s = doc.structured ?? {}
  return {
    projectId: String(doc.projectId || ''),
    projectName: String(doc.projectName || ''),
    customerName: String(doc.customerName || ''),
    date: String(doc.date || ''),
    employees: Array.isArray(doc.employees) ? doc.employees.map(String) : [],
    employeeIds: Array.isArray(doc.employeeIds) ? doc.employeeIds.map(String) : [],
    startTime: String(doc.startTime || '08:00'),
    endTime: String(doc.endTime || '16:30'),
    breakMinutes: typeof doc.breakMinutes === 'number' ? doc.breakMinutes : 45,
    exportFormat: String(doc.exportFormat || 'PDF'),
    rawText: String(doc.rawText || ''),
    notes: String(doc.notes || ''),
    seriesMode: Boolean(doc.runId),
    existingReportId: doc.id,
    structured: {
      summary: String(s.summary || ''),
      activities: Array.isArray(s.activities) ? [...s.activities] : [],
      materials: Array.isArray(s.materials) ? [...s.materials] : [],
      materialSuggestions: Array.isArray(s.materialSuggestions) ? [...s.materialSuggestions] : [],
      machineSuggestions: Array.isArray(s.machineSuggestions) ? [...s.machineSuggestions] : [],
      machineHours: Array.isArray(s.machineHours) ? [...s.machineHours] : [],
      problems: Array.isArray(s.problems) ? [...s.problems] : [],
      openItems: Array.isArray(s.openItems) ? [...s.openItems] : [],
      customerTalk: String(s.customerTalk || ''),
      workTime: s.workTime,
      participantsLine: s.participantsLine,
    },
  }
}
