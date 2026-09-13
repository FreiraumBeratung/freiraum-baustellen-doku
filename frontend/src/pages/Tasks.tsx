import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
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
}

export type SiteTask = {
  id: string
  projectId: string
  projectName: string
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

function formatQty(value: number | null | undefined): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0'
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(n)
}

function parseQty(raw: string): number | null {
  const cleaned = String(raw || '').trim().replace(',', '.')
  if (!cleaned) return null
  const n = Number(cleaned)
  if (!Number.isFinite(n) || n <= 0) return null
  return n
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
  const [tasks, setTasks] = useState<SiteTask[]>([])
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
    }
  }, [searchParams, queryTaskId])

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
      .then(() => window.dispatchEvent(new Event('freiraum-tasks-changed')))
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
      const created = await api<{ tasks: SiteTask[] }>('/api/tasks/batch', {
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
      const n = Array.isArray(created.tasks) ? created.tasks.length : validDrafts.length
      const planDate = dueDate
      setDraftLines([newDraftLine()])
      setComposerOpen(false)
      setViewMode('week')
      setWeekStart(startOfWeekMonday(planDate))
      setSelectedDay(planDate)
      setDueDate(planDate)
      setMsg(
        n === 1
          ? `Aufgabe für ${formatDateDe(planDate)} angelegt — steht im Kalender.`
          : `${n} Aufgaben für ${formatDateDe(planDate)} angelegt — stehen im Kalender.`,
      )
      window.dispatchEvent(new Event('freiraum-tasks-changed'))
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
              Woche
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
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                tab === 'done' ? 'bg-orange-500/15 text-orange-200' : 'text-zinc-500'
              }`}
            >
              Erledigt
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
        ) : (
          visibleTasks.map((t) => (
            <Card key={t.id} className="space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[0.7rem] font-medium uppercase tracking-wide text-orange-400/90">
                    {t.projectName || 'Baustelle'}
                  </p>
                  <p className="mt-1 text-sm font-medium text-white">{t.title}</p>
                  <p className="mt-2 text-xs text-zinc-500">
                    Datum: {formatDateDe(t.dueDate)}
                    {t.assigneeNames?.length
                      ? ` · ${t.assigneeNames.join(', ')}`
                      : ''}
                  </p>
                </div>
              </div>
              {t.targetQuantity != null ? (
                <div className="space-y-2 rounded-2xl border border-white/[0.06] bg-black/30 px-3 py-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <p className="text-sm font-medium text-zinc-100">
                      {formatQty(t.actualQuantity)} / {formatQty(t.targetQuantity)} {t.unit || 'm²'}
                    </p>
                    <p className="text-xs text-zinc-400">
                      Rest {formatQty(t.remainingQuantity)} {t.unit || 'm²'}
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
                          {p.actorName}: {formatQty(p.amount)} {t.unit || 'm²'}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-zinc-500">Noch kein Fortschritt gemeldet.</p>
                  )}
                  {t.status === 'open' ? (
                    <div className="flex items-center gap-2 pt-1">
                      <input
                        type="text"
                        inputMode="decimal"
                        className="min-w-0 flex-1 rounded-xl border border-white/[0.1] bg-black/55 px-3 py-2 text-sm text-white outline-none focus:border-orange-500/65"
                        value={progressDraft[t.id] || ''}
                        onChange={(e) =>
                          setProgressDraft((prev) => ({ ...prev, [t.id]: e.target.value }))
                        }
                        disabled={writeBlocked || busy}
                      />
                      <button
                        type="button"
                        disabled={writeBlocked || busy || !parseQty(progressDraft[t.id] || '')}
                        onClick={() => void addProgress(t.id)}
                        className="rounded-xl border border-orange-400/40 bg-orange-500/15 px-3 py-2 text-sm font-semibold text-orange-200 disabled:opacity-50"
                      >
                        Melden
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                {t.status === 'open' ? (
                  <button
                    type="button"
                    disabled={writeBlocked || busy}
                    onClick={() => void completeTask(t.id)}
                    className="rounded-xl border border-orange-400/40 bg-orange-500/15 px-3 py-2 text-sm font-semibold text-orange-200 disabled:opacity-50"
                  >
                    Erledigt ✓
                  </button>
                ) : isCompanyOwner ? (
                  <button
                    type="button"
                    disabled={writeBlocked || busy}
                    onClick={() => void reopenTask(t.id)}
                    className="rounded-xl border border-white/[0.12] bg-black/40 px-3 py-2 text-sm font-medium text-zinc-300 disabled:opacity-50"
                  >
                    Wieder öffnen
                  </button>
                ) : (
                  <span className="text-sm text-emerald-400/90">Erledigt</span>
                )}
                {isCompanyOwner ? (
                  <button
                    type="button"
                    disabled={writeBlocked || busy}
                    onClick={() => void deleteTask(t.id)}
                    className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm font-medium text-red-300/90 disabled:opacity-50"
                  >
                    Löschen
                  </button>
                ) : null}
                {t.status === 'done' ? (
                  <button
                    type="button"
                    onClick={() => setMediaOpenId((cur) => (cur === t.id ? null : t.id))}
                    className="rounded-xl border border-white/[0.12] bg-black/40 px-3 py-2 text-sm font-medium text-zinc-200 disabled:opacity-50"
                  >
                    {mediaOpenId === t.id
                      ? 'Fotos schließen'
                      : `Fotos ansehen${t.photoCount ? ` (${t.photoCount})` : ''}`}
                  </button>
                ) : null}
              </div>
              {t.status === 'open' || mediaOpenId === t.id ? (
                <div className="space-y-3 border-t border-white/[0.06] pt-3">
                  <ReportPhotosSection
                    reportId={null}
                    taskId={t.id}
                    enabled
                    embedded
                    iosGalleryRedirect
                    initialOpen={mediaOpenId === t.id}
                    onUploadComplete={() => void loadTasks()}
                  />
                  <TaskSignatureSection taskId={t.id} onChanged={() => void loadTasks()} />
                </div>
              ) : null}
            </Card>
          ))
        )}
      </div>
      <TaskPushOptIn isOwner={isCompanyOwner} />
    </div>
  )
}
