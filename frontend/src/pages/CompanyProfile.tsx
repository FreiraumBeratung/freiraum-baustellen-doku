import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { api, resolveBackendPublicUrl } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type CompanyProfile = {
  companyName: string
  contactPerson: string
  officeEmail: string
  phone: string
  address: string
  defaultExportFormat: string
  defaultRecipientEmail: string
  logoUrl: string | null
}

export function CompanyProfilePage() {
  const nav = useNavigate()
  const { logout, isAdmin } = useAuth()
  const { writeBlocked } = useWriteBlocked()
  const [prof, setProf] = useState<CompanyProfile | null>(null)
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<CompanyProfile>('/api/company-profile')
      .then(setProf)
      .finally(() => setLoading(false))
  }, [])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    if (!prof || writeBlocked) return
    setMsg('')
    try {
      const next = await api<CompanyProfile>('/api/company-profile', {
        method: 'POST',
        body: JSON.stringify({
          companyName: prof.companyName,
          contactPerson: prof.contactPerson,
          officeEmail: prof.officeEmail,
          phone: prof.phone,
          address: prof.address,
          defaultExportFormat: prof.defaultExportFormat,
          defaultRecipientEmail: prof.defaultRecipientEmail,
        }),
      })
      setProf(next)
      setMsg('Gespeichert.')
    } catch {
      setMsg('Speichern fehlgeschlagen.')
    }
  }

  async function onLogo(f: FileList | null) {
    if (!f?.[0] || writeBlocked) return
    const fd = new FormData()
    fd.append('file', f[0])
    setMsg('')
    try {
      const r = await api<{ logoUrl: string }>('/api/company-logo', {
        method: 'POST',
        body: fd,
      })
      setProf((p) => (p ? { ...p, logoUrl: r.logoUrl } : p))
      setMsg('Logo aktualisiert.')
    } catch {
      setMsg('Logo konnte nicht hochgeladen werden.')
    }
  }

  if (loading || !prof) {
    return <p className="text-zinc-400">Laden…</p>
  }

  return (
    <div>
      <PageTitle title="Firmenprofil" subtitle="Stammdaten fürs Büro & Export" />

      {prof.logoUrl ? (
        <div className="mb-4 flex justify-center">
          <img src={resolveBackendPublicUrl(prof.logoUrl) ?? prof.logoUrl} alt="Logo" className="h-20 w-auto max-w-full object-contain" />
        </div>
      ) : null}

      <Card className="border-transparent bg-black/40 py-11 shadow-none ring-1 ring-white/[0.08]">
        <form onSubmit={save} className="space-y-4">
          <label className="block">
            <span className="text-sm text-zinc-400">Firmenname</span>
            <input
              className="mt-1 w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              value={prof.companyName}
              onChange={(e) => setProf({ ...prof, companyName: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Ansprechpartner</span>
            <input
              className="mt-1 w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              value={prof.contactPerson}
              onChange={(e) => setProf({ ...prof, contactPerson: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Büro-E-Mail</span>
            <input
              className="mt-1 w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              type="email"
              value={prof.officeEmail}
              onChange={(e) => setProf({ ...prof, officeEmail: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Telefonnummer</span>
            <input
              className="mt-1 w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              value={prof.phone}
              onChange={(e) => setProf({ ...prof, phone: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Adresse</span>
            <textarea
              className="mt-1 min-h-[88px] w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              value={prof.address}
              onChange={(e) => setProf({ ...prof, address: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Standard-Exportformat</span>
            <select
              className="mt-1 w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              value={prof.defaultExportFormat}
              onChange={(e) => setProf({ ...prof, defaultExportFormat: e.target.value })}
            >
              <option value="PDF">PDF</option>
              <option value="Word">Word</option>
            </select>
          </label>

          <label className="block">
            <span className="text-sm text-zinc-400">Firmenlogo</span>
            <div className="mt-3 flex justify-center">
              <input
                id="company-logo-upload"
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={(e) => onLogo(e.target.files)}
                disabled={writeBlocked}
              />
              <label
                htmlFor="company-logo-upload"
                className={`inline-flex min-h-11 items-center justify-center rounded-lg border border-orange-500 bg-orange-500 px-5 py-2 text-sm font-semibold text-zinc-950 transition ${
                  writeBlocked
                    ? 'pointer-events-none cursor-not-allowed opacity-40'
                    : 'cursor-pointer hover:bg-orange-400'
                }`}
              >
                Datei auswählen
              </label>
            </div>
          </label>

          {msg ? <p className="text-sm text-orange-300">{msg}</p> : null}
          <BigButton type="submit" disabled={writeBlocked}>Speichern</BigButton>
        </form>
      </Card>

      {isAdmin ? (
        <div className="mt-6">
          <Link
            to="/verwaltung"
            className="flex min-h-12 items-center justify-between gap-3 rounded-[1rem] border border-white/[0.08] bg-black/35 px-4 py-3 text-sm font-medium text-zinc-200 ring-1 ring-white/[0.05] transition hover:bg-white/[0.05]"
          >
            <span className="flex items-center gap-3">
              <Shield strokeWidth={1.85} className="h-5 w-5 text-orange-300" aria-hidden />
              Verwaltung
            </span>
            <span className="text-zinc-500">›</span>
          </Link>
        </div>
      ) : null}

      <div className="mt-8">
        <PoweredBy />
      </div>

      <div className="mt-6">
        <BigButton
          variant="ghost"
          type="button"
          className="text-zinc-500"
          onClick={() => {
            logout()
            nav('/login', { replace: true })
          }}
        >
          Abmelden
        </BigButton>
      </div>
    </div>
  )
}
