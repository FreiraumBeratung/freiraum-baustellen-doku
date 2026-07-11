import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useRequireAuth } from './context/AuthContext'
import { AppShell } from './components/AppShell'
import { AuthLayout } from './components/AuthLayout'
import { ProfileGate } from './components/ProfileGate'
import { LoginPage } from './pages/Login'
import { RegisterPage } from './pages/Register'
import { OnboardingPage } from './pages/Onboarding'
import { DashboardPage } from './pages/Dashboard'
import { CompanyProfilePage } from './pages/CompanyProfile'
import { EmployeesPage } from './pages/Employees'
import { ProjectsPage } from './pages/Projects'
import { ReportNewPage } from './pages/ReportNew'
import { ReportPreviewPage } from './pages/ReportPreview'
import { ReportsListPage } from './pages/ReportsList'
import { ReportDetailPage } from './pages/ReportDetail'
import { TimeAccountsPage } from './pages/TimeAccounts'
import { ProtocolModePage } from './pages/ProtocolMode'
import { ProtocolNewPage } from './pages/ProtocolNew'
import { ProtocolPreviewPage } from './pages/ProtocolPreview'
import { AdminRoute } from './components/AdminRoute'
import { FeedbackPage } from './pages/Feedback'

function ProtectedOutlet() {
  const { token, ready } = useRequireAuth()
  if (!ready) {
    return <div className="p-8 text-center text-zinc-400">Laden…</div>
  }
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <AuthLayout>
            <LoginPage />
          </AuthLayout>
        }
      />
      <Route
        path="/register"
        element={
          <AuthLayout>
            <RegisterPage />
          </AuthLayout>
        }
      />

      <Route element={<ProtectedOutlet />}>
        <Route element={<ProfileGate />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/profil" element={<CompanyProfilePage />} />
            <Route path="/mitarbeiter" element={<EmployeesPage />} />
            <Route path="/baustellen" element={<ProjectsPage />} />
            <Route path="/bericht" element={<ReportNewPage />} />
            <Route path="/bericht/vorschau" element={<ReportPreviewPage />} />
            <Route path="/protokoll" element={<ProtocolModePage />} />
            <Route path="/protokoll/neu" element={<ProtocolNewPage />} />
            <Route path="/protokoll/vorschau" element={<ProtocolPreviewPage />} />
            <Route path="/berichte" element={<ReportsListPage />} />
            <Route path="/berichte/:id" element={<ReportDetailPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/stunden" element={<TimeAccountsPage />} />
            <Route path="/verwaltung" element={<AdminRoute />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
