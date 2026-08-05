// ──────────────────────────────────────────────
// App - Routing Principal
// ──────────────────────────────────────────────
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { MainLayout } from './components/layout/Layout'
import { LoginPage } from './pages/LoginPage'
import { ForgotPasswordPage, ResetPasswordPage } from './pages/PasswordPages'
import { DashboardPage } from './pages/DashboardPage'
import { DoctorsPage } from './pages/DoctorsPage'
import { DoctorDetailPage } from './pages/DoctorDetailPage'
import { VersionsPage } from './pages/VersionsPage'
import { VersionDetailPage } from './pages/VersionDetailPage'
import { SystemPage } from './pages/SystemPage'
import { AuditPage } from './pages/AuditPage'
import { MetricsPage } from './pages/MetricsPage'
import { ProfilePage } from './pages/ProfilePage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

function RequireRole({ roles, children }: { roles: string[]; children: React.ReactNode }) {
  const { user } = useAuth()

  if (!user || !roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <MainLayout>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <DashboardPage />
            </RequireAuth>
          }
        />
        <Route
          path="/doctors"
          element={
            <RequireAuth>
              <RequireRole roles={['admin', 'validator']}>
                <DoctorsPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/doctors/:id"
          element={
            <RequireAuth>
              <RequireRole roles={['admin', 'validator']}>
                <DoctorDetailPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/versions"
          element={
            <RequireAuth>
              <RequireRole roles={['admin']}>
                <VersionsPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/versions/:id"
          element={
            <RequireAuth>
              <RequireRole roles={['admin']}>
                <VersionDetailPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/system"
          element={
            <RequireAuth>
              <RequireRole roles={['admin']}>
                <SystemPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/audit"
          element={
            <RequireAuth>
              <RequireRole roles={['admin']}>
                <AuditPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/metrics"
          element={
            <RequireAuth>
              <RequireRole roles={['admin']}>
                <MetricsPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <ProfilePage />
            </RequireAuth>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MainLayout>
  )
}

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}