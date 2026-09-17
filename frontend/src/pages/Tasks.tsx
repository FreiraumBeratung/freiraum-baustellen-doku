import { useCallback, useEffect, useMemo, useState } from 'react'
import { MapPin } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { api, downloadExport } from '../api/client'
import { ReportPhotosSection } from '../components/ReportPhotosSection'
import { TaskSignatureSection } from '../components/TaskSignatureSection'
import { TaskPushOptIn } from '../components/TaskPushOptIn'
import { TasksWeekView } from '../components/TasksWeekView'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import {
  addDaysIso,
  formatDayMonth,
  startOfWeekMonday,
  todayIsoLocal,
  weekDates,
} from '../utils/taskWeek'

type Project = { id: string; name: string; customer?: string; status?: string }
type Employee = { id: string; name: string; active: boolean }

type TaskProgress = {
  id: string
  employeeId?: string
  actorName: string
  amount: number
  createdAt: string
  source?: string
}

export type SiteTask = {
  id: string
  projectId: string
  projectName: string
  projectAddress?: string
  projectCity?: string
  title: string
  dueDate: string
  assigneeIds: string[]
  assigneeNames: string[]
  status: 'open' | 'done'
  createdAt: string
  completedAt?: string | null
  targetQuantity?: number | null
  actualQuantity?: number | null
  remainingQuantity?: number | null
  unit?: string
  progress?: TaskProgress[]
  photoCount?: number
  hasSignature?: boolean
  completionSummary?: string
}

const TASK_UNITS = ['m²', 'm³', 'm', 'Stk', 'lfm', 'Std'] as const

type DraftLine = {
  key: string
  title: string
  targetQty: string
  unit: (typeof TASK_UNITS)[number]
}

function newDraftLine(): DraftLine {
  return {
    key: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: '',
    targetQty: '',
    unit: 'm²',
  }
}

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || '').trim())
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

function dateChips(): { label: string; iso: string }[] {
  const today = todayIsoLocal()
  return [
    { label: 'Heute', iso: today },
    { label: 'Morgen', iso: addDaysIso(today, 1) },
    { label: formatDayMonth(addDaysIso(today, 2)), iso: addDaysIso(today, 2) },
    { label: formatDayMonth(addDaysIso(today, 3)), iso: addDaysIso(today, 3) },
  ]
}

function formatGroupCompletionSummary(tasks: SiteTask[]): string {
  const done = tasks.filter((t) => t.status === 'done')
  if (!done.length) return ''
  if (done.length === 1) return String(done[0]?.completionSummary || '').trim()
  const first = done[0] as SiteTask
  const labels = done.map((t) => {
    const title = t.title.trim() || 'Aufgabe'
    if (t.targetQuantity == null) return `„${title}“`
    const qty = formatQty(t.actualQuantity ?? t.targetQuantity)
    return `„${title}“ (${qty} ${t.unit || 'm²'})`
  })
  const listed =
    labels.length === 2 ? `${labels[0]} und ${labels[1]}` : `${labels.slice(0, -1).join(', ')} und ${labels[labels.length - 1]}`
  const who = joinNamesDe([...new Set(done.flatMap((t) => t.assigneeNames || []))])
  return (
    `Am ${formatDateDe(first.dueDate)} wurden auf der Baustelle ${first.projectName || 'Baustelle'} ` +
    `folgende Tätigkeiten erledigt: ${listed}. Ausgeführt von ${who}.`
  )
}

function formatQty(value: number | null | undefined): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0'
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(n)
}

function joinNamesDe(names: string[]): string {
  const clean = names.map((n) => n.trim()).filter(Boolean)
  if (clean.length === 0) return 'Mitarbeiter'
  if (clean.length === 1) return clean[0] as string
  if (clean.length === 2) return `${clean[0]} und ${clean[1]}`
  return `${clean.slice(0, -1).join(', ')} und ${clean[clean.length - 1]}`
}

function createdTaskMessage(
  titles: string[],
  site: string,
  names: string[],
  dateIso: string,
): string {
  const who = joinNamesDe(names)
  const verb = names.length > 1 ? 'wurden' : 'wurde'
  const siteName = site.trim() || 'Baustelle'
  const when = formatDateDe(dateIso)
  if (titles.length === 1) {
    return `${who} ${verb} zum ${titles[0]} bei ${siteName} für den ${when} eingeplant.`
  }
  return `${who} ${verb} zu ${titles.join(', ')} bei ${siteName} für den ${when} eingeplant.`
}

function parseQty(raw: string): number | null {
  const cleaned = String(raw || '').trim().replace(',', '.')
  if (!cleaned) return null
  const n = Number(cleaned)
  if (!Number.isFinite(n) || n <= 0) return null
  return n
}

function formatProjectLocation(address?: string, city?: string): string {
  return [address, city].map((s) => String(s || '').trim()).filter(Boolean).join(', ')
}

function mapsUrlForLocation(query: string): string {
  const q = query.trim()
  if (!q) return ''
  const enc = encodeURIComponent(q)
  if (typeof navigator === 'undefined') {
    return `https://www.google.com/maps/search/?api=1&query=${enc}`
  }
  const ua = navigator.userAgent || ''
  const iOS =
    /iPhone|iPad|iPod/i.test(ua) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  if (iOS) return `https://maps.apple.com/?q=${enc}`
  return `https://www.google.com/maps/search/?api=1&query=${enc}`
}

function TaskAddressLink({ loc }: { loc: string }) {
  const href = mapsUrlForLocation(loc)
  if (!href) return null
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className="mt-1 inline-flex max-w-full items-center gap-1 text-xs text-zinc-500 underline decoration-white/15 underline-offset-2 transition hover:text-orange-300/85"
      aria-label={`Adresse in Karten öffnen: ${loc}`}
    >
      <MapPin className="h-3 w-3 shrink-0 opacity-70" strokeWidth={1.75} aria-hidden />
      <span className="min-w-0 truncate">{loc}</span>
    </a>
  )
}

