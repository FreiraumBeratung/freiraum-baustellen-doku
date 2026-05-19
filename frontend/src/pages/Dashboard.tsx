import { ChevronRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, resolveBackendPublicUrl } from '../api/client'
import { Card } from '../components/ui'

type CompanyProfile = {
  companyName: string
  logoUrl: string | null
}

const primaryQuick: { to: string; title: string; description: string; emoji: string }[] = [
  {
    to: '/bericht',
    title: 'Tagesbericht aufnehmen',
    description: 'Festhalten und vorbereiten lassen.',
    emoji: '📝',
  },
  { to: '/berichte', title: 'Berichte ansehen', description: 'Verlauf & Export.', emoji: '📋' },
  {
    to: '/baustellen',
    title: 'Baustellen verwalten',
    description: 'Projekte im Blick.',
    emoji: '🏗️',
  },
]

const moreActions: { to: string; title: string; description: string; emoji: string }[] = [
  {
    to: '/mitarbeiter',
    title: 'Mitarbeiter verwalten',
    description: 'Team.',
    emoji: '👷',
  },
  { to: '/profil', title: 'Firmenprofil', description: 'Stammdaten.', emoji: '⚙️' },
]

export function DashboardPage() {
  const [company, setCompany] = useState<CompanyProfile | null>(null)

  useEffect(() => {
    api<CompanyProfile>('/api/company-profile')
      .then(setCompany)
      .catch(() => setCompany({ companyName: '', logoUrl: null }))
  }, [])

  return (
    <div className="space-y-12 pb-4">
      <div className="-mx-4">
        <div className="relative overflow-hidden rounded-b-[2rem] border-b border-white/[0.045] px-7 pb-16 pt-12 text-center sm:pb-[4.25rem] sm:pt-14">
          {/* ruhiger, cineastischer Verlauf */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[linear-gradient(185deg,rgba(9,9,11,0.25)_0%,rgba(9,9,11,0.92)_45%,#09090b_100%)]"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(100%_85%_at_50%_-5%,rgba(249,115,22,0.14),transparent_58%)]"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-[-15%] -top-[50%] h-[120%] rounded-[100%] bg-orange-500/[0.09] blur-[64px]"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-[18%] bottom-[-55%] h-[75%] rounded-[100%] bg-orange-600/[0.06] blur-[52px]"
          />
          <div className="relative mx-auto max-w-[16.5rem]">
            <p className="text-[0.64rem] font-medium uppercase tracking-[0.28em] text-orange-300/85">Freiraum</p>
            <h1 className="mt-5 text-pretty text-[1.75rem] font-semibold tracking-[-0.029em] text-white/96 sm:text-[2rem]">
              Baustellen-Doku
            </h1>
            <p className="mt-6 text-pretty text-[0.97rem] font-normal leading-[1.55] text-zinc-400">
              Aus dem Kopf. Aus dem Sinn.
            </p>
          </div>
        </div>
      </div>

      <section className="flex flex-col items-center gap-5 px-1 text-center">
        {company?.logoUrl ? (
          <img
            src={resolveBackendPublicUrl(company.logoUrl) ?? company.logoUrl}
            alt="Firmenlogo"
            className="h-[4.25rem] w-auto max-w-[200px] object-contain opacity-[0.96]"
          />
        ) : (
          <div
            aria-hidden
            className="flex h-[4.25rem] w-[4.25rem] items-center justify-center rounded-[1.35rem] bg-white/[0.04] text-[1.75rem] ring-1 ring-white/[0.08]"
          >
            🏢
          </div>
        )}
        <p className="text-[1.125rem] font-medium tracking-tight text-white/95 sm:text-[1.2rem]">
          {company?.companyName?.trim() || 'Ihre Firma'}
        </p>
      </section>

      <div className="space-y-4 pt-2">
        <p className="px-1 text-[0.7rem] font-medium tracking-[0.14em] text-zinc-600">Schnellzugriff</p>
        {primaryQuick.map((a) => (
          <Link
            key={a.to}
            to={a.to}
            className="group block rounded-[1.35rem] outline-none ring-offset-[6px] ring-offset-zinc-950 duration-200 focus-visible:ring-2 focus-visible:ring-orange-400/35"
          >
            <div className="relative overflow-hidden rounded-[1.35rem] p-[1px] shadow-[0_24px_48px_-46px_rgba(249,115,22,0.5)] transition-shadow duration-300 group-hover:shadow-[0_28px_54px_-44px_rgba(249,115,22,0.42)]">
              <Card className="relative border-transparent bg-[linear-gradient(152deg,rgba(249,115,22,0.095),transparent_55%)] px-6 py-6 transition-transform duration-200 group-active:scale-[0.99]">
                <div
                  aria-hidden
                  className="pointer-events-none absolute right-[-25%] top-[-55%] h-[130%] w-[62%] rounded-full bg-orange-500/[0.07] blur-[56px]"
                />
                <div className="relative flex items-start gap-5">
                  <span className="flex h-[3.6rem] w-[3.6rem] shrink-0 items-center justify-center rounded-[1.05rem] bg-black/50 text-[1.35rem] ring-1 ring-white/[0.09]">
                    {a.emoji}
                  </span>
                  <div className="min-w-0 flex-1 pt-0.5 text-left">
                    <h2 className="text-[1.035rem] font-semibold tracking-[-0.02em] text-white/97">{a.title}</h2>
                    <p className="mt-2.5 text-[0.875rem] leading-snug text-zinc-500">{a.description}</p>
                  </div>
                  <ChevronRight
                    strokeWidth={1.75}
                    className="relative mt-2 h-[1.05rem] w-[1.05rem] shrink-0 text-zinc-600 transition duration-200 group-hover:translate-x-0.5 group-hover:text-orange-300/80"
                    aria-hidden
                  />
                </div>
              </Card>
            </div>
          </Link>
        ))}
      </div>

      <div className="space-y-4 pt-4">
        <p className="px-1 text-[0.7rem] font-medium tracking-[0.14em] text-zinc-600">Weitere Bereiche</p>
        {moreActions.map((a) => (
          <Link
            key={a.to}
            to={a.to}
            className="group block rounded-[1.35rem] outline-none ring-offset-[6px] ring-offset-zinc-950 duration-200 focus-visible:ring-2 focus-visible:ring-orange-400/35"
          >
            <Card className="border-white/[0.06] px-6 py-[1.1rem] transition-colors duration-200 group-hover:bg-white/[0.04]">
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[1rem] bg-black/45 text-[1.25rem] ring-1 ring-white/[0.08]">
                  {a.emoji}
                </span>
                <div className="min-w-0 flex-1 pt-0.5 text-left">
                  <h2 className="text-[1.035rem] font-semibold tracking-[-0.02em] text-white/96">{a.title}</h2>
                  <p className="mt-1.5 text-[0.875rem] leading-snug text-zinc-500">{a.description}</p>
                </div>
                <ChevronRight
                  strokeWidth={1.75}
                  className="mt-2 h-[1.05rem] w-[1.05rem] shrink-0 text-zinc-600 transition duration-200 group-hover:text-zinc-400"
                  aria-hidden
                />
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
