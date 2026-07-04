import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, resolveBackendPublicUrl } from '../api/client'

type CompanyProfile = {
  companyName: string
  logoUrl: string | null
}

type Tile = { to: string; title: string; emoji: string; primary?: boolean }

const tiles: Tile[] = [
  { to: '/bericht', title: 'Tagesbericht', emoji: '📝', primary: true },
  { to: '/berichte', title: 'Berichte', emoji: '📋' },
  { to: '/stunden', title: 'Stundenkonto', emoji: '⏱️' },
  { to: '/baustellen', title: 'Baustellen', emoji: '🏗️' },
  { to: '/mitarbeiter', title: 'Mitarbeiter', emoji: '👷' },
  { to: '/profil', title: 'Firmenprofil', emoji: '⚙️' },
]

export function DashboardPage() {
  const [company, setCompany] = useState<CompanyProfile | null>(null)

  useEffect(() => {
    api<CompanyProfile>('/api/company-profile')
      .then(setCompany)
      .catch(() => setCompany({ companyName: '', logoUrl: null }))
  }, [])

  return (
    <div className="flex min-h-full flex-col">
      {/* Dominanter Kopf: großes Logo schafft das „meine App"-Gefühl */}
      <header className="relative -mx-4 overflow-hidden rounded-b-[2rem] border-b border-white/[0.05] px-6 pb-12 pt-12 text-center">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_100%_at_50%_-12%,rgba(249,115,22,0.17),transparent_64%)]"
        />
        <div className="relative flex flex-col items-center gap-5">
          <p className="text-[0.72rem] font-medium uppercase tracking-[0.3em] text-orange-300/85">
            Freiraum · Baustellen-Doku
          </p>
          {company?.logoUrl ? (
            <div className="dashboard-company-logo flex items-center justify-center">
              <img
                src={resolveBackendPublicUrl(company.logoUrl) ?? company.logoUrl}
                alt="Firmenlogo"
                className="h-[6.25rem] w-auto max-w-[260px] object-contain"
              />
            </div>
          ) : (
            <div
              aria-hidden
              className="flex h-[7rem] w-[7rem] items-center justify-center rounded-[1.6rem] bg-white/[0.05] text-[2.8rem] ring-1 ring-white/[0.08]"
            >
              🏢
            </div>
          )}
          <p className="text-[1.55rem] font-semibold tracking-tight text-white/96">
            {company?.companyName?.trim() || 'Ihre Firma'}
          </p>
        </div>
      </header>

      {/* 3 + 3 Kacheln — ans untere Ende geschoben: alles bequem mit dem Daumen erreichbar */}
      <nav aria-label="Schnellzugriff" className="mt-auto grid grid-cols-3 gap-2.5 pb-1 pt-8">
        {tiles.map((t) => (
          <Link
            key={t.to}
            to={t.to}
            className={`group relative flex aspect-square flex-col items-center justify-center gap-2.5 rounded-[1.25rem] px-1.5 text-center outline-none ring-offset-2 ring-offset-zinc-950 transition focus-visible:ring-2 focus-visible:ring-orange-400/40 active:scale-[0.98] ${
              t.primary
                ? 'border border-orange-400/35 bg-[linear-gradient(155deg,rgba(249,115,22,0.16),rgba(249,115,22,0.04)_60%)] ring-1 ring-orange-400/20'
                : 'border border-white/[0.07] bg-zinc-900/[0.5] ring-1 ring-white/[0.04] hover:bg-white/[0.05]'
            }`}
          >
            <span
              className={`flex h-[3rem] w-[3rem] items-center justify-center rounded-[1rem] text-[1.45rem] ring-1 transition ${
                t.primary
                  ? 'bg-black/40 ring-orange-300/25'
                  : 'bg-black/45 ring-white/[0.08] group-hover:ring-white/[0.14]'
              }`}
            >
              {t.emoji}
            </span>
            <span
              className={`text-[0.8rem] font-medium leading-tight tracking-tight ${
                t.primary ? 'text-orange-100/95' : 'text-zinc-300'
              }`}
            >
              {t.title}
            </span>
          </Link>
        ))}
      </nav>
    </div>
  )
}
