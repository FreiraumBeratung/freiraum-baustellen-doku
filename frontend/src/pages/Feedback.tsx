import { useMemo, useState } from 'react'
import { BigButton, Card, PageTitle, PoweredBy } from '../components/ui'
import { sendFeedback, type FeedbackCategory } from '../api/client'
import { useWriteBlocked } from '../hooks/useWriteBlocked'

const CATEGORY_OPTIONS: FeedbackCategory[] = ['Problem', 'Verbesserung', 'Lob']

function appVersionLabel(): string {
  const v = (import.meta.env.VITE_APP_VERSION as string | undefined)?.trim()
  return v || 'web'
}

export function FeedbackPage() {
  const { writeBlocked } = useWriteBlocked()
  const [category, setCategory] = useState<FeedbackCategory>('Verbesserung')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastSentAt, setLastSentAt] = useState<string | null>(null)
  const charsLeft = useMemo(() => 1000 - text.length, [text.length])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (writeBlocked || busy) return
    const msg = text.trim()
    if (msg.length < 3) {
      setError('Bitte mindestens 3 Zeichen eingeben.')
      setMessage(null)
      return
    }
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const res = await sendFeedback({
        category,
        message: msg,
        page: window.location.pathname,
        appVersion: appVersionLabel(),
      })
      const sentAt = new Date()
      setLastSentAt(
        `${sentAt.toLocaleDateString('de-DE')} um ${sentAt.toLocaleTimeString('de-DE', {
          hour: '2-digit',
          minute: '2-digit',
        })}`,
      )
      setMessage(res.message || 'Danke! Feedback wurde gesendet.')
      setText('')
      setCategory('Verbesserung')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Feedback konnte nicht gesendet werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageTitle title="Feedback" subtitle="Direkt aus der App senden" />

      <Card className="border-transparent bg-black/40 py-8 shadow-none ring-1 ring-white/[0.08]">
        <form onSubmit={onSubmit} className="space-y-5">
          <div>
            <p className="text-sm text-zinc-400">Kategorie</p>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {CATEGORY_OPTIONS.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setCategory(opt)}
                  className={`min-h-11 rounded-xl border px-2 text-sm font-semibold transition ${
                    category === opt
                      ? 'border-orange-500/55 bg-orange-500/15 text-orange-200'
                      : 'border-white/[0.1] bg-black/45 text-zinc-300 hover:border-zinc-500/60 hover:text-zinc-100'
                  }`}
                  disabled={busy || writeBlocked}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          <label className="block">
            <span className="text-sm text-zinc-400">Dein Feedback</span>
            <textarea
              className="mt-2 min-h-[180px] w-full rounded-[1rem] border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none ring-1 ring-transparent focus:border-orange-500/55 focus:ring-orange-500/42"
              placeholder="Was war gut, was war schlecht, was sollten wir verbessern?"
              value={text}
              onChange={(e) => setText(e.target.value.slice(0, 1000))}
              disabled={busy || writeBlocked}
            />
            <p className="mt-2 text-right text-xs text-zinc-500">{charsLeft} Zeichen übrig</p>
          </label>

          {message ? <p className="text-sm text-orange-300">{message}</p> : null}
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          {lastSentAt ? <p className="text-xs text-zinc-500">Feedback gesendet am {lastSentAt}</p> : null}

          <BigButton type="submit" disabled={busy || writeBlocked}>
            {busy ? 'Wird gesendet…' : 'Feedback senden'}
          </BigButton>
        </form>
      </Card>

      <div className="mt-8">
        <PoweredBy />
      </div>
    </div>
  )
}

