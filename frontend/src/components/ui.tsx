import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function Card({
  children,
  className = '',
  id,
}: {
  children: ReactNode
  className?: string
  id?: string
}) {
  return (
    <div
      id={id}
      className={`rounded-[1.35rem] border border-white/[0.06] bg-zinc-900/[0.42] p-6 shadow-[0_20px_50px_-38px_rgba(0,0,0,0.88)] ring-1 ring-white/[0.04] ${className}`}
    >
      {children}
    </div>
  )
}

export function BigButton({
  children,
  className = '',
  variant = 'primary',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost'
}) {
  const base =
    'min-h-14 w-full rounded-2xl px-4 py-3 text-base font-semibold transition active:scale-[0.99] disabled:opacity-40'
  const styles =
    variant === 'primary'
      ? 'bg-orange-500 text-zinc-950 hover:bg-orange-400'
      : variant === 'secondary'
        ? 'border border-zinc-600 bg-zinc-800 text-white hover:bg-zinc-700'
        : 'bg-transparent text-zinc-300 hover:bg-zinc-800'
  return (
    <button type="button" className={`${base} ${styles} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function PageTitle({
  title,
  subtitle,
  variant = 'default',
}: {
  title: string
  subtitle?: string
  variant?: 'default' | 'auth'
}) {
  if (variant === 'auth') {
    return (
      <header className="mb-12 text-center">
        <p className="mb-4 text-[0.62rem] font-medium uppercase tracking-[0.18em] text-orange-400/88">
          Baustellen-Doku
        </p>
        <h1 className="text-balance text-2xl font-bold tracking-tight text-white sm:text-3xl">{title}</h1>
        {subtitle ? <p className="mt-4 text-pretty text-[0.9rem] leading-relaxed text-zinc-500">{subtitle}</p> : null}
      </header>
    )
  }
  return (
    <header className="mb-9">
      <h1 className="text-[1.375rem] font-semibold tracking-[-0.025em] text-white/97">{title}</h1>
      {subtitle ? <p className="mt-3 text-[0.9rem] font-normal leading-relaxed text-zinc-500">{subtitle}</p> : null}
    </header>
  )
}

export function PoweredBy() {
  return (
    <p className="text-center text-xs text-zinc-500">
      Powered by{' '}
      <span className="text-zinc-400">Freiraum Beratung</span>
    </p>
  )
}
