import { useEffect, useState } from 'react'

const PRESETS = [0, 15, 30, 45, 60, 90] as const
const CUSTOM = 'custom'

function isPreset(value: number): boolean {
  return (PRESETS as readonly number[]).includes(value)
}

function clampBreak(n: number): number {
  if (!Number.isFinite(n)) return 45
  return Math.max(0, Math.min(480, Math.round(n)))
}

export function BreakMinutesSelect({
  value,
  onChange,
  disabled,
  className,
}: {
  value: number
  onChange: (minutes: number) => void
  disabled?: boolean
  className: string
}) {
  const [customMode, setCustomMode] = useState(() => !isPreset(value))
  const [draft, setDraft] = useState<string | null>(null)

  useEffect(() => {
    if (!isPreset(value)) setCustomMode(true)
  }, [value])

  if (customMode) {
    return (
      <div className="flex items-center gap-2">
        <input
          type="number"
          inputMode="numeric"
          min={0}
          max={480}
          step={1}
          className={className}
          value={draft !== null ? draft : Number.isFinite(value) ? String(value) : ''}
          disabled={disabled}
          aria-label="Individuelle Pause in Minuten"
          onChange={(e) => {
            const raw = e.target.value
            setDraft(raw)
            if (raw.trim() === '') return
            const n = Number(raw)
            if (!Number.isFinite(n)) return
            onChange(clampBreak(n))
          }}
          onBlur={() => setDraft(null)}
        />
        <button
          type="button"
          disabled={disabled}
          className="shrink-0 text-xs font-medium text-orange-400 hover:underline disabled:opacity-50"
          onClick={() => {
            setDraft(null)
            setCustomMode(false)
            if (!isPreset(value)) onChange(45)
          }}
        >
          Auswahl
        </button>
      </div>
    )
  }

  return (
    <select
      className={className}
      value={isPreset(value) ? value : CUSTOM}
      disabled={disabled}
      onChange={(e) => {
        if (e.target.value === CUSTOM) {
          setCustomMode(true)
          return
        }
        setCustomMode(false)
        onChange(Number(e.target.value))
      }}
    >
      <option value={0}>Keine Pause</option>
      <option value={15}>15 Minuten</option>
      <option value={30}>30 Minuten</option>
      <option value={45}>45 Minuten</option>
      <option value={60}>60 Minuten</option>
      <option value={90}>90 Minuten</option>
      <option value={CUSTOM}>Individuelle Zeit</option>
    </select>
  )
}