function taskGroupKey(t: Pick<SiteTask, 'projectId' | 'projectName' | 'dueDate'>): string {
  return `${t.projectId || t.projectName || ''}|${t.dueDate || ''}`
}

type TaskGroup = {
  key: string
  projectId: string
  projectName: string
  projectAddress?: string
  projectCity?: string
  dueDate: string
  tasks: SiteTask[]
}

function groupTasksBySiteDay(list: SiteTask[]): TaskGroup[] {
  const map = new Map<string, TaskGroup>()
  const order: string[] = []
  for (const t of list) {
    const key = taskGroupKey(t)
    let group = map.get(key)
    if (!group) {
      group = {
        key,
        projectId: t.projectId,
        projectName: t.projectName || 'Baustelle',
        projectAddress: t.projectAddress,
        projectCity: t.projectCity,
        dueDate: t.dueDate,
        tasks: [],
      }
      map.set(key, group)
      order.push(key)
    }
    group.tasks.push(t)
  }
  return order.map((key) => map.get(key) as TaskGroup)
}

function MiniQtyBar({ t }: { t: SiteTask }) {
  if (t.targetQuantity == null) return null
  const pct = Math.min(
    100,
    Math.max(0, ((Number(t.actualQuantity) || 0) / (Number(t.targetQuantity) || 1)) * 100),
  )
  return (
    <div className="mt-2">
      <p className="text-[0.7rem] text-zinc-400">
        {formatQty(t.actualQuantity)} / {formatQty(t.targetQuantity)} {t.unit || 'm²'}
      </p>
      <div className="mt-1 h-1 overflow-hidden rounded-full bg-zinc-800">
        <div className="h-full rounded-full bg-orange-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function TaskCard({
  t,
  expanded,
  showSite,
  embedded,
  onToggle,
  isCompanyOwner,
  writeBlocked,
  busy,
  progressDraft,
  onProgressDraft,
  onAddProgress,
  onComplete,
  onReopen,
  onDelete,
  mediaOpen,
  onToggleMedia,
  onMediaChanged,
  reportOpen,
  onToggleReport,
  compactOnly,
}: {
  t: SiteTask
  expanded: boolean
  showSite: boolean
  embedded?: boolean
  onToggle: () => void
  isCompanyOwner: boolean
  writeBlocked: boolean
  busy: boolean
  progressDraft: string
  onProgressDraft: (value: string) => void
  onAddProgress: () => void
  onComplete: () => void
  onReopen: () => void
  onDelete: () => void
  mediaOpen: boolean
  onToggleMedia: () => void
  onMediaChanged: () => void
  reportOpen: boolean
  onToggleReport: () => void
  compactOnly?: boolean
}) {
  const loc = formatProjectLocation(t.projectAddress, t.projectCity)
  const unit = t.unit || 'm²'
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const [pdfBusy, setPdfBusy] = useState(false)
  const wrapClass = embedded
    ? 'space-y-2 py-1'
    : expanded
      ? 'space-y-3'
      : 'space-y-1 !px-4 !py-3.5'

  async function downloadCompletionPdf() {
    setOfficeErr('')
    setPdfBusy(true)
    try {
      await downloadExport(`/api/tasks/${encodeURIComponent(t.id)}/completion/export/pdf`)
    } catch {
      setOfficeErr('PDF konnte nicht erstellt werden.')
    } finally {
      setPdfBusy(false)
    }
  }

  async function sendCompletionOffice() {
    if (writeBlocked || officeBusy) return
    setOfficeMsg('')
    setOfficeErr('')
    setOfficeBusy(true)
    try {
      const res = await api<{ ok?: boolean; message?: string }>(
        `/api/tasks/${encodeURIComponent(t.id)}/completion/send-office`,
        { method: 'POST' },
      )
      setOfficeMsg(res.message?.trim() || 'Aufgabenabschluss wurde ans Büro gesendet.')
    } catch (ex) {
      setOfficeErr(ex instanceof Error ? ex.message : 'Versand fehlgeschlagen.')
    } finally {
      setOfficeBusy(false)
    }
  }

  const siteBlock =
    showSite ? (
      <>
        <p className="text-[0.7rem] font-medium uppercase tracking-wide text-orange-400/90">
          {t.projectName || 'Baustelle'}
        </p>
        {loc ? <TaskAddressLink loc={loc} /> : null}
      </>
    ) : null

  const head = compactOnly ? (
    <div>
      {siteBlock}
      <p className={`text-sm font-medium text-white ${showSite ? 'mt-1' : ''}`}>{t.title}</p>
      <p className="mt-1 text-xs text-zinc-500">
        Datum: {formatDateDe(t.dueDate)}
        {t.assigneeNames?.length ? ` · ${t.assigneeNames.join(', ')}` : ''}
      </p>
      <MiniQtyBar t={t} />
    </div>
  ) : (
    <button type="button" onClick={onToggle} className="block w-full text-left">
      {siteBlock}
      <p className={`text-sm font-medium text-white ${showSite ? 'mt-1' : ''}`}>{t.title}</p>
      <p className="mt-1 text-xs text-zinc-500">
        Datum: {formatDateDe(t.dueDate)}
        {t.assigneeNames?.length ? ` · ${t.assigneeNames.join(', ')}` : ''}
      </p>
      {expanded && t.status === 'open' && t.targetQuantity != null ? null : <MiniQtyBar t={t} />}
    </button>
  )

  const body = compactOnly || !expanded ? (
    head
  ) : (
    <>
      {head}
      {t.status === 'open' && t.targetQuantity != null ? (
        <div className="space-y-2 rounded-2xl border border-white/[0.06] bg-black/30 px-3 py-3">
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-sm font-medium text-zinc-100">
              {formatQty(t.actualQuantity)} / {formatQty(t.targetQuantity)} {unit}
            </p>
            <p className="text-xs text-zinc-400">
              Rest {formatQty(t.remainingQuantity)} {unit}
            </p>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
            <div
              className="h-full rounded-full bg-orange-500"
              style={{
                width: `${Math.min(
                  100,
                  Math.max(
                    0,
                    ((Number(t.actualQuantity) || 0) / (Number(t.targetQuantity) || 1)) * 100,
                  ),
                )}%`,
              }}
            />
          </div>
          {t.progress?.length ? (
            <ul className="space-y-1">
              {t.progress.map((p) => (
                <li key={p.id || `${p.actorName}-${p.createdAt}`} className="text-xs text-zinc-400">
                  {p.source === 'complete'
                    ? `${p.actorName}: Rest ${formatQty(p.amount)} ${unit} (erledigt)`
                    : `${p.actorName}: ${formatQty(p.amount)} ${unit}`}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-zinc-500">Noch kein Fortschritt gemeldet.</p>
          )}
          <div className="flex items-center gap-2 pt-1">
            <input
              type="text"
              inputMode="decimal"
              className="min-w-0 flex-1 rounded-xl border border-white/[0.1] bg-black/55 px-3 py-2 text-sm text-white outline-none focus:border-orange-500/65"
              value={progressDraft}
              onChange={(e) => onProgressDraft(e.target.value)}
              disabled={writeBlocked || busy}
            />
            <button
              type="button"
              disabled={writeBlocked || busy || !parseQty(progressDraft)}
              onClick={() => onAddProgress()}
              className="rounded-xl border border-orange-400/40 bg-orange-500/15 px-3 py-2 text-sm font-semibold text-orange-200 disabled:opacity-50"
            >
              Melden
            </button>
          </div>
        </div>
      ) : null}
      <div className="flex flex-wrap gap-1.5">
        {t.status === 'open' ? (
          <button
            type="button"
            disabled={writeBlocked || busy}
            onClick={() => onComplete()}
            className="rounded-xl border border-orange-400/40 bg-orange-500/15 px-2.5 py-1.5 text-xs font-semibold text-orange-200 disabled:opacity-50"
          >
            Erledigt ✓
          </button>
        ) : isCompanyOwner ? (
          <button
            type="button"
            disabled={writeBlocked || busy}
            onClick={() => onReopen()}
            className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-300 disabled:opacity-50"
          >
            Wieder öffnen
          </button>
        ) : (
          <span className="text-xs text-emerald-400/90">Erledigt</span>
        )}
        {isCompanyOwner ? (
          <button
            type="button"
            disabled={writeBlocked || busy}
            onClick={() => onDelete()}
            className="rounded-xl border border-red-500/30 bg-red-500/10 px-2.5 py-1.5 text-xs font-medium text-red-300/90 disabled:opacity-50"
          >
            Löschen
          </button>
        ) : null}
        {t.status === 'done' ? (
          <>
            <button
              type="button"
              onClick={() => onToggleMedia()}
              className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200"
            >
              {mediaOpen ? 'Fotos schließen' : `Fotos${t.photoCount ? ` (${t.photoCount})` : ''}`}
            </button>
            <button
              type="button"
              onClick={() => onToggleReport()}
              className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200"
            >
              {reportOpen ? 'Bericht schließen' : 'Bericht'}
            </button>
          </>
        ) : null}
      </div>
      {t.status === 'open' || mediaOpen ? (
        <div className="space-y-3 border-t border-white/[0.06] pt-3">
          <ReportPhotosSection
            reportId={null}
            taskId={t.id}
            enabled
            embedded
            iosGalleryRedirect
            initialOpen={mediaOpen}
            onUploadComplete={onMediaChanged}
          />
          <TaskSignatureSection taskId={t.id} onChanged={onMediaChanged} />
        </div>
      ) : null}
      {t.status === 'done' && reportOpen ? (
        <div className="space-y-2 border-t border-white/[0.06] pt-3">
          <p className="text-sm leading-relaxed text-zinc-300">
            {t.completionSummary?.trim() || 'Noch keine Zusammenfassung.'}
          </p>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              disabled={pdfBusy}
              onClick={() => void downloadCompletionPdf()}
              className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200 disabled:opacity-50"
            >
              {pdfBusy ? '…' : 'PDF'}
            </button>
            {isCompanyOwner ? (
              <button
                type="button"
                disabled={writeBlocked || officeBusy}
                onClick={() => void sendCompletionOffice()}
                className="rounded-xl border border-orange-400/40 bg-orange-500/15 px-2.5 py-1.5 text-xs font-semibold text-orange-200 disabled:opacity-50"
              >
                {officeBusy ? '…' : 'Ans Büro senden'}
              </button>
            ) : null}
          </div>
          {officeMsg ? <p className="text-xs text-emerald-400/90">{officeMsg}</p> : null}
          {officeErr ? <p className="text-xs text-red-400">{officeErr}</p> : null}
        </div>
      ) : null}
    </>
  )

  if (embedded) {
    return <div className={wrapClass}>{body}</div>
  }
  return <Card className={wrapClass}>{body}</Card>
}

function GroupDoneFooter({
  g,
  isCompanyOwner,
  writeBlocked,
  busy,
  mediaOpen,
  reportOpen,
  onToggleMedia,
  onToggleReport,
  onReopenAll,
  onDeleteAll,
  onMediaChanged,
}: {
  g: TaskGroup
  isCompanyOwner: boolean
  writeBlocked: boolean
  busy: boolean
  mediaOpen: boolean
  reportOpen: boolean
  onToggleMedia: () => void
  onToggleReport: () => void
  onReopenAll: () => void
  onDeleteAll: () => void
  onMediaChanged: () => void
}) {
  const [officeBusy, setOfficeBusy] = useState(false)
  const [officeMsg, setOfficeMsg] = useState('')
  const [officeErr, setOfficeErr] = useState('')
  const [pdfBusy, setPdfBusy] = useState(false)
  const photoCount = g.tasks.reduce((sum, t) => sum + (t.photoCount || 0), 0)
  const summary = formatGroupCompletionSummary(g.tasks)
  const qs = `projectId=${encodeURIComponent(g.projectId)}&dueDate=${encodeURIComponent(g.dueDate)}`

  async function downloadPdf() {
    setOfficeErr('')
    setPdfBusy(true)
    try {
      await downloadExport(`/api/tasks/completion-bundle/export/pdf?${qs}`)
    } catch {
      setOfficeErr('PDF konnte nicht erstellt werden.')
    } finally {
      setPdfBusy(false)
    }
  }

  async function sendOffice() {
    if (writeBlocked || officeBusy) return
    setOfficeMsg('')
    setOfficeErr('')
    setOfficeBusy(true)
    try {
      const res = await api<{ message?: string }>(`/api/tasks/completion-bundle/send-office?${qs}`, {
        method: 'POST',
      })
      setOfficeMsg(res.message?.trim() || 'Aufgabenabschluss wurde ans Büro gesendet.')
    } catch (ex) {
      setOfficeErr(ex instanceof Error ? ex.message : 'Versand fehlgeschlagen.')
    } finally {
      setOfficeBusy(false)
    }
  }

  return (
    <div className="mt-3 space-y-2 border-t border-white/[0.06] pt-3">
      <div className="flex flex-wrap gap-1.5">
        {isCompanyOwner ? (
          <>
            <button
              type="button"
              disabled={writeBlocked || busy}
              onClick={() => onReopenAll()}
              className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-300 disabled:opacity-50"
            >
              Wieder öffnen
            </button>
            <button
              type="button"
              disabled={writeBlocked || busy}
              onClick={() => onDeleteAll()}
              className="rounded-xl border border-red-500/30 bg-red-500/10 px-2.5 py-1.5 text-xs font-medium text-red-300/90 disabled:opacity-50"
            >
              Löschen
            </button>
          </>
        ) : (
          <span className="text-xs text-emerald-400/90">Erledigt</span>
        )}
        <button
          type="button"
          onClick={() => onToggleMedia()}
          className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200"
        >
          {mediaOpen ? 'Fotos schließen' : `Fotos${photoCount ? ` (${photoCount})` : ''}`}
        </button>
        <button
          type="button"
          onClick={() => onToggleReport()}
          className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200"
        >
          {reportOpen ? 'Bericht schließen' : 'Bericht'}
        </button>
      </div>
      {mediaOpen ? (
        <div className="space-y-3">
          {g.tasks.map((t) => (
            <ReportPhotosSection
              key={t.id}
              reportId={null}
              taskId={t.id}
              enabled
              embedded
              iosGalleryRedirect
              initialOpen
              onUploadComplete={onMediaChanged}
            />
          ))}
        </div>
      ) : null}
      {reportOpen ? (
        <div className="space-y-2">
          <p className="text-sm leading-relaxed text-zinc-300">{summary || 'Noch keine Zusammenfassung.'}</p>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              disabled={pdfBusy}
              onClick={() => void downloadPdf()}
              className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200 disabled:opacity-50"
            >
              {pdfBusy ? '…' : 'PDF'}
            </button>
            {isCompanyOwner ? (
              <button
                type="button"
                disabled={writeBlocked || officeBusy}
                onClick={() => void sendOffice()}
                className="rounded-xl border border-orange-400/40 bg-orange-500/15 px-2.5 py-1.5 text-xs font-semibold text-orange-200 disabled:opacity-50"
              >
                {officeBusy ? '…' : 'Ans Büro senden'}
              </button>
            ) : null}
          </div>
          {officeMsg ? <p className="text-xs text-emerald-400/90">{officeMsg}</p> : null}
          {officeErr ? <p className="text-xs text-red-400">{officeErr}</p> : null}
        </div>
      ) : null}
    </div>
  )
}

export function TasksPage() {
  const { isCompanyOwner } = useAuth()
  const { writeBlocked } = useWriteBlocked()
  const [searchParams] = useSearchParams()
  const queryTaskId = searchParams.get('task') || ''
  const [tab, setTab] = useState<'open' | 'done'>('open')
  const [viewMode, setViewMode] = useState<'list' | 'week'>('list')
  const [weekStart, setWeekStart] = useState(() => startOfWeekMonday(todayIsoLocal()))
  const [selectedDay, setSelectedDay] = useState(() => todayIsoLocal())
  const [filterProjectId, setFilterProjectId] = useState('')
  const [filterEmployeeId, setFilterEmployeeId] = useState('')
  const [mediaOpenId, setMediaOpenId] = useState<string | null>(queryTaskId || null)
  const [reportOpenId, setReportOpenId] = useState<string | null>(null)
  const [expandedGroupKey, setExpandedGroupKey] = useState<string | null>(null)
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null)
  const [tasks, setTasks] = useState<SiteTask[]>([])
  const [doneUnseen, setDoneUnseen] = useState(0)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [composerOpen, setComposerOpen] = useState(false)

  const [projects, setProjects] = useState<Project[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [projectId, setProjectId] = useState('')
  const [dueDate, setDueDate] = useState(() => todayIsoLocal())
  const [selectedEmp, setSelectedEmp] = useState<Record<string, boolean>>({})
  const [draftLines, setDraftLines] = useState<DraftLine[]>(() => [newDraftLine()])
  const [progressDraft, setProgressDraft] = useState<Record<string, string>>({})

  const loadTasks = useCallback(async () => {
    setErr('')
    try {
      const q = new URLSearchParams()
      if (isCompanyOwner && viewMode === 'week') {
        q.set('fromDate', weekStart)
        q.set('toDate', addDaysIso(weekStart, 6))
        if (filterProjectId) q.set('projectId', filterProjectId)
        if (filterEmployeeId) q.set('employeeId', filterEmployeeId)
      } else {
        q.set('status', tab)
      }
      const r = await api<{ tasks: SiteTask[] }>(`/api/tasks?${q.toString()}`)
      setTasks(Array.isArray(r.tasks) ? r.tasks : [])
      if (isCompanyOwner) {
        const badge = await api<{ doneUnseenCount?: number }>('/api/tasks/badge')
        setDoneUnseen(Math.max(0, Number(badge.doneUnseenCount) || 0))
      } else {
        setDoneUnseen(0)
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Aufgaben konnten nicht geladen werden.')
    }
  }, [tab, isCompanyOwner, viewMode, weekStart, filterProjectId, filterEmployeeId])

  useEffect(() => {
    void loadTasks()
  }, [loadTasks])

  useEffect(() => {
    if (searchParams.get('photos') === '1' && queryTaskId) {
      setMediaOpenId(queryTaskId)
      setViewMode('list')
      setExpandedTaskId(queryTaskId)
    }
  }, [searchParams, queryTaskId])

  useEffect(() => {
    if (!queryTaskId) return
    const found = tasks.find((t) => t.id === queryTaskId)
    if (found) setExpandedGroupKey(taskGroupKey(found))
  }, [queryTaskId, tasks])

  useEffect(() => {
    const id = window.setInterval(() => {
      void loadTasks()
    }, 15000)
    return () => window.clearInterval(id)
  }, [loadTasks])

  useEffect(() => {
    if (!isCompanyOwner) return
    api<{ projects: Project[] }>('/api/projects')
      .then((r) => {
        const aktiv = (r.projects || []).filter((p) => ((p.status as string) || 'aktiv') === 'aktiv')
        setProjects(aktiv)
        if (aktiv[0]?.id) setProjectId(aktiv[0].id)
      })
      .catch(() => setProjects([]))
    api<{ employees: Employee[] }>('/api/employees')
      .then((r) => {
        const active = (r.employees || []).filter((e) => e.active)
        setEmployees(active)
        const sel: Record<string, boolean> = {}
        active.forEach((e) => {
          sel[e.id] = false
        })
        setSelectedEmp(sel)
      })
      .catch(() => setEmployees([]))
  }, [isCompanyOwner])

  const selectedIds = useMemo(
    () => employees.filter((e) => selectedEmp[e.id]).map((e) => e.id),
    [employees, selectedEmp],
  )

  const validDrafts = useMemo(
    () => draftLines.filter((line) => line.title.trim().length >= 3),
    [draftLines],
  )

  const visibleTasks = useMemo(() => {
    if (isCompanyOwner && viewMode === 'week') {
      return tasks.filter((t) => t.dueDate === selectedDay)
    }
    if (!isCompanyOwner && tab === 'open') {
      const today = todayIsoLocal()
      return [...tasks].sort((a, b) => {
        const ad = a.dueDate || ''
        const bd = b.dueDate || ''
        if (ad === bd) return (a.createdAt || '').localeCompare(b.createdAt || '')
        if (ad === today) return -1
        if (bd === today) return 1
        if (ad < today && bd >= today) return -1
        if (bd < today && ad >= today) return 1
        return ad.localeCompare(bd)
      })
    }
    return tasks
  }, [isCompanyOwner, viewMode, tasks, selectedDay, tab])

  const groupedTasks = useMemo(() => groupTasksBySiteDay(visibleTasks), [visibleTasks])

  const plannedNotices = useMemo(() => {
    if (isCompanyOwner || tab !== 'open') return []
    const today = todayIsoLocal()
    const map = new Map<string, { date: string; project: string; titles: string[] }>()
    for (const t of tasks) {
      if (t.status !== 'open') continue
      const due = String(t.dueDate || '')
      if (!due || due <= today) continue
      const key = `${due}|${t.projectId || t.projectName}`
      const cur = map.get(key) || {
        date: due,
        project: t.projectName || 'Baustelle',
        titles: [],
      }
      cur.titles.push(t.title)
      map.set(key, cur)
    }
    return [...map.values()].sort((a, b) => a.date.localeCompare(b.date))
  }, [isCompanyOwner, tab, tasks])

  useEffect(() => {
    if (!isCompanyOwner || tab !== 'done') return
    void api('/api/tasks/ack-done', { method: 'POST' })
      .then(() => {
        setDoneUnseen(0)
        window.dispatchEvent(new Event('freiraum-tasks-changed'))
      })
      .catch(() => {})
  }, [isCompanyOwner, tab])

  async function createTask() {
    if (writeBlocked || busy) return
    if (!validDrafts.length) {
      setErr('Mindestens eine Aufgabe mit Text angeben.')
      return
    }
    setErr('')
    setMsg('')
    setBusy(true)
    try {
      const proj = projects.find((p) => p.id === projectId)
      await api<{ tasks: SiteTask[] }>('/api/tasks/batch', {
        method: 'POST',
        body: JSON.stringify({
          projectId,
          projectName: proj?.name || '',
          dueDate,
          assigneeIds: selectedIds,
          items: validDrafts.map((line) => ({
            title: line.title.trim(),
            targetQuantity: parseQty(line.targetQty),
            unit: parseQty(line.targetQty) ? line.unit : '',
          })),
        }),
      })
      const planDate = dueDate
      const siteName = proj?.name || ''
      const who = employees.filter((e) => selectedEmp[e.id]).map((e) => e.name)
      const titles = validDrafts.map((line) => line.title.trim())
      setDraftLines([newDraftLine()])
      setComposerOpen(false)
      setViewMode('list')
      setTab('open')
      setExpandedTaskId(null)
      setExpandedGroupKey(`${projectId}|${planDate}`)
      setMsg(createdTaskMessage(titles, siteName, who, planDate))
      window.dispatchEvent(new Event('freiraum-tasks-changed'))
      await loadTasks()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Anlegen fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  async function addProgress(id: string) {
    if (writeBlocked || busy) return
    const amount = parseQty(progressDraft[id] || '')
    if (amount == null) {
      setErr('Bitte eine Menge größer als 0 eingeben.')
      return
    }
    setBusy(true)
    setErr('')
    setMsg('')
    try {
      await api(`/api/tasks/${encodeURIComponent(id)}/progress`, {
        method: 'POST',
        body: JSON.stringify({ amount }),
      })
      setProgressDraft((prev) => ({ ...prev, [id]: '' }))
      setMsg('Fortschritt gemeldet.')
      await loadTasks()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Fortschritt fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  async function completeTask(id: string) {
    if (writeBlocked || busy) return
    setBusy(true)
    setErr('')
    try {
      await api(`/api/tasks/${encodeURIComponent(id)}/complete`, { method: 'POST' })
      window.dispatchEvent(new Event('freiraum-tasks-changed'))
      await loadTasks()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Abschließen fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  async function reopenTask(id: string) {
    if (writeBlocked || busy || !isCompanyOwner) return
    setBusy(true)
    setErr('')
    try {
      await api(`/api/tasks/${encodeURIComponent(id)}/reopen`, { method: 'POST' })
      await loadTasks()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Wiederöffnen fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteTask(id: string) {
    if (writeBlocked || busy || !isCompanyOwner) return
    if (!window.confirm('Aufgabe wirklich löschen?')) return
    setBusy(true)
    setErr('')
    try {
      await api(`/api/tasks/${encodeURIComponent(id)}`, { method: 'DELETE' })
      await loadTasks()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Löschen fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  function renderTaskCard(t: SiteTask, showSite: boolean, embedded = false, compactOnly = false) {
    return (
      <TaskCard
        key={t.id}
        t={t}
        expanded={expandedTaskId === t.id}
        showSite={showSite}
        embedded={embedded}
        compactOnly={compactOnly}
        onToggle={() => {
          setExpandedTaskId((cur) => (cur === t.id ? null : t.id))
          if (mediaOpenId === t.id) setMediaOpenId(null)
          if (reportOpenId === t.id) setReportOpenId(null)
        }}
        isCompanyOwner={isCompanyOwner}
        writeBlocked={writeBlocked}
        busy={busy}
        progressDraft={progressDraft[t.id] || ''}
        onProgressDraft={(value) => setProgressDraft((prev) => ({ ...prev, [t.id]: value }))}
        onAddProgress={() => void addProgress(t.id)}
        onComplete={() => void completeTask(t.id)}
        onReopen={() => void reopenTask(t.id)}
        onDelete={() => void deleteTask(t.id)}
        mediaOpen={mediaOpenId === t.id}
        onToggleMedia={() => {
          setMediaOpenId((cur) => (cur === t.id ? null : t.id))
          setReportOpenId((cur) => (cur === t.id ? null : cur))
          setExpandedTaskId(t.id)
        }}
        onMediaChanged={() => void loadTasks()}
        reportOpen={reportOpenId === t.id}
        onToggleReport={() => {
          setReportOpenId((cur) => (cur === t.id ? null : t.id))
          setMediaOpenId((cur) => (cur === t.id ? null : cur))
          setExpandedTaskId(t.id)
        }}
      />
    )
  }

  return (
    <div className="overflow-x-hidden pb-2">
      <PageTitle
        title={isCompanyOwner ? 'To-do' : 'Aufgaben'}
        subtitle={isCompanyOwner ? 'Aufgaben zuweisen' : 'Deine Einsätze'}
      />

      {isCompanyOwner ? (
        <div className="mb-4">
          {!composerOpen ? (
            <BigButton
              type="button"
              disabled={writeBlocked}
              onClick={() => {
                if (viewMode === 'week') setDueDate(selectedDay)
                setComposerOpen(true)
              }}
            >
              + Aufgabe anlegen
            </BigButton>
          ) : (
            <Card className="space-y-4">
              <p className="text-sm font-medium text-zinc-200">Neue Aufgaben</p>
              <label className="block text-left">
                <span className="text-xs text-zinc-500">Baustelle</span>
                <select
                  className="mt-1 w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65"
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  disabled={!projects.length || writeBlocked}
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                      {p.customer ? ` (${p.customer})` : ''}
                    </option>
                  ))}
                </select>
              </label>
              <div className="text-left">
                <span className="text-xs text-zinc-500">Datum</span>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {dateChips().map((chip) => (
                    <button
                      key={chip.iso}
                      type="button"
                      disabled={writeBlocked}
                      onClick={() => setDueDate(chip.iso)}
                      className={`rounded-xl px-2.5 py-1.5 text-xs font-semibold ${
                        dueDate === chip.iso
                          ? 'border border-orange-400/45 bg-orange-500/15 text-orange-200'
                          : 'border border-white/[0.08] bg-black/40 text-zinc-400'
                      }`}
                    >
                      {chip.label}
                    </button>
                  ))}
                </div>
                <input
                  type="date"
                  className="mt-2 w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  disabled={writeBlocked}
                />
              </div>
              <div className="space-y-3">
                {draftLines.map((line, idx) => (
                  <div
                    key={line.key}
                    className="space-y-3 rounded-2xl border border-white/[0.08] bg-black/30 p-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-zinc-500">Aufgabe {idx + 1}</span>
                      {draftLines.length > 1 ? (
                        <button
                          type="button"
                          disabled={writeBlocked}
                          onClick={() =>
                            setDraftLines((prev) => prev.filter((item) => item.key !== line.key))
                          }
                          className="text-xs text-zinc-400 hover:text-red-300"
                        >
                          Entfernen
                        </button>
                      ) : null}
                    </div>
                    <label className="block text-left">
                      <span className="text-xs text-zinc-500">Text</span>
                      <textarea
                        className="mt-1 min-h-[4.5rem] w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none placeholder:text-zinc-600 focus:border-orange-500/65"
                        value={line.title}
                        onChange={(e) =>
                          setDraftLines((prev) =>
                            prev.map((item) =>
                              item.key === line.key ? { ...item, title: e.target.value } : item,
                            ),
                          )
                        }
                        disabled={writeBlocked}
                      />
                    </label>
                    <div className="grid grid-cols-[1fr_auto] gap-2">
                      <label className="block text-left">
                        <span className="text-xs text-zinc-500">Soll-Menge (optional)</span>
                        <input
                          type="text"
                          inputMode="decimal"
                          className="mt-1 w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none placeholder:text-zinc-600 focus:border-orange-500/65"
                          value={line.targetQty}
                          onChange={(e) =>
                            setDraftLines((prev) =>
                              prev.map((item) =>
                                item.key === line.key ? { ...item, targetQty: e.target.value } : item,
                              ),
                            )
                          }
                          disabled={writeBlocked}
                        />
                      </label>
                      <label className="block text-left">
                        <span className="text-xs text-zinc-500">Einheit</span>
                        <select
                          className="mt-1 w-[5.5rem] rounded-2xl border border-white/[0.1] bg-black/55 px-2 py-2.5 text-white outline-none focus:border-orange-500/65"
                          value={line.unit}
                          onChange={(e) =>
                            setDraftLines((prev) =>
                              prev.map((item) =>
                                item.key === line.key
                                  ? { ...item, unit: e.target.value as (typeof TASK_UNITS)[number] }
                                  : item,
                              ),
                            )
                          }
                          disabled={writeBlocked}
                        >
                          {TASK_UNITS.map((u) => (
                            <option key={u} value={u}>
                              {u}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                  </div>
                ))}
                {draftLines.length < 20 ? (
                  <button
                    type="button"
                    disabled={writeBlocked}
                    onClick={() => setDraftLines((prev) => [...prev, newDraftLine()])}
                    className="flex w-full items-center justify-center rounded-2xl border border-orange-400/35 bg-orange-500/10 px-3 py-2.5 text-sm font-semibold text-orange-200 disabled:opacity-50"
                  >
                    + Weitere Aufgabe
                  </button>
                ) : null}
              </div>
              <div className="text-left">
                <span className="text-xs text-zinc-500">Mitarbeiter zuweisen</span>
                <div className="mt-2 space-y-2">
                  {employees.length === 0 ? (
                    <p className="text-sm text-zinc-500">Keine aktiven Mitarbeiter.</p>
                  ) : (
                    employees.map((e) => (
                      <label
                        key={e.id}
                        className="flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-black/40 px-3 py-2.5"
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4 accent-orange-500"
                          checked={Boolean(selectedEmp[e.id])}
                          disabled={writeBlocked}
                          onChange={() =>
                            setSelectedEmp((prev) => ({ ...prev, [e.id]: !prev[e.id] }))
                          }
                        />
                        <span className="text-sm text-zinc-200">{e.name}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <BigButton
                  type="button"
                  disabled={
                    writeBlocked ||
                    busy ||
                    !projectId ||
                    validDrafts.length === 0 ||
                    selectedIds.length === 0
                  }
                  onClick={() => void createTask()}
                >
                  Speichern
                </BigButton>
                <BigButton
                  type="button"
                  variant="secondary"
                  disabled={busy}
                  onClick={() => setComposerOpen(false)}
                >
                  Abbrechen
                </BigButton>
              </div>
            </Card>
          )}
        </div>
      ) : null}

      {isCompanyOwner ? (
        <div className="mb-3 flex justify-center">
          <div className="inline-flex rounded-full border border-white/[0.08] bg-black/40 p-0.5">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`rounded-full px-3.5 py-1 text-xs font-medium ${
                viewMode === 'list' ? 'bg-white/[0.08] text-zinc-100' : 'text-zinc-500'
              }`}
            >
              Liste
            </button>
            <button
              type="button"
              onClick={() => {
                setViewMode('week')
                setDueDate(selectedDay)
              }}
              className={`rounded-full px-3.5 py-1 text-xs font-medium ${
                viewMode === 'week' ? 'bg-white/[0.08] text-zinc-100' : 'text-zinc-500'
              }`}
            >
              Kalender
            </button>
          </div>
        </div>
      ) : null}

      {isCompanyOwner && viewMode === 'week' ? (
        <div className="mb-4 grid grid-cols-2 gap-2">
          <label className="block text-left">
            <span className="text-xs text-zinc-500">Baustelle</span>
            <select
              className="mt-1 w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-sm text-white outline-none focus:border-orange-500/65"
              value={filterProjectId}
              onChange={(e) => setFilterProjectId(e.target.value)}
            >
              <option value="">Alle</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-left">
            <span className="text-xs text-zinc-500">Mitarbeiter</span>
            <select
              className="mt-1 w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-sm text-white outline-none focus:border-orange-500/65"
              value={filterEmployeeId}
              onChange={(e) => setFilterEmployeeId(e.target.value)}
            >
              <option value="">Alle</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {isCompanyOwner && viewMode === 'week' ? (
        <TasksWeekView
          weekStart={weekStart}
          selectedDay={selectedDay}
          days={weekDates(weekStart).map((date) => ({
            date,
            tasks: tasks.filter((t) => t.dueDate === date),
          }))}
          onWeekChange={(next) => {
            setWeekStart(next)
            const inWeek = selectedDay >= next && selectedDay <= addDaysIso(next, 6)
            if (!inWeek) setSelectedDay(next)
          }}
          onSelectDay={(iso) => {
            setSelectedDay(iso)
            setDueDate(iso)
          }}
        />
      ) : (
        <div className="mb-4 flex justify-center">
          <div className="inline-flex rounded-full border border-white/[0.08] bg-black/30 p-0.5">
            <button
              type="button"
              onClick={() => setTab('open')}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                tab === 'open' ? 'bg-orange-500/15 text-orange-200' : 'text-zinc-500'
              }`}
            >
              Offen
            </button>
            <button
              type="button"
              onClick={() => setTab('done')}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                tab === 'done' ? 'bg-orange-500/15 text-orange-200' : 'text-zinc-500'
              }`}
            >
              Erledigt
              {isCompanyOwner && tab !== 'done' && doneUnseen > 0 ? (
                <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-orange-500 px-1 text-[0.62rem] font-bold leading-none text-zinc-950">
                  {doneUnseen > 9 ? '9+' : doneUnseen}
                </span>
              ) : null}
            </button>
          </div>
        </div>
      )}

      {err ? <p className="mb-3 text-sm text-red-400">{err}</p> : null}
      {msg ? <p className="mb-3 text-sm text-emerald-400/90">{msg}</p> : null}

      {!isCompanyOwner && tab === 'open' && plannedNotices.length ? (
        <div className="mb-4 space-y-2">
          {plannedNotices.map((g) => (
            <Card key={`${g.date}-${g.project}`} className="border-orange-400/25 !py-4">
              <p className="text-sm font-medium text-orange-100">
                Du bist am {formatDateDe(g.date)} auf {g.project} eingeplant
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-zinc-300">
                {g.titles.map((title, i) => (
                  <li key={`${g.date}-${title}-${i}`}>{title}</li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="space-y-3">
        {visibleTasks.length === 0 && plannedNotices.length === 0 ? (
          <Card>
            <p className="text-center text-sm text-zinc-500">
              {isCompanyOwner && viewMode === 'week'
                ? 'Keine Aufgaben an diesem Tag.'
                : tab === 'open'
                  ? 'Keine offenen Aufgaben.'
                  : 'Noch keine erledigten Aufgaben.'}
            </p>
          </Card>
        ) : isCompanyOwner && viewMode === 'week' ? (
          visibleTasks.map((t) => renderTaskCard(t, true))
        ) : (
          groupedTasks.map((g) => {
            const loc = formatProjectLocation(g.projectAddress, g.projectCity)
            if (g.tasks.length === 1) {
              return renderTaskCard(g.tasks[0] as SiteTask, true)
            }
            const open = expandedGroupKey === g.key
            const allDone = g.tasks.every((t) => t.status === 'done')
            return (
              <Card key={g.key} className="!px-4 !py-3.5">
                <button
                  type="button"
                  onClick={() => {
                    setExpandedGroupKey((cur) => (cur === g.key ? null : g.key))
                    setExpandedTaskId(null)
                    setMediaOpenId(null)
                    setReportOpenId(null)
                  }}
                  className="flex w-full items-start justify-between gap-3 text-left"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">{g.projectName}</p>
                    <p className="mt-1 text-xs text-zinc-500">Datum: {formatDateDe(g.dueDate)}</p>
                  </div>
                  <span className="flex h-6 min-w-6 shrink-0 items-center justify-center rounded-full bg-orange-500/20 px-2 text-xs font-semibold text-orange-200">
                    {g.tasks.length}
                  </span>
                </button>
                {loc ? <TaskAddressLink loc={loc} /> : null}
                {open ? (
                  <>
                    <div className="mt-3 divide-y divide-white/[0.06] border-t border-white/[0.06] pt-1">
                      {g.tasks.map((t) => (
                        <div key={t.id} className="py-2">
                          {renderTaskCard(t, false, true, allDone)}
                        </div>
                      ))}
                    </div>
                    {allDone ? (
                      <GroupDoneFooter
                        g={g}
                        isCompanyOwner={isCompanyOwner}
                        writeBlocked={writeBlocked}
                        busy={busy}
                        mediaOpen={mediaOpenId === g.key}
                        reportOpen={reportOpenId === g.key}
                        onToggleMedia={() => {
                          setMediaOpenId((cur) => (cur === g.key ? null : g.key))
                          setReportOpenId((cur) => (cur === g.key ? null : cur))
                        }}
                        onToggleReport={() => {
                          setReportOpenId((cur) => (cur === g.key ? null : g.key))
                          setMediaOpenId((cur) => (cur === g.key ? null : cur))
                        }}
                        onReopenAll={() => {
                          if (!window.confirm('Alle Aufgaben dieser Baustelle wieder öffnen?')) return
                          void (async () => {
                            setBusy(true)
                            setErr('')
                            try {
                              for (const t of g.tasks) {
                                await api(`/api/tasks/${encodeURIComponent(t.id)}/reopen`, { method: 'POST' })
                              }
                              await loadTasks()
                            } catch (e) {
                              setErr(e instanceof Error ? e.message : 'Wiederöffnen fehlgeschlagen.')
                            } finally {
                              setBusy(false)
                            }
                          })()
                        }}
                        onDeleteAll={() => {
                          if (!window.confirm(`Alle ${g.tasks.length} Aufgaben dieser Baustelle löschen?`)) return
                          void (async () => {
                            setBusy(true)
                            setErr('')
                            try {
                              for (const t of g.tasks) {
                                await api(`/api/tasks/${encodeURIComponent(t.id)}`, { method: 'DELETE' })
                              }
                              await loadTasks()
                            } catch (e) {
                              setErr(e instanceof Error ? e.message : 'Löschen fehlgeschlagen.')
                            } finally {
                              setBusy(false)
                            }
                          })()
                        }}
                        onMediaChanged={() => void loadTasks()}
                      />
                    ) : null}
                  </>
                ) : null}
              </Card>
            )
          })
        )}
      </div>
      <TaskPushOptIn isOwner={isCompanyOwner} />
    </div>
  )
}
