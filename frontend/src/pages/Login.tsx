import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiAuthDebugOriginLabel, getDebugPing, LoginRequestError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'
import { PasswordField } from '../components/PasswordField'

function formatLoginErrorDev(err: unknown): string {
  if (err instanceof LoginRequestError) {
    const lines = ['Login fehlgeschlagen.', `API: ${err.apiBase}`]
    if (err.kind === 'network') {
      lines.push(`Netzwerkfehler: ${err.message}`)
      lines.push('(fetch ohne gültige HTTP-Antwort — kein Backend-Status gelesen.)')
      return lines.join('\n')
    }
    lines.push(`Status: ${err.status ?? '—'}`)
    lines.push(`Meldung: ${err.backendMessage ?? '—'}`)
    lines.push('Fetch hat das Backend erreicht (HTTP-Antwort erhalten).')
    return lines.join('\n')
  }
  if (err instanceof Error) {
    return ['Login fehlgeschlagen.', `API: ${apiAuthDebugOriginLabel()}`, `Meldung: ${err.message}`].join('\n')
  }
  return ['Login fehlgeschlagen.', `API: ${apiAuthDebugOriginLabel()}`].join('\n')
}

function formatLoginErrorProd(err: unknown): string {
  if (err instanceof LoginRequestError) {
    if (err.kind === 'network') {
      return err.message
    }
    return err.backendMessage ?? 'Ungültige Zugangsdaten'
  }
  if (err instanceof Error) return err.message
  return 'Login fehlgeschlagen.'
}

export function LoginPage() {
  const nav = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const [pingBusy, setPingBusy] = useState(false)
  const [pingMsg, setPingMsg] = useState('')

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setLoading(true)
    try {
      await login(email, password)
      nav('/', { replace: true })
    } catch (caught) {
      setErr(import.meta.env.DEV ? formatLoginErrorDev(caught) : formatLoginErrorProd(caught))
    } finally {
      setLoading(false)
    }
  }

  async function onPingBackend() {
    setPingMsg('')
    setPingBusy(true)
    try {
      const r = await getDebugPing()
      setPingMsg(r.ok ? 'Backend erreichbar' : r.message ?? 'Backend nicht erreichbar')
    } catch {
      setPingMsg('Backend nicht erreichbar')
    } finally {
      setPingBusy(false)
    }
  }

  return (
    <div>
      <PageTitle
        variant="auth"
        title="Willkommen zurück"
        subtitle="Melden Sie sich an – Ihre Baustellenberichte immer griffbereit."
      />
      <Card className="border-zinc-700/80 shadow-xl shadow-black/40">
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm text-zinc-400">E-Mail</span>
            <input
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none focus:border-orange-500"
              type="email"
              inputMode="email"
              autoComplete="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <PasswordField
            id="login-password"
            label="Passwort"
            autoComplete="current-password"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {err ? (
            <p className="whitespace-pre-line text-sm text-red-400" role="alert">
              {err}
            </p>
          ) : null}
          <BigButton type="submit" disabled={loading}>
            {loading ? '…' : 'Einloggen'}
          </BigButton>
        </form>
        {import.meta.env.DEV ? (
          <div className="mt-4 border-t border-zinc-800 pt-4">
            <BigButton type="button" variant="secondary" disabled={pingBusy} onClick={() => void onPingBackend()}>
              {pingBusy ? '…' : 'Backend testen'}
            </BigButton>
            {pingMsg ? (
              <p className="mt-2 whitespace-pre-line text-center text-sm text-zinc-400">{pingMsg}</p>
            ) : null}
          </div>
        ) : null}
      </Card>
      <p className="mt-6 text-center text-sm text-zinc-500">
        Noch kein Konto?{' '}
        <Link className="font-medium text-orange-400 hover:underline" to="/register">
          Registrieren
        </Link>
      </p>
      <div className="mt-8">
        <PoweredBy />
      </div>
    </div>
  )
}
