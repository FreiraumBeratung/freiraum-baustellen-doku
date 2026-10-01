import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Settings, Shield, X } from 'lucide-react'
import { api, resolveBackendPublicUrl } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { BigButton, Card, PageTitle, PoweredBy, Switch } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

type CompanyProfile = {
  companyName: string
  contactPerson: string
  officeEmail: string
  phone: string
  address: string
  defaultExportFormat: string
  defaultRecipientEmail: string
  includePhotosInPdf: boolean
  protocolReminderEnabled: boolean
  protocolReminderTime: string
  logoUrl: string | null
}

type SettingsSlice = {
  includePhotosInPdf: boolean
  protocolReminderEnabled: boolean
  protocolReminderTime: string
}

export function CompanyProfilePage() {
  const nav = useNavigate()
  const { logout, isAdmin } = useAuth()
  const { writeBlocked } = useWriteBlocked()
  const [prof, setProf] = useState<CompanyProfile | null>(null)
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const settingsSnap = useRef<SettingsSlice | null>(null)
  const profRef = useRef(prof)
  profRef.current = prof

  useEffect(() => {
    api<CompanyProfile>('/api/company-profile')
      .then((p) =>
        setProf({
          ...p,
          includePhotosInPdf: Boolean(p.includePhotosInPdf),
          protocolReminderEnabled: Boolean(p.protocolReminderEnabled),
          protocolReminderTime: p.protocolReminderTime || '21:00',
        }),
      )
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!settingsOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeSettings(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [settingsOpen])

  function openSettings() {
    if (!prof) return
    settingsSnap.current = {
      includePhotosInPdf: Boolean(prof.includePhotosInPdf),
      protocolReminderEnabled: Boolean(prof.protocolReminderEnabled),
      protocolReminderTime: prof.protocolReminderTime || '21:00',
    }
    setSettingsOpen(true)
  }

  function closeSettings(keep: boolean) {
    if (!keep && settingsSnap.current) {
      const snap = settingsSnap.current
      setProf((p) => (p ? { ...p, ...snap } : p))
    }
    settingsSnap.current = null
    setSettingsOpen(false)
  }

  async function persist(): Promise<boolean> {
    const current = profRef.current
    if (!current || writeBlocked) return false
    setMsg('')
    try {
      const next = await api<CompanyProfile>('/api/company-profile', {
        method: 'POST',
        body: JSON.stringify({
          companyName: current.companyName,
          contactPerson: current.contactPerson,
          officeEmail: current.officeEmail,
          phone: current.phone,
          address: current.address,
          defaultExportFormat: current.defaultExportFormat,
          defaultRecipientEmail: current.defaultRecipientEmail,
          includePhotosInPdf: Boolean(current.includePhotosInPdf),
          protocolReminderEnabled: Boolean(current.protocolReminderEnabled),
          protocolReminderTime: current.protocolReminderTime || '21:00',
        }),
      })
      setProf({
        ...next,
        includePhotosInPdf: Boolean(next.includePhotosInPdf),
        protocolReminderEnabled: Boolean(next.protocolReminderEnabled),
        protocolReminderTime: next.protocolReminderTime || '21:00',
      })
      setMsg('Gespeichert.')
      return true
    } catch {
      setMsg('Speichern fehlgeschlagen.')
      return false
    }
  }

  async function save(e: React.FormEvent) {
    e.preventDefault()
    await persist()
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

      <div className="mt-6">
        <button
          type="button"
          onClick={openSettings}
          className="flex min-h-12 w-full items-center justify-between gap-3 rounded-[1rem] border border-white/[0.08] bg-black/35 px-4 py-3 text-sm font-medium text-zinc-200 ring-1 ring-white/[0.05] transition hover:bg-white/[0.05] active:scale-[0.99]"
        >
          <span className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-500/12 ring-1 ring-orange-400/20">
              <Settings strokeWidth={1.85} className="h-5 w-5 text-orange-300" aria-hidden />
            </span>
            Einstellungen
          </span>
          <span className="text-zinc-500">›</span>
        </button>
      </div>

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

      {settingsOpen ? (
        <div
          className="fixed inset-0 z-[80] flex flex-col justify-end bg-black/62 backdrop-blur-[3px]"
          role="dialog"
          aria-modal="true"
          aria-labelledby="company-settings-title"
          onClick={() => closeSettings(false)}
        >
          <div
            className="freiraum-sheet-up mx-auto w-full max-w-[390px] rounded-t-[1.75rem] border border-white/[0.08] border-b-0 bg-zinc-950 px-4 pb-[calc(1.25rem+env(safe-area-inset-bottom,0px))] pt-2 shadow-[0_-18px_50px_-28px_rgba(0,0,0,0.9)] ring-1 ring-white/[0.06]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-white/18" aria-hidden />
            <div className="mb-5 flex items-center justify-between gap-3">
              <h2 id="company-settings-title" className="text-[1.05rem] font-semibold tracking-tight text-white">
                Einstellungen
              </h2>
              <button
                type="button"
                onClick={() => closeSettings(false)}
                aria-label="Schließen"
                className="rounded-full p-1.5 text-zinc-500 transition hover:bg-white/[0.06] hover:text-zinc-300"
              >
                <X strokeWidth={2} className="h-5 w-5" aria-hidden />
              </button>
            </div>

            <div className="space-y-3">
              <div className="rounded-2xl border border-white/[0.06] bg-black/40 px-3 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-zinc-300">Fotos in der Tagesbericht-PDF</span>
                  <Switch
                    checked={Boolean(prof.includePhotosInPdf)}
                    onChange={(next) =>
                      setProf((p) => (p ? { ...p, includePhotosInPdf: next } : p))
                    }
                    disabled={writeBlocked}
                    label="Fotos in der Tagesbericht-PDF"
                  />
                </div>
                <p className="mt-2 text-[0.72rem] leading-snug text-zinc-600">
                  {prof.includePhotosInPdf
                    ? 'An: die Bilder stehen im PDF. In der Mail dann kein extra Foto-Anhang.'
                    : 'Aus: Fotos bleiben in der App und gehen wie bisher extra mit der Mail.'}
                </p>
              </div>

              <div className="rounded-2xl border border-white/[0.06] bg-black/40 px-3 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-zinc-300">Erinnerung für Protokoll</span>
                  <Switch
                    checked={Boolean(prof.protocolReminderEnabled)}
                    onChange={(next) =>
                      setProf((p) => (p ? { ...p, protocolReminderEnabled: next } : p))
                    }
                    disabled={writeBlocked}
                    label="Erinnerung für Protokoll"
                  />
                </div>
                <p className="mt-2 text-[0.72rem] leading-snug text-zinc-600">
                  {prof.protocolReminderEnabled
                    ? 'An: ab dieser Uhr auf Home, wenn Gedankensammlung, Schnellnotiz oder Protokoll noch nicht ans Büro ging.'
                    : 'Aus: keine Erinnerung. Senden ans Büro bleibt wie bisher.'}
                </p>
                {prof.protocolReminderEnabled ? (
                  <label className="mt-3 block">
                    <span className="text-xs tracking-wide text-zinc-400">Uhrzeit</span>
                    <input
                      type="time"
                      lang="de-DE"
                      className="mt-1 w-full min-w-0 rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-[0.65rem] text-white outline-none ring-1 ring-transparent focus:border-orange-500/47 focus:ring-orange-500/42 [color-scheme:dark] disabled:opacity-50"
                      value={prof.protocolReminderTime || '21:00'}
                      disabled={writeBlocked}
                      onChange={(e) => {
                        const stamp = e.target.value || '21:00'
                        setProf((p) => (p ? { ...p, protocolReminderTime: stamp } : p))
                      }}
                    />
                  </label>
                ) : null}
              </div>
            </div>

            {msg ? <p className="mt-3 text-sm text-orange-300">{msg}</p> : null}
            <div className="mt-5">
              <BigButton
                type="button"
                disabled={writeBlocked}
                onClick={async () => {
                  const ok = await persist()
                  if (ok) closeSettings(true)
                }}
              >
                Speichern
              </BigButton>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
