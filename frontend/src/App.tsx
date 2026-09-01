import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useRequireAuth } from './context/AuthContext'
import { AppShell } from './components/AppShell'
import { AuthLayout } from './components/AuthLayout'
import { ProfileGate } from './components/ProfileGate'
import { RequirePermission } from './components/RequirePermission'
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
import { ProtocolsListPage } from './pages/ProtocolsList'
import { ProtocolDetailPage } from './pages/ProtocolDetail'
import { ProtocolSeriesPage } from './pages/ProtocolSeries'
import { AdminRoute } from './components/AdminRoute'
import { FeedbackPage } from './pages/Feedback'
import { DeliveryNoteScanPage } from './pages/DeliveryNoteScan'

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
            <Route
              path="/profil"
              element={
                <RequirePermission permission="company_profile">
                  <CompanyProfilePage />
                </RequirePermission>
              }
            />
            <Route
              path="/mitarbeiter"
              element={
                <RequirePermission permission="employees">
                  <EmployeesPage />
                </RequirePermission>
              }
            />
            <Route
              path="/baustellen"
              element={
                <RequirePermission permission="projects">
                  <ProjectsPage />
                </RequirePermission>
              }
            />
            <Route path="/bericht" element={<ReportNewPage />} />
            <Route path="/bericht/vorschau" element={<ReportPreviewPage />} />
            <Route path="/protokoll" element={<ProtocolModePage />} />
            <Route path="/protokoll/neu" element={<ProtocolNewPage />} />
            <Route path="/protokoll/vorschau" element={<ProtocolPreviewPage />} />
            <Route path="/protokolle" element={<ProtocolsListPage />} />
            <Route path="/protokolle/baustelle/:projectId" element={<ProtocolSeriesPage />} />
            <Route path="/protokolle/:id" element={<ProtocolDetailPage />} />
            <Route
              path="/lieferschein"
              element={
                <RequirePermission permission="delivery_notes">
                  <DeliveryNoteScanPage />
                </RequirePermission>
              }
            />
            <Route
              path="/berichte"
              element={
                <RequirePermission permission="reports_list">
                  <ReportsListPage />
                </RequirePermission>
              }
            />
            <Route
              path="/berichte/:id"
              element={
                <RequirePermission permission="report">
                  <ReportDetailPage />
                </RequirePermission>
              }
            />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route
              path="/stunden"
              element={
                <RequirePermission permission="time_accounts">
                  <TimeAccountsPage />
                </RequirePermission>
              }
            />
            <Route path="/verwaltung" element={<AdminRoute />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
