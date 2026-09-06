import { useMemo, useRef, useState, useEffect, useLayoutEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api, downloadExport, resolveBackendPublicUrl } from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { ReportPhotosSection } from '../components/ReportPhotosSection'
import { ReportSignaturesSection } from '../components/ReportSignaturesSection'
import {
  clearReportPreviewPersist,
  loadReportPreviewPersist,
  saveReportPreviewPersist,
} from '../utils/reportPreviewPersist'
import { formatArbeitszeitWithHours } from '../utils/formatArbeitszeit'
import {
  buildEmployeeTimesPayload,
  defaultEmployeeTimeSlot,
  employeeTimesToMap,
  type EmployeeTimeSlot,
} from '../utils/employeeTimes'
import type { ReportPreviewState, StructuredPayload } from './ReportNew'
import type { FeedbackNavState } from './Feedback'

const inputClass =
  'mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none placeholder:text-zinc-600 focus:border-orange-500'
const textareaClass =
  `${inputClass} resize-y min-h-[8rem]` as const

function cloneStructured(s: StructuredPayload): StructuredPayload {
  return {
    summary: s.summary,
    activities: [...s.activities],
    materials: [...s.materials],
    materialSuggestions: [...s.materialSuggestions],
    machineSuggestions: [...s.machineSuggestions],
    machineHours: [...s.machineHours],
    problems: [...s.problems],
    openItems: [...s.openItems],
    customerTalk: s.customerTalk,
    workTime: s.workTime,
    participantsLine: s.participantsLine,
  }
}

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  return a.every((v, i) => v.trim() === b[i]!.trim())
}

function defaultEmptyStructured(): StructuredPayload {
  return {
    summary: '',
    activities: [],
    materials: [],
    materialSuggestions: [],
    machineSuggestions: [],
    machineHours: [],
    problems: [],
    openItems: [],
    customerTalk: '',
  }
}

function structuredEqual(a: StructuredPayload, b: StructuredPayload): boolean {
  return (
    a.summary.trim() === b.summary.trim() &&
    a.customerTalk.trim() === b.customerTalk.trim() &&
    arraysEqual(a.activities, b.activities) &&
    arraysEqual(a.materials, b.materials) &&
    arraysEqual(a.materialSuggestions, b.materialSuggestions) &&
    arraysEqual(a.machineSuggestions, b.machineSuggestions) &&
    arraysEqual(a.machineHours, b.machineHours) &&
    arraysEqual(a.problems, b.problems) &&
    arraysEqual(a.openItems, b.openItems)
  )
}

function defaultBreakMinutes(st: ReportPreviewState): number {
  const n = st.breakMinutes
  return typeof n === 'number' && n >= 0 ? n : 45
}

function defaultEmployeeIds(st: ReportPreviewState): string[] {
  return Array.isArray(st.employeeIds) ? st.employeeIds : []
}

type DraftMeta = {
  startTime: string
  endTime: string
  breakMinutes: number
  employees: string[]
  employeeIds: string[]
  perEmployeeTimes: boolean
  employeeTimesById: Record<string, EmployeeTimeSlot>
}

function emptyDraftMeta(): DraftMeta {
  return {
    startTime: '08:00',
    endTime: '16:30',
    breakMinutes: 45,
    employees: [],
    employeeIds: [],
    perEmployeeTimes: false,
    employeeTimesById: {},
  }
}

function metaFromState(st: ReportPreviewState): DraftMeta {
  const times = Array.isArray(st.employeeTimes) ? st.employeeTimes : []
  return {
    startTime: st.startTime,
    endTime: st.endTime,
    breakMinutes: defaultBreakMinutes(st),
    employees: [...(st.employees || [])],
    employeeIds: [...defaultEmployeeIds(st)],
    perEmployeeTimes: times.length > 0,
    employeeTimesById: employeeTimesToMap(times),
  }
}

function metaEqual(a: DraftMeta, b: DraftMeta): boolean {
  if (a.startTime !== b.startTime || a.endTime !== b.endTime || a.breakMinutes !== b.breakMinutes) {
    return false
  }
  if (a.perEmployeeTimes !== b.perEmployeeTimes) return false
  if (a.employees.length !== b.employees.length || a.employeeIds.length !== b.employeeIds.length) {
    return false
  }
  if (!a.employees.every((v, i) => v === b.employees[i])) return false
  if (!a.employeeIds.every((v, i) => v === b.employeeIds[i])) return false
  const aPayload = buildEmployeeTimesPayload(a.perEmployeeTimes, a.employeeIds, a.employeeTimesById, a)
  const bPayload = buildEmployeeTimesPayload(b.perEmployeeTimes, b.employeeIds, b.employeeTimesById, b)
  if (aPayload.length !== bPayload.length) return false
  return aPayload.every((row, i) => {
    const other = bPayload[i]!
    return (
      row.employeeId === other.employeeId &&
      row.startTime === other.startTime &&
      row.endTime === other.endTime &&
      row.breakMinutes === other.breakMinutes
    )
  })
}

function formatHoursDe(h: number | null | undefined): string {
  if (h == null || Number.isNaN(h)) return '—'
  return `${String(h).replace('.', ',')} h`
}

function formatBookedEmployeeNames(names: string[]): string {
  const cleaned = names.map((n) => n.trim()).filter(Boolean)
  if (cleaned.length === 0) return ''
  if (cleaned.length === 1) return cleaned[0]!
  if (cleaned.length === 2) return `${cleaned[0]} und ${cleaned[1]}`
  return `${cleaned.slice(0, -1).join(', ')} und ${cleaned[cleaned.length - 1]}`
}

