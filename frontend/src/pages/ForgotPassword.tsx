import { useState } from 'react'
import { Link } from 'react-router-dom'
import { requestPasswordReset } from '../api/client'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setMsg('')
    setLoading(true)
    try {
      const r = await requestPasswordReset(email)
      setMsg(r.message || 'Wenn ein Konto zu dieser E-Mail existiert, senden wir einen Link.')
    } catch (caught) {
      setErr(caught instanceof Error ? caught.message : 'Anfrage fehlgeschlagen.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageTitle
        variant="auth"
        title="Passwort vergessen"
        subtitle="Wir schicken einen Link an Ihre Registrierungs-Mail. Das alte Passwort bleibt geheim — Sie setzen ein neues."
      />
      <Card className="border-zinc-700/80 shadow-xl shadow-black/40">
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm text-zinc-400">E-Mail</span>
            <input
              className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-white outline-none focus:border-orange-500"
              type="email"
              autoComplete="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          {msg ? <p className="text-sm text-orange-300">{msg}</p> : null}
          {err ? <p className="text-sm text-red-400">{err}</p> : null}
          <BigButton type="submit" disabled={loading}>
            {loading ? '…' : 'Link senden'}
          </BigButton>
        </form>
      </Card>
      <p className="mt-6 text-center text-sm text-zinc-500">
        Zurück zum{' '}
        <Link className="font-medium text-orange-400 hover:underline" to="/login">
          Login
        </Link>
      </p>
      <div className="mt-8">
        <PoweredBy />
      </div>
    </div>
  )
}
