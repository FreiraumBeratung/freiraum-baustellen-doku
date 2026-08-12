import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { BigButton, Card, PoweredBy, PageTitle } from '../components/ui'
import { PasswordField } from '../components/PasswordField'

export function RegisterPage() {
  const nav = useNavigate()
  const { register } = useAuth()
  const [companyName, setCompanyName] = useState('')
  const [entrepreneurName, setEntrepreneurName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setLoading(true)
    try {
      await register({ companyName, entrepreneurName, email, password })
      nav('/onboarding', { replace: true })
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Registrierung fehlgeschlagen.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageTitle variant="auth" title="Firma registrieren" subtitle="Legen Sie Ihr lokales Firmenkonto in wenigen Schritten an." />
      <Card className="border-zinc-700/80 shadow-xl shadow-black/40">
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm text-zinc-400">Firmenname</span>
            <input
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none focus:border-orange-500"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">Name des Unternehmers</span>
            <input
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none focus:border-orange-500"
              value={entrepreneurName}
              onChange={(e) => setEntrepreneurName(e.target.value)}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-zinc-400">E-Mail</span>
            <input
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none focus:border-orange-500"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <PasswordField
            id="register-password"
            label="Passwort"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {err ? <p className="text-sm text-red-400">{err}</p> : null}
          <BigButton type="submit" disabled={loading}>
            {loading ? '…' : 'Konto erstellen'}
          </BigButton>
        </form>
      </Card>
      <p className="mt-6 text-center text-sm text-zinc-500">
        Bereits registriert?{' '}
        <Link className="font-medium text-orange-400 hover:underline" to="/login">
          Zum Login
        </Link>
      </p>
      <div className="mt-8">
        <PoweredBy />
      </div>
    </div>
  )
}
