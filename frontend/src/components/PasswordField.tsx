import { Eye, EyeOff } from 'lucide-react'
import { useState, type InputHTMLAttributes } from 'react'

type PasswordFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string
}

/** Passwortfeld mit Sichtbarkeits-Toggle (Auge) — nur UI, kein Speicherverhalten. */
export function PasswordField({ label, className = '', id, ...inputProps }: PasswordFieldProps) {
  const [visible, setVisible] = useState(false)
  const inputId = id ?? 'password-field'

  return (
    <label className="block" htmlFor={inputId}>
      <span className="text-sm text-zinc-400">{label}</span>
      <div className="relative mt-1">
        <input
          {...inputProps}
          id={inputId}
          type={visible ? 'text' : 'password'}
          className={`w-full rounded-xl border border-zinc-700 bg-zinc-950 py-3 pl-3 pr-12 text-white outline-none focus:border-orange-500 ${className}`}
        />
        <button
          type="button"
          className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-zinc-400 hover:text-zinc-200"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Passwort verbergen' : 'Passwort anzeigen'}
          tabIndex={-1}
        >
          {visible ? <EyeOff className="h-5 w-5" aria-hidden /> : <Eye className="h-5 w-5" aria-hidden />}
        </button>
      </div>
    </label>
  )
}