function timeBookingMessage(booking: {
  created?: number
  hoursPerEmployee?: number | null
  hoursByEmployee?: { name?: string; hours?: number }[]
  hoursUniform?: boolean
  bookedNames?: string[]
  skippedNames?: string[]
  reason?: string | null
} | null | undefined): { ok: string; warn: string } {
  if (!booking) return { ok: '', warn: '' }
  const created = booking.created ?? 0
  if (created > 0) {
    const byEmp = Array.isArray(booking.hoursByEmployee) ? booking.hoursByEmployee : []
    const uniform = booking.hoursUniform !== false
    if (!uniform && byEmp.length > 0) {
      const parts = byEmp
        .map((row) => {
          const n = String(row.name || '').trim()
          if (!n) return ''
          return `${n} ${formatHoursDe(row.hours)}`
        })
        .filter(Boolean)
      if (parts.length) {
        return { ok: `Stundenkonto: ${parts.join(' · ')}.`, warn: '' }
      }
    }
    const per = formatHoursDe(booking.hoursPerEmployee)
    const names = formatBookedEmployeeNames(booking.bookedNames ?? [])
    if (names) {
      if (created === 1) {
        return {
          ok: `Auf dem Stundenkonto von ${names} wurden ${per} gebucht.`,
          warn: '',
        }
      }
      return {
        ok: `Auf den Stundenkonten von ${names} wurden je ${per} gebucht.`,
        warn: '',
      }
    }
    return {
      ok: `Stunden gebucht: ${created} Mitarbeiter à je ${per}.`,
      warn: '',
    }
  }
  if (booking.reason === 'invalid_work_time') {
    return { ok: '', warn: 'Arbeitszeit ungültig — keine Stunden gebucht.' }
  }
  if (booking.reason === 'no_employees') {
    return { ok: '', warn: 'Keine Mitarbeiter gewählt — keine Stunden gebucht.' }
  }
  const skipped = booking.skippedNames ?? []
  if (skipped.length) {
    return {
      ok: '',
      warn: `Stunden nicht gebucht — unbekannte Mitarbeiter: ${skipped.join(', ')}`,
    }
  }
  if (booking.reason === 'no_matched_employees') {
    return { ok: '', warn: 'Keine passenden Mitarbeiter — keine Stunden gebucht.' }
  }
  return { ok: '', warn: '' }
}

function buildPlainText(companyName: string, st: ReportPreviewState, structured: StructuredPayload) {
  const s = structured
  const emps = st.employees.length ? st.employees.join(', ') : 'Keine Angabe'
  const empLine = `Mitarbeiter: ${emps}`
  const timeLine = `Arbeitszeit: ${formatArbeitszeitWithHours(st.startTime, st.endTime)}`
  const lines = [
    'TAGESBERICHT',
    `Firma: ${companyName}`,
    `Baustelle: ${st.projectName}`,
    `Kunde: ${st.customerName}`,
    `Datum: ${st.date}`,
    empLine,
    timeLine,
    `Format: ${st.exportFormat}`,
    '',
    'Zusammenfassung',
    s.summary || 'Keine Angabe',
    '',
    'Tätigkeiten',
    ...(s.activities.length ? s.activities.map((a) => `• ${a}`) : ['• Keine Angabe']),
    '',
    'Material',
    ...(s.materials.length ? s.materials.map((a) => `• ${a}`) : ['• Keine Angabe']),
    '',
    'Maschinenstunden',
    ...(s.machineHours.length ? s.machineHours.map((a) => `• ${a}`) : ['• Keine Angabe']),
    '',
    'Probleme',
    ...(s.problems.length ? s.problems.map((a) => `• ${a}`) : ['• Keine Angabe']),
    '',
    'Offene Punkte',
    ...(s.openItems.length ? s.openItems.map((a) => `• ${a}`) : ['• Keine Angabe']),
    '',
    'Kundengespräch',
    s.customerTalk || 'Keine Angabe',
    '',
    'Rohtext',
    st.rawText,
  ]
  return lines.join('\n')
}

function EditableArraySection({
  title,
  items,
  onChange,
  addLabel,
  disabled,
}: {
  title: string
  items: string[]
  onChange: (next: string[]) => void
  addLabel: string
  disabled: boolean
}) {
  function setIdx(i: number, v: string) {
    const next = [...items]
    next[i] = v
    onChange(next)
  }
  function removeIdx(i: number) {
    onChange(items.filter((_, j) => j !== i))
  }
  function addRow() {
    onChange([...items, ''])
  }

  return (
    <section>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">{title}</h3>
      <div className="mt-3 space-y-3">
        {items.length ? (
          items.map((value, i) => (
            <div key={i} className="flex flex-col gap-2 sm:flex-row sm:items-start">
              <textarea
                rows={2}
                className={`${textareaClass} sm:flex-1 !mt-0 !min-h-[3rem]`}
                value={value}
                disabled={disabled}
                onChange={(e) => setIdx(i, e.target.value)}
                placeholder="Eintrag"
                aria-label={`${title} ${i + 1}`}
              />
              <button
                type="button"
                disabled={disabled}
                className="shrink-0 rounded-lg border border-zinc-600 px-3 py-2 text-sm text-zinc-300 hover:border-red-500/70 hover:text-red-300 disabled:pointer-events-none disabled:opacity-40"
                onClick={() => removeIdx(i)}
              >
                Entfernen
              </button>
            </div>
          ))
        ) : (
          <p className="text-sm text-zinc-500">Noch keine Einträge — unten einen Punkt hinzufügen.</p>
        )}
        <BigButton variant="secondary" type="button" disabled={disabled} className="!py-2 text-sm" onClick={addRow}>
          {addLabel}
        </BigButton>
      </div>
    </section>
  )
}

function normalizeSuggestionToMaterial(value: string): string {
  let out = String(value || '')
    .replace(/\?+$/g, '')
    .trim()
  // Vorschlagslabels wie "Beton benutzt" -> Materialkern "Beton"
  out = out.replace(
    /\s+(benutzt|verwendet|verbaut|verarbeitet|eingebaut|aufgetragen|aufgebracht|gesetzt|gelegt|montiert)$/i,
    '',
  )
  out = out.replace(/[.,;:!?]+$/g, '').trim()
  return out
}

function normalizeMachineSuggestionToEntry(value: string): string {
  const raw = String(value || '')
    .replace(/\?+$/g, '')
    .trim()
  // "Baggerstunden erfassen" -> "Bagger: "
  const m = raw.match(/^(.+?)stunden\s+erfassen$/i)
  if (m?.[1]) {
    return `${m[1].trim()}: `
  }
  return `${raw}: `
}

