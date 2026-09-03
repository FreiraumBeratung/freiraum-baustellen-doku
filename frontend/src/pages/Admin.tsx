import { useCallback, useEffect, useState } from 'react'
import { Trash2 } from 'lucide-react'
import {
  deleteAdminUser,
  listAdminUsers,
  setAdminUserLicense,
  type AdminUserRow,
} from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Card, PageTitle } from '../components/ui'

function fmtDate(iso: string): string {
  const s = iso.trim()
  if (!s) return '—'
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s.slice(0, 10)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function fmtActivityTooltip(iso: string | undefined, usedToday: boolean | undefined): string {
  const s = (iso || '').trim()
  if (!s) return 'Noch keine Nutzung erkannt'
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return 'Noch keine Nutzung erkannt'
  const time = d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
  const date = d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  if (usedToday) return `Zuletzt heute ${time} Uhr`
  return `Zuletzt ${date}, ${time} Uhr`
}

export function AdminPage() {
  const { token } = useAuth()
  const [users, setUsers] = useState<AdminUserRow[]>([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setErr('')
    setLoading(true)
    try {
      const r = await listAdminUsers()
      setUsers(r.users ?? [])
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Accounts konnten nicht geladen werden.')
      setUsers([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function toggleLicense(row: AdminUserRow) {
    if (row.isAdmin) return
    setBusyId(row.id)
    setMsg('')
    setErr('')
    const next = !row.licenseActive
    try {
      const r = await setAdminUserLicense(row.id, next)
      setUsers((prev) => prev.map((u) => (u.id === row.id ? r.user : u)))
      setMsg(next ? 'Lizenz aktiviert.' : 'Lizenz pausiert (Read-only).')
      window.setTimeout(() => setMsg(''), 4000)
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Lizenz konnte nicht geändert werden.')
    } finally {
      setBusyId(null)
    }
  }

  async function removeUser(row: AdminUserRow) {
    if (row.isAdmin || row.id === token) return
    const label = row.companyName?.trim() || row.email
    const ok = window.confirm(
      `Account „${label}“ wirklich löschen?\n\nAlle Berichte, Fotos und Mandantendaten werden unwiderruflich entfernt.`,
    )
    if (!ok) return

    setBusyId(row.id)
    setMsg('')
    setErr('')
    try {
      await deleteAdminUser(row.id)
      setUsers((prev) => prev.filter((u) => u.id !== row.id))
      setMsg('Account gelöscht.')
      window.setTimeout(() => setMsg(''), 4000)
    } catch (ex) {
      const m = ex instanceof Error ? ex.message : ''
      setErr(m || 'Account konnte nicht gelöscht werden.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="overflow-x-hidden pb-2">
      <PageTitle
        title="Verwaltung"
        subtitle="Registrierte Accounts — Lizenz steuern, Testaccounts entfernen"
      />

      {loading ? <p className="text-sm text-zinc-400">Laden…</p> : null}
      {msg ? <p className="mb-3 text-sm text-orange-300">{msg}</p> : null}
      {err ? <p className="mb-3 text-sm text-red-400">{err}</p> : null}

      <div className="space-y-4">
        {users.map((row) => {
          const isSelf = row.id === token
          const busy = busyId === row.id
          const usedToday = row.usedToday === true
          const activityTitle = fmtActivityTooltip(row.lastActivityAt, row.usedToday)
          return (
            <Card
              key={row.id}
              className="border-white/[0.07] bg-black/35 px-5 py-4 shadow-none ring-1 ring-white/[0.05]"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="truncate text-base font-semibold text-white">{row.companyName || '—'}</h2>
                    {usedToday ? (
                      <span
                        className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300 ring-1 ring-emerald-400/40"
                        title={activityTitle}
                      >
                        Heute aktiv
                      </span>
                    ) : (
                      <span
                        className="rounded-full bg-zinc-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-zinc-300 ring-1 ring-zinc-400/35"
                        title={activityTitle}
                      >
                        Heute still
                      </span>
                    )}
                    {row.isAdmin ? (
                      <span className="rounded-full bg-orange-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-orange-300 ring-1 ring-orange-500/30">
                        Admin
                      </span>
                    ) : null}
                    {!row.licenseActive ? (
                      <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200 ring-1 ring-amber-500/30">
                        Pausiert
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 truncate text-sm text-zinc-400">{row.email}</p>
                  {row.entrepreneurName ? (
                    <p className="mt-0.5 text-xs text-zinc-500">{row.entrepreneurName}</p>
                  ) : null}
                  <p className="mt-2 text-xs text-zinc-500">Registriert: {fmtDate(row.createdAt)}</p>
                  <p className="mt-1 text-sm font-medium text-zinc-200" title={activityTitle}>
                    {row.lastActivityAt ? activityTitle : 'Noch keine Nutzung erkannt'}
                  </p>
                  {!row.isAdmin ? (
                    <p className="mt-1 text-sm text-zinc-300">
                      Registrierte Mitarbeiter: {typeof row.workerCount === 'number' ? row.workerCount : 0}
                    </p>
                  ) : null}
                </div>
              </div>

              <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                {!row.isAdmin ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void toggleLicense(row)}
                    className={`inline-flex h-11 flex-1 items-center justify-center rounded-xl border px-3 text-sm font-semibold transition disabled:opacity-40 ${
                      row.licenseActive
                        ? 'border-amber-500/35 bg-amber-950/30 text-amber-200 hover:bg-amber-950/45'
                        : 'border-emerald-500/35 bg-emerald-950/25 text-emerald-200 hover:bg-emerald-950/40'
                    }`}
                  >
                    {busy ? '…' : row.licenseActive ? 'Lizenz pausieren' : 'Lizenz aktivieren'}
                  </button>
                ) : (
                  <p className="flex flex-1 items-center text-xs text-zinc-500">
                    {isSelf ? 'Ihr Administrator-Account' : 'Administrator'}
                  </p>
                )}

                {!row.isAdmin && !isSelf ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void removeUser(row)}
                    className="inline-flex h-11 flex-1 items-center justify-center gap-2 rounded-xl border border-red-500/30 bg-red-950/30 text-sm font-semibold text-red-300 hover:bg-red-950/45 disabled:opacity-40"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden />
                    {busy ? '…' : 'Löschen'}
                  </button>
                ) : null}
              </div>
            </Card>
          )
        })}

        {!loading && users.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">Keine Accounts gefunden.</p>
        ) : null}
      </div>
    </div>
  )
}
