import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type Project = { id: string; name: string; customer?: string; status?: string }
type Employee = { id: string; name: string; active: boolean }

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
}

function formatDateDe(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || '').trim())
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

export function TasksPage() {
  const { isCompanyOwner } = useAuth()
  const { writeBlocked } = useWriteBlocked()
  const [tab, setTab] = useState<'open' | 'done'>('open')
  const [tasks, setTasks] = useState<SiteTask[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [composerOpen, setComposerOpen] = useState(false)

  const [projects, setProjects] = useState<Project[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [projectId, setProjectId] = useState('')
  const [dueDate, setDueDate] = useState(todayIso())
  const [title, setTitle] = useState('')
  const [selectedEmp, setSelectedEmp] = useState<Record<string, boolean>>({})

  const loadTasks = useCallback(async () => {
    setErr('')
    try {
      const r = await api<{ tasks: SiteTask[] }>(`/api/tasks?status=${tab}`)
      setTasks(Array.isArray(r.tasks) ? r.tasks : [])
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Aufgaben konnten nicht geladen werden.')
    }
  }, [tab])

  useEffect(() => {
    void loadTasks()
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

  async function createTask() {
    if (writeBlocked || busy) return
    setErr('')
    setMsg('')
    setBusy(true)
    try {
      const proj = projects.find((p) => p.id === projectId)
      await api('/api/tasks', {
        method: 'POST',
        body: JSON.stringify({
          projectId,
          projectName: proj?.name || '',
          title: title.trim(),
          dueDate,
          assigneeIds: selectedIds,
        }),
      })
      setTitle('')
      setComposerOpen(false)
      setMsg('Aufgabe angelegt.')
      setTab('open')
      await loadTasks()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Anlegen fehlgeschlagen.')
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
        subtitle={isCompanyOwner ? 'Aufgaben anlegen und zuweisen' : 'Deine zugewiesenen Aufgaben'}
      />

      {isCompanyOwner ? (
        <div className="mb-4">
          {!composerOpen ? (
            <BigButton type="button" disabled={writeBlocked} onClick={() => setComposerOpen(true)}>
              + Aufgabe anlegen
            </BigButton>
          ) : (
            <Card className="space-y-4">
              <p className="text-sm font-medium text-zinc-200">Neue Aufgabe</p>
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
              <label className="block text-left">
                <span className="text-xs text-zinc-500">Datum</span>
                <input
                  type="date"
                  className="mt-1 w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  disabled={writeBlocked}
                />
              </label>
              <label className="block text-left">
                <span className="text-xs text-zinc-500">Aufgabe</span>
                <textarea
                  className="mt-1 min-h-[5.5rem] w-full rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="z. B. 50 m² Rasen mähen"
                  disabled={writeBlocked}
                />
              </label>
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
                    title.trim().length < 3 ||
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

      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={() => setTab('open')}
          className={`flex-1 rounded-2xl px-3 py-2.5 text-sm font-semibold transition ${
            tab === 'open'
              ? 'border border-orange-400/45 bg-orange-500/[0.12] text-orange-200'
              : 'border border-white/[0.08] bg-black/40 text-zinc-400'
          }`}
        >
          Offen
        </button>
        <button
          type="button"
          onClick={() => setTab('done')}
          className={`flex-1 rounded-2xl px-3 py-2.5 text-sm font-semibold transition ${
            tab === 'done'
              ? 'border border-orange-400/45 bg-orange-500/[0.12] text-orange-200'
              : 'border border-white/[0.08] bg-black/40 text-zinc-400'
          }`}
        >
          Erledigt
        </button>
      </div>

      {err ? <p className="mb-3 text-sm text-red-400">{err}</p> : null}
      {msg ? <p className="mb-3 text-sm text-emerald-400/90">{msg}</p> : null}

      <div className="space-y-3">
        {tasks.length === 0 ? (
          <Card>
            <p className="text-center text-sm text-zinc-500">
              {tab === 'open' ? 'Keine offenen Aufgaben.' : 'Noch keine erledigten Aufgaben.'}
            </p>
          </Card>
        ) : (
          tasks.map((t) => (
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
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
