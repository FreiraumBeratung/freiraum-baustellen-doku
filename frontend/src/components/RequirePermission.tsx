import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { AppPermission } from '../utils/accountPermissions'

/** Leitet ohne Recht oder ohne Firmen-Modul auf Home um. */
export function RequirePermission({
  permission,
  children,
}: {
  permission: AppPermission
  children: React.ReactNode
}) {
  const { can, ready } = useAuth()
  if (!ready) {
    return <div className="p-8 text-center text-zinc-400">Laden…</div>
  }
  if (!can(permission)) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
