// ──────────────────────────────────────────────
// Layout Components
// ──────────────────────────────────────────────
import { ReactNode, useState } from 'react'
import { Link, useLocation, NavLink } from 'react-router-dom'
import { cn, getFullName, getInitials, getRoleLabel, getRoleColor } from '../../utils/helpers'
import {
  LayoutDashboard,
  Users,
  Package,
  Settings,
  BarChart3,
  LogOut,
  Menu,
  X,
  User,
  Shield,
  Database,
  Bell,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../services/api'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const navigation = [
  { name: 'Tableau de bord', href: '/', icon: LayoutDashboard, roles: ['admin', 'validator'] },
  { name: 'Médecins', href: '/doctors', icon: Users, roles: ['admin', 'validator'] },
  { name: 'Versions', href: '/versions', icon: Package, roles: ['admin'] },
  { name: 'Système', href: '/system', icon: Settings, roles: ['admin'] },
  { name: 'Audit', href: '/audit', icon: Database, roles: ['admin'] },
  { name: 'Métriques', href: '/metrics', icon: BarChart3, roles: ['admin'] },
]

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth()
  const location = useLocation()

  const filteredNav = navigation.filter((item) => item.roles.includes(user?.role || ''))

  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 transform transition-transform duration-300 ease-in-out flex flex-col',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        aria-label="Navigation principale"
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-slate-200">
          <Link to="/" className="flex items-center gap-2" onClick={onClose}>
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-slate-900">Vital KA</span>
          </Link>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            aria-label="Fermer le menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto" role="navigation">
          {filteredNav.map((item) => {
            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
            const Icon = item.icon
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {item.name}
              </NavLink>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-200">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-sm font-bold">
              {getInitials(user)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{getFullName(user)}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
            <span className={cn('px-2 py-0.5 text-xs font-medium rounded-full', getRoleColor(user?.role || ''))}>
              {getRoleLabel(user?.role || '')}
            </span>
          </div>
          <div className="mt-3 flex flex-col gap-1">
            <Link
              to="/profile"
              className="flex items-center gap-3 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
              onClick={onClose}
            >
              <User className="w-5 h-5" />
              Profil
            </Link>
            <button
              onClick={async () => {
                await api.logoutApi()
                onClose()
              }}
              className="flex items-center gap-3 px-3 py-2 text-sm text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors text-left w-full"
            >
              <LogOut className="w-5 h-5" />
              Déconnexion
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user } = useAuth()
  const [notificationsOpen, setNotificationsOpen] = useState(false)

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/95 backdrop-blur-sm border-b border-slate-200 lg:ml-64">
      <div className="h-full px-4 lg:px-6 flex items-center justify-between gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          aria-label="Ouvrir le menu"
        >
          <Menu className="w-6 h-6" />
        </button>

        <div className="flex-1 lg:flex-none" />

        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 relative"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50">
                <p className="px-4 py-2 text-sm font-medium text-slate-900 border-b border-slate-100">Notifications</p>
                <p className="px-4 py-4 text-sm text-slate-500 text-center">Aucune notification</p>
              </div>
            )}
          </div>

          <div className="hidden sm:flex items-center gap-2 pl-4 border-l border-slate-200">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-xs font-bold">
              {getInitials(user)}
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-900">{getFullName(user)}</p>
              <p className="text-xs text-slate-500">{getRoleLabel(user?.role || '')}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0 lg:ml-64">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 lg:p-6 overflow-auto">{children}</main>
      </div>
    </div>
  )
}