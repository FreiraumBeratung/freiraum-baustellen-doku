import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, resolveBackendPublicUrl } from '../api/client'
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

const inputClass =
  'mt-1 w-full min-w-0 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none focus:border-orange-500'

export function OnboardingPage() {
  const nav = useNavigate()
  const [prof, setProf] = useState<CompanyProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    api<CompanyProfile>('/api/company-profile')
      .then(setProf)
      .catch(() => setErr('Profil konnte nicht geladen werden.'))
      .finally(() => setLoading(false))
  }, [])

  async function onLogo(f: FileList | null) {
    if (!f?.[0]) return
    const fd = new FormData()
    fd.append('file', f[0])
    setErr('')
    try {
      const r = await api<{ logoUrl: string }>('/api/company-logo', {
        method: 'POST',
        body: fd,
      })
      setProf((p) => (p ? { ...p, logoUrl: r.logoUrl } : p))
    } catch {
      setErr('Logo konnte nicht hochgeladen werden.')
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!prof) return
    setErr('')
    setSaving(true)
    try {
      const office = prof.officeEmail.trim()
      const recipient = prof.defaultRecipientEmail.trim() || office
      const next = await api<CompanyProfile>('/api/company-profile', {
        method: 'POST',
        body: JSON.stringify({
          companyName: prof.companyName,
          contactPerson: prof.contactPerson,
          officeEmail: office,
          phone: prof.phone,
          address: prof.address,
          defaultExportFormat: prof.defaultExportFormat,
          defaultRecipientEmail: recipient,
        }),
      })
      setProf(next)
      nav('/', { replace: true })
    } catch {
      setErr('Speichern fehlgeschlagen. Bitte alle Pflichtfelder prüfen.')
    } finally {
      setSaving(false)
    }
  }

  if (loading || !prof) {
    return <p className="text-center text-zinc-400">Laden…</p>
  }

  return (
    <div className="mx-auto w-full max-w-lg px-4 pb-8 pt-6">
      <PageTitle
        title="Willkommen bei Baustellen-Doku"
        subtitle="Richten Sie Ihr Firmenprofil ein — einmal ausfüllen, dann direkt loslegen."
      />

      {prof.logoUrl ? (
        <div className="mb-4 flex justify-center">
          <img src={resolveBackendPublicUrl(prof.logoUrl) ?? prof.logoUrl} alt="Firmenlogo" className="h-16 w-auto max-w-full object-contain" />
        </div>
      ) : null}

      <Card className="border-zinc-700/80 p-5">
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm text-zinc-400">Firmenname *</span>
            <input
              className={inputClass}
              value={prof.companyName}
              onChange={(e) => setProf({ ...prof, companyName: e.target.value })}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Ansprechpartner *</span>
            <input
              className={inputClass}
              value={prof.contactPerson}
              onChange={(e) => setProf({ ...prof, contactPerson: e.target.value })}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Büro-E-Mail *</span>
            <input
              className={inputClass}
              type="email"
              autoComplete="email"
              value={prof.officeEmail}
              onChange={(e) => setProf({ ...prof, officeEmail: e.target.value })}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Telefonnummer *</span>
            <input
              className={inputClass}
              type="tel"
              autoComplete="tel"
              value={prof.phone}
              onChange={(e) => setProf({ ...prof, phone: e.target.value })}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Adresse *</span>
            <textarea
              className={`${inputClass} min-h-[88px] resize-y`}
              value={prof.address}
              onChange={(e) => setProf({ ...prof, address: e.target.value })}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Standard-Exportformat *</span>
            <select
              className={inputClass}
              value={prof.defaultExportFormat}
              onChange={(e) => setProf({ ...prof, defaultExportFormat: e.target.value })}
            >
              <option value="PDF">PDF</option>
              <option value="Word">Word</option>
            </select>
          </label>

          <label className="block">
            <span className="text-sm text-zinc-400">Firmenlogo (optional)</span>
            <input
              type="file"
              accept="image/*"
              className="mt-2 w-full min-w-0 text-sm text-zinc-400 file:mr-3 file:rounded-lg file:border-0 file:bg-orange-500 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-zinc-950"
              onChange={(e) => onLogo(e.target.files)}
            />
          </label>

          {err ? <p className="text-sm text-red-400">{err}</p> : null}
          <BigButton type="submit" disabled={saving}>
            {saving ? '…' : 'Speichern & zum Dashboard'}
          </BigButton>
        </form>
      </Card>

      <div className="mt-8">
        <PoweredBy />
      </div>
    </div>
  )
}
