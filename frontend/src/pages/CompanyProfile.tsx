import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, resolveBackendPublicUrl } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'

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
  const { logout } = useAuth()
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
    if (!prof) return
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
    if (!f?.[0]) return
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
            <span className="text-sm text-zinc-400">Standard-Empfänger (Büro)</span>
            <input
              className="mt-1 w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              type="email"
              value={prof.defaultRecipientEmail}
              onChange={(e) => setProf({ ...prof, defaultRecipientEmail: e.target.value })}
            />
          </label>

          <label className="block">
            <span className="text-sm text-zinc-400">Firmenlogo</span>
            <input
              type="file"
              accept="image/*"
              className="mt-2 w-full text-sm text-zinc-400 file:mr-3 file:rounded-lg file:border-0 file:bg-orange-500 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-zinc-950"
              onChange={(e) => onLogo(e.target.files)}
            />
          </label>

          {msg ? <p className="text-sm text-orange-300">{msg}</p> : null}
          <BigButton type="submit">Speichern</BigButton>
        </form>
      </Card>

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
