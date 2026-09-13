import { useEffect, useState } from 'react'
import { getPushConfig, getPushStatus } from '../api/client'
import { disablePushOnDevice, enablePushOnDevice, pushSupported } from '../utils/pushOptIn'

export function TaskPushOptIn({ isOwner }: { isOwner: boolean }) {
  const [visible, setVisible] = useState(false)
  const [on, setOn] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!pushSupported()) return
    let cancelled = false
    Promise.all([getPushConfig(), getPushStatus()])
      .then(([cfg, status]) => {
        if (cancelled) return
        if (!cfg.enabled || !cfg.publicKey) return
        setVisible(true)
        setOn(Boolean(status.subscribed))
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  if (!visible) return null

  async function toggle() {
    if (busy) return
    setBusy(true)
    setErr('')
    try {
      if (on) {
        await disablePushOnDevice()
        setOn(false)
      } else {
        await enablePushOnDevice()
        setOn(true)
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Hinweis konnte nicht geändert werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-6 rounded-2xl border border-white/[0.06] bg-black/30 px-3 py-3">
      <label className="flex items-center justify-between gap-3">
        <span className="text-sm text-zinc-300">
          {isOwner ? 'Hinweis wenn erledigt' : 'Hinweis bei neuen Aufgaben'}
        </span>
        <button
          type="button"
          role="switch"
          aria-checked={on}
          disabled={busy}
          onClick={() => void toggle()}
          className={`relative h-7 w-12 shrink-0 rounded-full transition ${
            on ? 'bg-orange-500' : 'bg-zinc-700'
          } disabled:opacity-50`}
        >
          <span
            className={`absolute top-0.5 h-6 w-6 rounded-full bg-white transition ${
              on ? 'left-5' : 'left-0.5'
            }`}
          />
        </button>
      </label>
      {err ? <p className="mt-2 text-xs text-red-400">{err}</p> : null}
    </div>
  )
}
