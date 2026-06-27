import { Pencil, Power, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type Employee = {
  id: string
  name: string
  role: string
  active: boolean
}

export function EmployeesPage() {
  const { writeBlocked } = useWriteBlocked()
  const [rows, setRows] = useState<Employee[]>([])
  const [name, setName] = useState('')
  const [role, setRole] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editRole, setEditRole] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  async function load() {
    const r = await api<{ employees: Employee[] }>('/api/employees')
    setRows(r.employees)
  }

  useEffect(() => {
    load().catch(() => {})
  }, [])

  async function add(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || writeBlocked) return
    await api<Employee>('/api/employees', {
      method: 'POST',
      body: JSON.stringify({ name: name.trim(), role: role.trim(), active: true }),
    })
    setName('')
    setRole('')
    load()
  }

  async function toggleActive(emp: Employee) {
    if (writeBlocked) return
    setBusyId(emp.id)
    try {
      await api(`/api/employees/${emp.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ active: !emp.active }),
      })
      await load()
    } finally {
      setBusyId(null)
    }
  }

  function startEdit(emp: Employee) {
    setConfirmDeleteId(null)
    setEditId(emp.id)
    setEditName(emp.name)
    setEditRole(emp.role || '')
  }

  function cancelEdit() {
    setEditId(null)
    setEditName('')
    setEditRole('')
  }

  async function saveEdit(emp: Employee) {
    if (writeBlocked || !editName.trim()) return
    setBusyId(emp.id)
    try {
      await api(`/api/employees/${emp.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ name: editName.trim(), role: editRole.trim() }),
      })
      cancelEdit()
      await load()
    } finally {
      setBusyId(null)
    }
  }

  async function deleteEmployee(emp: Employee) {
    if (writeBlocked) return
    setBusyId(emp.id)
    try {
      await api(`/api/employees/${emp.id}`, { method: 'DELETE' })
      setConfirmDeleteId(null)
      await load()
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Mitarbeiter verwalten" subtitle="Anlegen, bearbeiten, deaktivieren oder löschen — für die Auswahl im Tagesbericht" />

      <Card className="mb-4">
        <form onSubmit={add} className="space-y-3">
          <label className="block min-w-0">
            <span className="text-sm text-zinc-400">Name</span>
            <input
              className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="z. B. Marcel"
            />
          </label>
          <label className="block min-w-0">
            <span className="text-sm text-zinc-400">Rolle (optional)</span>
            <input
              className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Vorarbeiter"
            />
          </label>
          <BigButton type="submit" disabled={writeBlocked}>Mitarbeiter hinzufügen</BigButton>
        </form>
      </Card>

      <div className="space-y-2">
        {rows.map((emp) => (
          <Card key={emp.id} className="py-3">
            {editId === emp.id ? (
              <div className="space-y-2.5">
                <label className="block min-w-0">
                  <span className="text-xs text-zinc-400">Name</span>
                  <input
                    className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                </label>
                <label className="block min-w-0">
                  <span className="text-xs text-zinc-400">Rolle</span>
                  <input
                    className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-white"
                    value={editRole}
                    onChange={(e) => setEditRole(e.target.value)}
                    placeholder="z. B. Vorarbeiter"
                  />
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={writeBlocked || busyId === emp.id || !editName.trim()}
                    onClick={() => saveEdit(emp)}
                    className="flex-1 rounded-xl bg-orange-500/90 px-3 py-2.5 text-sm font-semibold text-zinc-950 transition hover:bg-orange-400 disabled:opacity-40"
                  >
                    {busyId === emp.id ? '…' : 'Speichern'}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="rounded-xl border border-zinc-600 px-3 py-2.5 text-sm text-zinc-300 transition hover:bg-zinc-800"
                  >
                    Abbrechen
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-2.5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-semibold text-white">{emp.name}</div>
                    {emp.role ? <div className="text-sm text-zinc-500">{emp.role}</div> : null}
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-[0.18rem] text-[0.68rem] font-semibold uppercase tracking-[0.08em] ${
                      emp.active
                        ? 'bg-emerald-500/[0.12] text-emerald-300/95 ring-1 ring-emerald-400/25'
                        : 'bg-zinc-800 text-zinc-500 ring-1 ring-white/[0.06]'
                    }`}
                  >
                    {emp.active ? 'aktiv' : 'inaktiv'}
                  </span>
                </div>

                {confirmDeleteId === emp.id ? (
                  <div className="flex items-center gap-2 rounded-xl border border-red-500/35 bg-red-500/[0.08] px-3 py-2">
                    <span className="min-w-0 flex-1 text-[0.78rem] text-red-200/95">Wirklich löschen?</span>
                    <button
                      type="button"
                      disabled={busyId === emp.id}
                      onClick={() => deleteEmployee(emp)}
                      className="rounded-[0.7rem] bg-red-500/90 px-3 py-1.5 text-[0.74rem] font-semibold text-zinc-950 transition hover:bg-red-400 disabled:opacity-40"
                    >
                      {busyId === emp.id ? '…' : 'Löschen'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfirmDeleteId(null)}
                      className="rounded-[0.7rem] bg-black/45 px-3 py-1.5 text-[0.74rem] font-medium text-zinc-300 ring-1 ring-white/[0.1] transition hover:bg-black/60"
                    >
                      Abbrechen
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={writeBlocked}
                      onClick={() => startEdit(emp)}
                      className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-[0.85rem] bg-black/50 py-[0.5rem] text-[0.74rem] font-medium text-zinc-300 ring-1 ring-white/[0.08] transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
                    >
                      <Pencil strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
                      Bearbeiten
                    </button>
                    <button
                      type="button"
                      disabled={writeBlocked || busyId === emp.id}
                      onClick={() => toggleActive(emp)}
                      className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-[0.85rem] bg-black/50 py-[0.5rem] text-[0.74rem] font-medium text-zinc-300 ring-1 ring-white/[0.08] transition hover:bg-black/60 active:scale-[0.99] disabled:opacity-40"
                    >
                      <Power strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
                      {emp.active ? 'Deaktivieren' : 'Aktivieren'}
                    </button>
                    <button
                      type="button"
                      disabled={writeBlocked}
                      onClick={() => setConfirmDeleteId(emp.id)}
                      aria-label="Mitarbeiter löschen"
                      className="inline-flex items-center justify-center rounded-[0.85rem] bg-black/50 px-3 py-[0.5rem] text-zinc-400 ring-1 ring-white/[0.08] transition hover:bg-red-500/[0.12] hover:text-red-300 hover:ring-red-500/30 active:scale-[0.99] disabled:opacity-40"
                    >
                      <Trash2 strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
                    </button>
                  </div>
                )}
              </div>
            )}
          </Card>
        ))}
        {rows.length === 0 ? <p className="text-center text-zinc-500">Noch keine Mitarbeiter.</p> : null}
      </div>
    </div>
  )
}
