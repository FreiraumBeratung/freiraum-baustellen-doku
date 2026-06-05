import { LICENSE_SUSPENDED_MESSAGE } from '../constants/license'
import { useAuth } from '../context/AuthContext'

export function LicenseSuspendedBanner() {
  const { licenseActive } = useAuth()
  if (licenseActive) return null

  return (
    <div
      role="alert"
      className="mb-5 rounded-2xl border border-amber-500/35 bg-amber-500/[0.09] px-4 py-3.5 text-sm text-amber-100 ring-1 ring-amber-500/20"
    >
      <p className="font-semibold tracking-tight text-amber-50">Zugang pausiert</p>
      <p className="mt-1.5 leading-snug text-amber-100/92">{LICENSE_SUSPENDED_MESSAGE}</p>
      <p className="mt-2 text-xs leading-relaxed text-amber-200/75">
        Sie können Ihre bestehenden Daten weiter ansehen und exportieren. Neue Einträge sind derzeit nicht möglich.
      </p>
    </div>
  )
}
