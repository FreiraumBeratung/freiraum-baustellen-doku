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
    await api(`/api/employees/${emp.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ active: !emp.active }),
    })
    load()
  }

  return (
    <div className="overflow-x-hidden">
      <PageTitle title="Mitarbeiter verwalten" subtitle="Liste, anlegen und aktiv setzen — für Auswahl im Tagesbericht" />

      <Card className="mb-4">
        <form onSubmit={add} className="space-y-3">
          <label className="block min-w-0">
            <span className="text-sm text-zinc-400">Name</span>
            <input
              className="mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="z. B. Marcel"
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
          <Card key={emp.id} className="flex min-w-0 items-center justify-between gap-3 py-3">
            <div className="min-w-0">
              <div className="font-semibold text-white">{emp.name}</div>
              {emp.role ? <div className="text-sm text-zinc-500">{emp.role}</div> : null}
              <div className="text-xs text-zinc-500">{emp.active ? 'aktiv' : 'inaktiv'}</div>
            </div>
            <button
              type="button"
              disabled={writeBlocked}
              className="rounded-xl border border-zinc-600 px-3 py-2 text-sm text-white hover:bg-zinc-800 disabled:opacity-40"
              onClick={() => toggleActive(emp)}
            >
              {emp.active ? 'Deaktivieren' : 'Aktivieren'}
            </button>
          </Card>
        ))}
        {rows.length === 0 ? <p className="text-center text-zinc-500">Noch keine Mitarbeiter.</p> : null}
      </div>
    </div>
  )
}
