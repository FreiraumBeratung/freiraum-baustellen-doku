import { useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { submitPasswordReset } from '../api/client'
import { PasswordField } from '../components/PasswordField'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'

export function ResetPasswordPage() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const token = useMemo(() => (params.get('token') || '').trim(), [params])
  const [password, setPassword] = useState('')
  const [repeat, setRepeat] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    if (!token) {
      setErr('Link unvollständig. Bitte „Passwort vergessen“ erneut nutzen.')
      return
    }
    if (password !== repeat) {
      setErr('Die neuen Passwörter stimmen nicht überein.')
      return
    }
    setLoading(true)
    try {
      await submitPasswordReset({ token, newPassword: password })
      nav('/login', { replace: true })
    } catch (caught) {
      setErr(caught instanceof Error ? caught.message : 'Zurücksetzen fehlgeschlagen.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageTitle
        variant="auth"
        title="Neues Passwort"
        subtitle="Wählen Sie ein eigenes Passwort. Der Link gilt nur einmal und nur kurz."
      />
      <Card className="border-zinc-700/80 shadow-xl shadow-black/40">
        <form onSubmit={onSubmit} className="space-y-4">
          <PasswordField
            id="reset-password"
            label="Neues Passwort"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <PasswordField
            id="reset-password-repeat"
            label="Neues Passwort wiederholen"
            autoComplete="new-password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            required
            minLength={8}
          />
          {err ? <p className="text-sm text-red-400">{err}</p> : null}
          <BigButton type="submit" disabled={loading || !token}>
            {loading ? '…' : 'Passwort speichern'}
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
