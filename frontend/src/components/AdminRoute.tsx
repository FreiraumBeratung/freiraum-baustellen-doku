import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { AdminPage } from '../pages/Admin'

export function AdminRoute() {
  const { isAdmin, ready } = useAuth()
  if (!ready) {
    return <div className="p-8 text-center text-zinc-400">Laden…</div>
  }
  if (!isAdmin) {
    return <Navigate to="/" replace />
  }
  return <AdminPage />
}