function MaterialSuggestionsSection({
  suggestions,
  materials,
  disabled,
  onApply,
  onDismiss,
}: {
  suggestions: string[]
  materials: string[]
  disabled: boolean
  onApply: (suggestion: string) => void
  onDismiss: (suggestion: string) => void
}) {
  const matSet = new Set(materials.map((m) => m.trim().toLowerCase()))
  const visibleSuggestions = suggestions.filter((s) => {
    const core = normalizeSuggestionToMaterial(s).toLowerCase()
    return core.length > 0 && !matSet.has(core)
  })

  if (!visibleSuggestions.length) return null

  return (
    <section>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">Material-Vorschläge</h3>
      <p className="mt-2 text-xs text-zinc-500">Mit einem Klick in die Materialliste übernehmen.</p>
      <div className="mt-3 space-y-2">
        {visibleSuggestions.map((suggestion) => (
          <div key={suggestion} className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <button
              type="button"
              disabled={disabled}
              onClick={() => onApply(suggestion)}
              className="w-full rounded-xl border border-orange-500/50 bg-zinc-950 px-3 py-2 text-left text-sm text-orange-300 transition hover:border-orange-400 hover:text-orange-200 disabled:pointer-events-none disabled:opacity-50"
            >
              + {suggestion}
            </button>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onDismiss(suggestion)}
              className="shrink-0 rounded-lg border border-zinc-600 px-3 py-2 text-sm text-zinc-300 hover:border-zinc-500 disabled:pointer-events-none disabled:opacity-40"
            >
              Ausblenden
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}

function MachineHoursSection({
  items,
  suggestions,
  onChange,
  onApplySuggestion,
  onDismissSuggestion,
  disabled,
}: {
  items: string[]
  suggestions: string[]
  onChange: (next: string[]) => void
  onApplySuggestion: (suggestion: string) => void
  onDismissSuggestion: (suggestion: string) => void
  disabled: boolean
}) {
  const visibleSuggestions = suggestions.filter((s) => String(s || '').trim().length > 0)

  function setIdx(i: number, v: string) {
    const next = [...items]
    next[i] = v
    onChange(next)
  }
  function removeIdx(i: number) {
    onChange(items.filter((_, j) => j !== i))
  }
  function addRow() {
    onChange([...items, ''])
  }

  return (
    <section>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">Maschinenstunden</h3>
      <p className="mt-2 text-xs text-zinc-500">Optional für Kalkulation: Stunden je Maschine erfassen.</p>
      {visibleSuggestions.length > 0 ? (
        <div className="mt-3 space-y-2">
          {visibleSuggestions.map((suggestion) => (
            <div key={suggestion} className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <button
                type="button"
                disabled={disabled}
                onClick={() => onApplySuggestion(suggestion)}
                className="w-full rounded-xl border border-orange-500/50 bg-zinc-950 px-3 py-2 text-left text-sm text-orange-300 transition hover:border-orange-400 hover:text-orange-200 disabled:pointer-events-none disabled:opacity-50"
              >
                + {suggestion}
              </button>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onDismissSuggestion(suggestion)}
                className="shrink-0 rounded-lg border border-zinc-600 px-3 py-2 text-sm text-zinc-300 hover:border-zinc-500 disabled:pointer-events-none disabled:opacity-40"
              >
                Ausblenden
              </button>
            </div>
          ))}
        </div>
      ) : null}
      <div className="mt-3 space-y-3">
        {items.length ? (
          items.map((value, i) => (
            <div key={i} className="flex flex-col gap-2 sm:flex-row sm:items-start">
              <textarea
                rows={2}
                className={`${textareaClass} sm:flex-1 !mt-0 !min-h-[3rem]`}
                value={value}
                disabled={disabled}
                onChange={(e) => setIdx(i, e.target.value)}
                placeholder="Eintrag"
                aria-label={`Maschinenstunden ${i + 1}`}
              />
              <button
                type="button"
                disabled={disabled}
                className="shrink-0 rounded-lg border border-zinc-600 px-3 py-2 text-sm text-zinc-300 hover:border-red-500/70 hover:text-red-300 disabled:pointer-events-none disabled:opacity-40"
                onClick={() => removeIdx(i)}
              >
                Entfernen
              </button>
            </div>
          ))
        ) : (
          <p className="text-sm text-zinc-500">Noch keine Einträge — unten einen Punkt hinzufügen.</p>
        )}
        <BigButton variant="secondary" type="button" disabled={disabled} className="!py-2 text-sm" onClick={addRow}>
          + Maschinenstunde hinzufügen
        </BigButton>
      </div>
    </section>
  )
}

function ReportPreviewInner({
  st,
  draftStructured,
  setDraftStructured,
  draftMeta,
  setDraftMeta,
  setMetaBaseline,
  savedReportId,
  onSave,
  onCopy,
  saveBusy,
  saveErr,
  saveMsg,
  timeBookingMsg,
  timeBookingWarn,
  dirty,
}: {
  st: ReportPreviewState
  draftStructured: StructuredPayload
  setDraftStructured: React.Dispatch<React.SetStateAction<StructuredPayload>>
  draftMeta: DraftMeta
  setDraftMeta: React.Dispatch<React.SetStateAction<DraftMeta>>
  setMetaBaseline: React.Dispatch<React.SetStateAction<DraftMeta>>
  savedReportId: string | null
  onSave: (logoUrl: string | null, companyName: string, officeEmail: string) => void
  onCopy: (companyName: string, structured: StructuredPayload) => void
  saveBusy: boolean
  saveErr: string
  saveMsg: string
  timeBookingMsg: string
  timeBookingWarn: string
  dirty: boolean
}) {
  const nav = useNavigate()
  const { writeBlocked } = useWriteBlocked()
  const isEditMode = Boolean(st.existingReportId)
  const metaEditable = isEditMode && !savedReportId
  const [companyName, setCompanyName] = useState('')
  const [officeEmail, setOfficeEmail] = useState('')
  const [logoUrl, setLogoUrl] = useState<string | null>(null)
  const [dlBusy, setDlBusy] = useState(false)
  const [dlErr, setDlErr] = useState('')
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const [pageWakeKey, setPageWakeKey] = useState(0)
  const [moreOpen, setMoreOpen] = useState(false)
  const [roster, setRoster] = useState<{ id: string; name: string; active?: boolean }[]>([])

  useEffect(() => {
    api<{ companyName: string; officeEmail: string; logoUrl: string | null }>('/api/company-profile').then(
      (p) => {
        setCompanyName(p.companyName)
        setOfficeEmail(p.officeEmail)
        setLogoUrl(p.logoUrl)
      },
    )
  }, [])

  // Nur Edit-Modus: Mitarbeiterliste laden (Create-Vorschau bleibt unverändert).
  useEffect(() => {
    if (!metaEditable) return
    api<{ employees: { id: string; name: string; active?: boolean }[] }>('/api/employees')
      .then((r) => {
        const list = (r.employees || []).filter((e) => e.active !== false)
        setRoster(list)
        // Falls nur Namen gespeichert sind: IDs nachziehen, ohne Auswahl zu verlieren.
        setDraftMeta((prev) => {
          if (prev.employeeIds.length > 0 || prev.employees.length === 0 || list.length === 0) {
            return prev
          }
          const nameSet = new Set(prev.employees.map((n) => n.trim().toLowerCase()).filter(Boolean))
          const matched = list.filter((e) => nameSet.has(e.name.trim().toLowerCase()))
          if (!matched.length) return prev
          const next: DraftMeta = {
            ...prev,
            employeeIds: matched.map((e) => e.id),
            employees: matched.map((e) => e.name),
          }
          // Baseline mitziehen, damit reines ID-Nachziehen nicht als „dirty“ gilt.
          setMetaBaseline((base) =>
            base.employeeIds.length > 0
              ? base
              : { ...base, employeeIds: next.employeeIds, employees: next.employees },
          )
          return next
        })
      })
      .catch(() => setRoster([]))
  }, [metaEditable, setDraftMeta, setMetaBaseline])

  const s = draftStructured

  function applyMaterialSuggestion(suggestion: string) {
    const material = normalizeSuggestionToMaterial(suggestion)
    if (!material) return
    setDraftStructured((prev) => {
      const exists = prev.materials.some((m) => m.trim().toLowerCase() === material.toLowerCase())
      const nextMaterials = exists ? prev.materials : [...prev.materials, material]
      const nextSuggestions = prev.materialSuggestions.filter((x) => x !== suggestion)
      return {
        ...prev,
        materials: nextMaterials,
        materialSuggestions: nextSuggestions,
      }
    })
  }

  function dismissMaterialSuggestion(suggestion: string) {
    setDraftStructured((prev) => ({
      ...prev,
      materialSuggestions: prev.materialSuggestions.filter((x) => x !== suggestion),
    }))
  }

  function applyMachineSuggestion(suggestion: string) {
    const entry = normalizeMachineSuggestionToEntry(suggestion)
    setDraftStructured((prev) => {
      const exists = prev.machineHours.some((x) => x.trim().toLowerCase() === entry.trim().toLowerCase())
      const nextMachineHours = exists ? prev.machineHours : [...prev.machineHours, entry]
      const nextSuggestions = prev.machineSuggestions.filter((x) => x !== suggestion)
      return {
        ...prev,
        machineHours: nextMachineHours,
        machineSuggestions: nextSuggestions,
      }
    })
  }

  function dismissMachineSuggestion(suggestion: string) {
    setDraftStructured((prev) => ({
      ...prev,
      machineSuggestions: prev.machineSuggestions.filter((x) => x !== suggestion),
    }))
  }

  async function doDownload(kind: 'pdf' | 'word') {
    if (!savedReportId) return
    setDlErr('')
    setDlBusy(true)
    try {
      const path =
        kind === 'pdf'
          ? `/api/reports/${savedReportId}/export/pdf`
          : `/api/reports/${savedReportId}/export/word`
      await downloadExport(path)
    } catch {
      setDlErr('Export konnte nicht erstellt werden.')
    } finally {
      setDlBusy(false)
    }
  }

  async function sendOffice() {
    if (!savedReportId) return
    setOfficeMsg('')
    setOfficeErr('')
    setOfficeBusy(true)
    try {
      const res = await api<{ ok: boolean; simulated: boolean; message: string }>(
        `/api/reports/${savedReportId}/send-office`,
        { method: 'POST' },
      )
      const text = res.message?.trim()
      if (text) setOfficeMsg(text)
      else
        setOfficeMsg(
          res.simulated
            ? 'SMTP ist noch nicht konfiguriert. Versand wurde simuliert.'
            : 'Bericht wurde ans Büro gesendet.',
        )
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setOfficeErr(m || 'Bericht konnte nicht gesendet werden.')
    } finally {
      setOfficeBusy(false)
    }
  }

  return (
    <div key={`preview-wake-${pageWakeKey}`} className="overflow-x-hidden">
      <PageTitle
        title="Tagesbericht"
        subtitle={
          savedReportId
            ? 'Fotos, Unterschrift & Versand'
            : isEditMode
              ? 'Bericht bearbeiten'
              : 'Prüfen & anpassen'
        }
      />
      {!savedReportId ? (
        <p className="mb-2 text-center text-sm text-zinc-500">
          {isEditMode
            ? 'Änderungen prüfen und speichern — Fotos & Unterschriften bleiben erhalten.'
            : 'Bitte prüfen und bei Bedarf anpassen — im nächsten Schritt Fotos & Unterschrift.'}
        </p>
      ) : null}
      {dirty && !savedReportId ? (
        <p className="mb-3 text-center text-sm text-amber-400">Änderungen noch nicht gespeichert</p>
      ) : null}
      {!dirty && savedReportId && saveMsg ? (
        <p className="mb-3 text-center text-sm text-emerald-400/90">{saveMsg}</p>
      ) : null}

      {logoUrl ? (
        <div className="mb-4 flex justify-center">
          <img src={resolveBackendPublicUrl(logoUrl) ?? logoUrl} alt="" className="h-14 w-auto object-contain opacity-90" />
        </div>
      ) : null}

      <Card className="mb-4 space-y-4">
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Firma</span>
            <span className="text-right font-medium text-white">{companyName}</span>
          </div>
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Baustelle</span>
            <span className="text-right text-white">{st.projectName}</span>
          </div>
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Kunde</span>
            <span className="text-right text-white">{st.customerName}</span>
          </div>
          <div className="flex justify-between gap-2 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Datum</span>
            <span className="text-right text-white">{st.date}</span>
          </div>
          <div className="flex gap-3 border-b border-zinc-800 pb-2">
            <span className="text-zinc-500 shrink-0 pt-0.5">Mitarbeiter</span>
            <div className="min-w-0 flex-1 text-right font-medium text-white">
              {metaEditable ? (
                <div className="space-y-2 text-left">
                  {roster.map((e) => {
                    const checked = draftMeta.employeeIds.includes(e.id)
                    return (
                      <label
                        key={e.id}
                        className="flex cursor-pointer items-center gap-2 rounded-xl border border-transparent bg-black/40 px-2.5 py-2 ring-1 ring-white/[0.08]"
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4 accent-orange-500"
                          checked={checked}
                          disabled={writeBlocked}
                          onChange={() => {
                            setDraftMeta((prev) => {
                              const nextIds = checked
                                ? prev.employeeIds.filter((id) => id !== e.id)
                                : [...prev.employeeIds, e.id]
                              const idSet = new Set(nextIds)
                              const nextNames = roster
                                .filter((row) => idSet.has(row.id))
                                .map((row) => row.name)
                              const nextTimes = { ...prev.employeeTimesById }
                              if (!checked && prev.perEmployeeTimes) {
                                nextTimes[e.id] =
                                  nextTimes[e.id] ??
                                  defaultEmployeeTimeSlot(
                                    e.id,
                                    prev.startTime,
                                    prev.endTime,
                                    prev.breakMinutes,
                                  )
                              }
                              return {
                                ...prev,
                                employeeIds: nextIds,
                                employees: nextNames,
                                employeeTimesById: nextTimes,
                                perEmployeeTimes:
                                  prev.perEmployeeTimes && nextIds.length >= 2
                                    ? prev.perEmployeeTimes
                                    : false,
                              }
                            })
                          }}
                        />
                        <span className="text-sm font-normal text-white">{e.name}</span>
                      </label>
                    )
                  })}
                  {roster.length === 0 ? (
                    <p className="text-sm font-normal text-zinc-500">
                      {draftMeta.employees.length
                        ? draftMeta.employees.join(', ')
                        : 'Keine aktiven Mitarbeitenden.'}
                    </p>
                  ) : null}
                </div>
              ) : (
                <p>{st.employees.length ? st.employees.join(', ') : 'Keine Angabe'}</p>
              )}
            </div>
          </div>
          <div className="border-b border-zinc-800 pb-2">
            <span className="text-zinc-500">Arbeitszeit</span>
            {metaEditable ? (
              <div className="mt-2 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <label className="block text-left">
                    <span className="text-xs text-zinc-500">Start</span>
                    <input
                      type="time"
                      className={`${inputClass} disabled:opacity-60`}
                      value={draftMeta.startTime}
                      disabled={writeBlocked}
                      onChange={(e) =>
                        setDraftMeta((prev) => ({ ...prev, startTime: e.target.value }))
                      }
                    />
                  </label>
                  <label className="block text-left">
                    <span className="text-xs text-zinc-500">Ende</span>
                    <input
                      type="time"
                      className={`${inputClass} disabled:opacity-60`}
                      value={draftMeta.endTime}
                      disabled={writeBlocked}
                      onChange={(e) =>
                        setDraftMeta((prev) => ({ ...prev, endTime: e.target.value }))
                      }
                    />
                  </label>
                </div>
                <label className="block text-left">
                  <span className="text-xs text-zinc-500">Pause</span>
                  <select
                    className={`${inputClass} disabled:opacity-60`}
                    value={draftMeta.breakMinutes}
                    disabled={writeBlocked}
                    onChange={(e) =>
                      setDraftMeta((prev) => ({
                        ...prev,
                        breakMinutes: Number(e.target.value),
                      }))
                    }
                  >
                    <option value={0}>Keine Pause</option>
                    <option value={30}>30 Minuten</option>
                    <option value={45}>45 Minuten</option>
                    <option value={60}>60 Minuten</option>
                    <option value={90}>90 Minuten</option>
                  </select>
                </label>
                {draftMeta.employeeIds.length >= 2 ? (
                  <div className="space-y-3 text-left">
                    {draftMeta.perEmployeeTimes ? (
                      <>
                        <button
                          type="button"
                          className="text-sm font-medium text-orange-400 hover:underline disabled:opacity-60"
                          disabled={writeBlocked}
                          onClick={() =>
                            setDraftMeta((prev) => ({ ...prev, perEmployeeTimes: false }))
                          }
                        >
                          Alle gleiche Zeit (wie oben)
                        </button>
                        <div className="space-y-3">
                          {roster
                            .filter((e) => draftMeta.employeeIds.includes(e.id))
                            .map((e) => {
                              const slot =
                                draftMeta.employeeTimesById[e.id] ??
                                defaultEmployeeTimeSlot(
                                  e.id,
                                  draftMeta.startTime,
                                  draftMeta.endTime,
                                  draftMeta.breakMinutes,
                                )
                              return (
                                <div
                                  key={e.id}
                                  className="rounded-2xl border border-white/[0.08] bg-black/40 px-3 py-3"
                                >
                                  <p className="text-sm font-medium text-zinc-200">{e.name}</p>
                                  <div className="mt-2 grid grid-cols-2 gap-2">
                                    <label className="block">
                                      <span className="text-xs text-zinc-500">Start</span>
                                      <input
                                        type="time"
                                        className={`${inputClass} disabled:opacity-60`}
                                        value={slot.startTime}
                                        disabled={writeBlocked}
                                        onChange={(ev) =>
                                          setDraftMeta((prev) => ({
                                            ...prev,
                                            employeeTimesById: {
                                              ...prev.employeeTimesById,
                                              [e.id]: {
                                                ...slot,
                                                startTime: ev.target.value,
                                                employeeId: e.id,
                                              },
                                            },
                                          }))
                                        }
                                      />
                                    </label>
                                    <label className="block">
                                      <span className="text-xs text-zinc-500">Ende</span>
                                      <input
                                        type="time"
                                        className={`${inputClass} disabled:opacity-60`}
                                        value={slot.endTime}
                                        disabled={writeBlocked}
                                        onChange={(ev) =>
                                          setDraftMeta((prev) => ({
                                            ...prev,
                                            employeeTimesById: {
                                              ...prev.employeeTimesById,
                                              [e.id]: {
                                                ...slot,
                                                endTime: ev.target.value,
                                                employeeId: e.id,
                                              },
                                            },
                                          }))
                                        }
                                      />
                                    </label>
                                  </div>
                                  <label className="mt-2 block">
                                    <span className="text-xs text-zinc-500">Pause</span>
                                    <select
                                      className={`${inputClass} disabled:opacity-60`}
                                      value={slot.breakMinutes}
                                      disabled={writeBlocked}
                                      onChange={(ev) =>
                                        setDraftMeta((prev) => ({
                                          ...prev,
                                          employeeTimesById: {
                                            ...prev.employeeTimesById,
                                            [e.id]: {
                                              ...slot,
                                              breakMinutes: Number(ev.target.value),
                                              employeeId: e.id,
                                            },
                                          },
                                        }))
                                      }
                                    >
                                      <option value={0}>Keine Pause</option>
                                      <option value={30}>30 Minuten</option>
                                      <option value={45}>45 Minuten</option>
                                      <option value={60}>60 Minuten</option>
                                      <option value={90}>90 Minuten</option>
                                    </select>
                                  </label>
                                </div>
                              )
                            })}
                        </div>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="text-sm font-medium text-orange-400 hover:underline disabled:opacity-60"
                        disabled={writeBlocked}
                        onClick={() =>
                          setDraftMeta((prev) => {
                            const next: Record<string, EmployeeTimeSlot> = {
                              ...prev.employeeTimesById,
                            }
                            for (const id of prev.employeeIds) {
                              next[id] =
                                next[id] ??
                                defaultEmployeeTimeSlot(
                                  id,
                                  prev.startTime,
                                  prev.endTime,
                                  prev.breakMinutes,
                                )
                            }
                            return {
                              ...prev,
                              perEmployeeTimes: true,
                              employeeTimesById: next,
                            }
                          })
                        }
                      >
                        Zeiten einzeln anpassen
                      </button>
                    )}
                  </div>
                ) : null}
              </div>
            ) : (
              <span className="mt-1 block min-w-0 whitespace-pre-wrap text-right text-white">
                {formatArbeitszeitWithHours(st.startTime, st.endTime)}
                {`\nPause: ${defaultBreakMinutes(st)} Min.`}
                {st.structured.workTime ? `\n${st.structured.workTime}` : ''}
                {Array.isArray(st.employeeTimes) && st.employeeTimes.length > 0
                  ? `\n\nStunden je Mitarbeiter:\n${(() => {
                      const ids = defaultEmployeeIds(st)
                      const names = st.employees || []
                      const nameById = new Map(ids.map((id, i) => [id, names[i] || id]))
                      return st.employeeTimes
                        .map((row) => {
                          const name = nameById.get(row.employeeId) || row.employeeId
                          return `• ${name}: ${formatArbeitszeitWithHours(row.startTime, row.endTime)} (Pause ${row.breakMinutes} Min.)`
                        })
                        .join('\n')
                    })()}`
                  : ''}
              </span>
            )}
          </div>
          <div className="flex justify-between gap-2">
            <span className="text-zinc-500">Ausgabeformat</span>
            <span className="text-right text-white">{st.exportFormat}</span>
          </div>
          {st.seriesMode ? (
            <div className="flex justify-between gap-2 border-t border-zinc-800 pt-2">
              <span className="text-zinc-500">Art</span>
              <span className="text-right font-medium text-orange-300/95">Folgebericht (zur laufenden Baustelle)</span>
            </div>
          ) : null}
        </div>
      </Card>

      <Card className="space-y-6">
        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">
            Zusammenfassung
          </h3>
          <textarea
            className={`${textareaClass} disabled:opacity-60`}
            rows={5}
            value={s.summary}
            disabled={Boolean(savedReportId)}
            onChange={(e) =>
              setDraftStructured((prev) => ({ ...prev, summary: e.target.value }))
            }
            placeholder="Zusammenfassung bearbeiten"
          />
        </section>

        <EditableArraySection
          title="Tätigkeiten"
          items={s.activities}
          onChange={(next) =>
            setDraftStructured((prev) => ({ ...prev, activities: next }))
          }
          addLabel="+ Tätigkeit hinzufügen"
          disabled={Boolean(savedReportId)}
        />
        <EditableArraySection
          title="Material"
          items={s.materials}
          onChange={(next) =>
            setDraftStructured((prev) => ({ ...prev, materials: next }))
          }
          addLabel="+ Materialpunkt hinzufügen"
          disabled={Boolean(savedReportId)}
        />
        <MaterialSuggestionsSection
          suggestions={s.materialSuggestions}
          materials={s.materials}
          disabled={Boolean(savedReportId)}
          onApply={applyMaterialSuggestion}
          onDismiss={dismissMaterialSuggestion}
        />
        <MachineHoursSection
          items={s.machineHours}
          suggestions={s.machineSuggestions}
          disabled={Boolean(savedReportId)}
          onChange={(next) =>
            setDraftStructured((prev) => ({ ...prev, machineHours: next }))
          }
          onApplySuggestion={applyMachineSuggestion}
          onDismissSuggestion={dismissMachineSuggestion}
        />
        <EditableArraySection
          title="Probleme"
          items={s.problems}
          onChange={(next) =>
            setDraftStructured((prev) => ({ ...prev, problems: next }))
          }
          addLabel="+ Problem hinzufügen"
          disabled={Boolean(savedReportId)}
        />
        <EditableArraySection
          title="Offene Punkte"
          items={s.openItems}
          onChange={(next) =>
            setDraftStructured((prev) => ({ ...prev, openItems: next }))
          }
          addLabel="+ Offenen Punkt hinzufügen"
          disabled={Boolean(savedReportId)}
        />

        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">
            Kundengespräch
          </h3>
          <textarea
            className={`${textareaClass} disabled:opacity-60`}
            rows={5}
            value={s.customerTalk}
            disabled={Boolean(savedReportId)}
            onChange={(e) =>
              setDraftStructured((prev) => ({ ...prev, customerTalk: e.target.value }))
            }
            placeholder="Kundengespräch bearbeiten"
          />
        </section>

        {st.notes && st.notes.trim() ? (
          <section>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">Besonderheiten</h3>
            <p className="mt-2 whitespace-pre-wrap text-zinc-300">{st.notes}</p>
          </section>
        ) : null}

        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">Rohtext</h3>
          <p className="mt-2 whitespace-pre-wrap text-zinc-400">{st.rawText}</p>
        </section>

        {savedReportId ? (
          <section className="border-t border-zinc-800 pt-4">
            <p className="mb-3 text-xs leading-relaxed text-zinc-500">
              Bericht gespeichert. Jetzt Fotos aufnehmen und Unterschriften erfassen — alles wird direkt im
              Bericht gebündelt. Unten kannst du den Bericht senden oder herunterladen.
            </p>
            <ReportPhotosSection
              reportId={savedReportId}
              enabled
              iosGalleryRedirect
              onUploadComplete={() => setPageWakeKey((k) => k + 1)}
            />

            <ReportSignaturesSection
              reportId={savedReportId}
              enabled
              customerName={st.customerName}
            />
          </section>
        ) : (
          <section className="border-t border-zinc-800 pt-4">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-orange-400">
              Fotos & Unterschrift <span className="font-normal normal-case text-zinc-500">(optional)</span>
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-zinc-500">
              Nach dem Speichern kannst du — wenn nötig — Fotos aufnehmen und Unterschriften erfassen. Wer das
              nicht braucht, sendet den Bericht direkt ans Büro.
            </p>
          </section>
        )}
      </Card>

      <div className="mt-6 space-y-3">
        {!savedReportId ? (
          <>
            <BigButton
              type="button"
              disabled={writeBlocked || saveBusy}
              onClick={() => onSave(logoUrl, companyName, officeEmail)}
            >
              {saveBusy ? '…' : isEditMode ? 'Änderungen speichern' : 'Bericht speichern'}
            </BigButton>
            <p className="text-center text-xs text-zinc-500">
              {isEditMode
                ? 'Nach dem Speichern landest du wieder in der Berichtansicht.'
                : 'Fotos & Unterschrift sind optional und folgen direkt nach dem Speichern.'}
            </p>
            {isEditMode ? (
              <BigButton variant="secondary" type="button" onClick={() => nav(`/berichte/${st.existingReportId}`)}>
                Abbrechen
              </BigButton>
            ) : null}
          </>
        ) : null}

        {saveErr ? <p className="text-center text-sm text-red-400">{saveErr}</p> : null}
        {saveMsg ? <p className="text-center text-sm text-emerald-400/90">{saveMsg}</p> : null}
        {timeBookingMsg ? <p className="text-center text-sm text-emerald-400/90">{timeBookingMsg}</p> : null}
        {timeBookingWarn ? <p className="text-center text-sm text-amber-400/90">{timeBookingWarn}</p> : null}
        {officeMsg ? <p className="text-center text-sm text-orange-300">{officeMsg}</p> : null}
        {officeErr ? <p className="text-center text-sm text-red-400">{officeErr}</p> : null}

        {savedReportId ? (
          <>
            <BigButton
              type="button"
              disabled={writeBlocked || officeBusy || dlBusy}
              onClick={() => void sendOffice()}
            >
              {officeBusy ? '…' : 'Ans Büro senden'}
            </BigButton>

            <div className="overflow-hidden rounded-2xl ring-1 ring-white/[0.08]">
              <button
                type="button"
                aria-expanded={moreOpen}
                onClick={() => setMoreOpen((o) => !o)}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-medium text-zinc-400 transition hover:bg-white/[0.04]"
              >
                <span>Weitere Optionen</span>
                <span className="text-zinc-500">{moreOpen ? '▴' : '▾'}</span>
              </button>
              {moreOpen ? (
                <div className="space-y-2 border-t border-white/[0.06] px-3 py-3">
                  <BigButton
                    variant="secondary"
                    type="button"
                    disabled={dlBusy || officeBusy}
                    onClick={() => void doDownload('pdf')}
                  >
                    {dlBusy ? '…' : 'PDF herunterladen'}
                  </BigButton>
                  <BigButton
                    variant="secondary"
                    type="button"
                    disabled={dlBusy || officeBusy}
                    onClick={() => void doDownload('word')}
                  >
                    {dlBusy ? '…' : 'Word herunterladen'}
                  </BigButton>
                  <BigButton variant="secondary" type="button" onClick={() => onCopy(companyName, draftStructured)}>
                    Als Text kopieren
                  </BigButton>
                  {savedReportId ? (
                    <BigButton
                      variant="secondary"
                      type="button"
                      onClick={() => {
                        const state: FeedbackNavState = {
                          category: 'Problem',
                          reportId: savedReportId,
                          reportLabel: `${st.projectName} · ${st.date}`,
                          prefill: `Betreffender Bericht: ${st.projectName}, ${st.date}\n\n`,
                        }
                        nav('/feedback', { state })
                      }}
                    >
                      Problem melden
                    </BigButton>
                  ) : null}
                </div>
              ) : null}
            </div>
          </>
        ) : null}
        {dlErr ? <p className="text-center text-sm text-red-400">{dlErr}</p> : null}

        {savedReportId ? (
          <div className="pt-2 text-center">
            <Link className="text-sm font-medium text-orange-400 hover:underline" to="/berichte">
              Zu den gespeicherten Berichten
            </Link>
          </div>
        ) : null}
      </div>
    </div>
  )
}

function ReportPhotoRecoveryPage({ reportId }: { reportId: string }) {
  const nav = useNavigate()
  const [pageWakeKey, setPageWakeKey] = useState(0)

  return (
    <div key={`photo-recovery-wake-${pageWakeKey}`} className="overflow-x-hidden">
      <PageTitle title="Baustellenfotos" subtitle="Bericht gespeichert — Fotos hier anfügen" />
      <p className="mb-4 text-center text-sm text-zinc-500">
        Nach der Kamera kehrt die App manchmal hierher zurück. Ihr Bericht ist gespeichert.
      </p>
      <Card>
        <ReportPhotosSection
          reportId={reportId}
          enabled
          iosGalleryRedirect
          onUploadComplete={() => setPageWakeKey((k) => k + 1)}
        />
        <ReportSignaturesSection reportId={reportId} enabled embedded />
      </Card>
      <div className="mt-6 space-y-3">
        <BigButton variant="secondary" type="button" onClick={() => nav(`/berichte/${reportId}`)}>
          Zum Bericht
        </BigButton>
        <BigButton variant="secondary" type="button" onClick={() => nav('/berichte')}>
          Alle Berichte
        </BigButton>
      </div>
    </div>
  )
}

export function ReportPreviewPage() {
  const nav = useNavigate()
  const location = useLocation()
  const st = location.state as ReportPreviewState | undefined

  const reportSyncKey =
    st
      ? `${st.projectId}|${st.date}|${st.startTime}|${st.endTime}|${defaultBreakMinutes(st)}|${defaultEmployeeIds(st).join(',')}|${st.exportFormat}|${st.rawText.length}|${JSON.stringify(st.structured)}`
      : ''

  const lastReportKeyRef = useRef<string>('')

  const [draftStructured, setDraftStructured] = useState<StructuredPayload>(() =>
    st ? cloneStructured(st.structured) : defaultEmptyStructured(),
  )
  const [savedBaseline, setSavedBaseline] = useState<StructuredPayload>(() =>
    st ? cloneStructured(st.structured) : defaultEmptyStructured(),
  )
  const [draftMeta, setDraftMeta] = useState<DraftMeta>(() =>
    st ? metaFromState(st) : emptyDraftMeta(),
  )
  const [metaBaseline, setMetaBaseline] = useState<DraftMeta>(() =>
    st ? metaFromState(st) : emptyDraftMeta(),
  )
  const [savedReportId, setSavedReportId] = useState<string | null>(null)
  const [saveBusy, setSaveBusy] = useState(false)
  const [saveErr, setSaveErr] = useState('')
  const [saveMsg, setSaveMsg] = useState('')
  const [timeBookingMsg, setTimeBookingMsg] = useState('')
  const [timeBookingWarn, setTimeBookingWarn] = useState('')

  useLayoutEffect(() => {
    if (!st || !reportSyncKey) return
    if (lastReportKeyRef.current === reportSyncKey) return
    lastReportKeyRef.current = reportSyncKey
    const c = cloneStructured(st.structured)
    setDraftStructured(c)
    setSavedBaseline(c)
    const m = metaFromState(st)
    setDraftMeta(m)
    setMetaBaseline(m)
    setSaveMsg('')
    setSaveErr('')

    // Edit-Modus: nie aus Create-Persist wiederherstellen — Felder bleiben editierbar.
    if (st.existingReportId) {
      setSavedReportId(null)
      return
    }

    const persisted = loadReportPreviewPersist()
    if (persisted?.reportSyncKey === reportSyncKey && persisted.savedReportId) {
      setSavedReportId(persisted.savedReportId)
      setSaveMsg('Bericht gespeichert')
    } else {
      setSavedReportId(null)
      if (persisted && persisted.reportSyncKey !== reportSyncKey) {
        clearReportPreviewPersist()
      }
    }
  }, [reportSyncKey, st])

  const dirty = useMemo(() => {
    const structDirty = !structuredEqual(draftStructured, savedBaseline)
    if (!st?.existingReportId) return structDirty
    return structDirty || !metaEqual(draftMeta, metaBaseline)
  }, [draftStructured, savedBaseline, draftMeta, metaBaseline, st?.existingReportId])

  async function saveReport(logoUrl: string | null, companyName: string, officeEmail: string) {
    if (!st) return
    setSaveErr('')
    setSaveMsg('')
    setTimeBookingMsg('')
    setTimeBookingWarn('')
    setSaveBusy(true)
    try {
      const s = draftStructured
      const isEdit = Boolean(st.existingReportId)
      const employeeTimes = isEdit
        ? buildEmployeeTimesPayload(
            draftMeta.perEmployeeTimes,
            draftMeta.employeeIds,
            draftMeta.employeeTimesById,
            {
              startTime: draftMeta.startTime,
              endTime: draftMeta.endTime,
              breakMinutes: draftMeta.breakMinutes,
            },
          )
        : Array.isArray(st.employeeTimes)
          ? st.employeeTimes
          : []
      const payload = {
        companyName,
        companyLogoUrl: resolveBackendPublicUrl(logoUrl),
        officeEmail,
        projectId: st.projectId,
        projectName: st.projectName,
        customerName: st.customerName,
        projectAddress: st.projectAddress || '',
        projectCity: st.projectCity || '',
        date: st.date,
        // Edit: Zeiten/Mitarbeiter aus Draft — Create: unverändert aus st.
        employees: isEdit ? draftMeta.employees : st.employees,
        employeeIds: isEdit ? draftMeta.employeeIds : defaultEmployeeIds(st),
        startTime: isEdit ? draftMeta.startTime : st.startTime,
        endTime: isEdit ? draftMeta.endTime : st.endTime,
        breakMinutes: isEdit ? draftMeta.breakMinutes : defaultBreakMinutes(st),
        employeeTimes,
        exportFormat: st.exportFormat,
        rawText: st.rawText,
        seriesMode: Boolean(st.seriesMode),
        notes: st.notes ?? '',
        structured: {
          summary: s.summary,
          activities: s.activities,
          materials: s.materials,
          materialSuggestions: s.materialSuggestions,
          machineSuggestions: s.machineSuggestions,
          machineHours: s.machineHours,
          problems: s.problems,
          openItems: s.openItems,
          customerTalk: s.customerTalk,
        } satisfies StructuredPayload,
      }

      // Edit: bestehenden Bericht aktualisieren (Create-Pfad darunter unverändert).
      if (st.existingReportId) {
        await api<{ id: string }>(`/api/reports/${encodeURIComponent(st.existingReportId)}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
        setSavedBaseline(cloneStructured(draftStructured))
        setMetaBaseline({ ...draftMeta })
        setSaveMsg('Änderungen gespeichert')
        nav(`/berichte/${encodeURIComponent(st.existingReportId)}`, { replace: true })
        return
      }

      const doc = await api<{
        id: string
        timeBooking?: {
          created?: number
          hoursPerEmployee?: number | null
          hoursByEmployee?: { name?: string; hours?: number }[]
          hoursUniform?: boolean
          bookedNames?: string[]
          skippedNames?: string[]
          reason?: string | null
        }
      }>('/api/reports', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setSavedReportId(doc.id)
      setSavedBaseline(cloneStructured(draftStructured))
      setSaveMsg('Bericht gespeichert')
      const tb = timeBookingMessage(doc.timeBooking)
      setTimeBookingMsg(tb.ok)
      setTimeBookingWarn(tb.warn)
      if (reportSyncKey) {
        saveReportPreviewPersist({ reportSyncKey, savedReportId: doc.id })
      }
    } catch {
      setSaveErr(
        st.existingReportId
          ? 'Änderungen konnten nicht gespeichert werden.'
          : 'Bericht konnte nicht gespeichert werden.',
      )
    } finally {
      setSaveBusy(false)
    }
  }

  function copyText(companyName: string, structured: StructuredPayload) {
    if (!st) return
    const t = buildPlainText(companyName, st, structured)
    void navigator.clipboard.writeText(t)
  }

  if (!st) {
    const persisted = loadReportPreviewPersist()
    if (persisted?.savedReportId) {
      return <ReportPhotoRecoveryPage reportId={persisted.savedReportId} />
    }
    return (
      <div>
        <PageTitle title="Vorschau" subtitle="Kein Bericht geladen" />
        <BigButton onClick={() => nav('/bericht')}>Zur Erfassung</BigButton>
      </div>
    )
  }

  return (
    <ReportPreviewInner
      st={st}
      draftStructured={draftStructured}
      setDraftStructured={setDraftStructured}
      draftMeta={draftMeta}
      setDraftMeta={setDraftMeta}
      setMetaBaseline={setMetaBaseline}
      savedReportId={savedReportId}
      onSave={saveReport}
      onCopy={copyText}
      saveBusy={saveBusy}
      saveErr={saveErr}
      saveMsg={saveMsg}
      timeBookingMsg={timeBookingMsg}
      timeBookingWarn={timeBookingWarn}
      dirty={dirty}
    />
  )
}
