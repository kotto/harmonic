// ──────────────────────────────────────────────
// Dashboard Page
// ──────────────────────────────────────────────
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Users,
  Package,
  CheckCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  FileCode,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { api } from '../services/api'
import { formatDateShort, getStatusColor, getStatusLabel, getFullName, cn } from '../utils/helpers'

export function DashboardPage() {
  const { data: metrics } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: () => api.getMetricsSummary(),
    refetchInterval: 60000,
  })

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  })

  const { data: recentDoctors } = useQuery({
    queryKey: ['doctors', { page: 1, page_size: 5 }],
    queryFn: () => api.getDoctors({ page: 1, page_size: 5 }),
  })

  const { data: versions } = useQuery({
    queryKey: ['versions'],
    queryFn: () => api.getVersions(),
  })

  const statCards = [
    {
      title: 'Médecins total',
      value: metrics?.total_doctors ?? 0,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      change: `${metrics?.validated_doctors ?? 0} validés`,
      changeIcon: TrendingUp,
      link: '/doctors',
    },
    {
      title: 'En attente validation',
      value: metrics?.pending_doctors ?? 0,
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      change: 'Nécessite action',
      changeIcon: AlertTriangle,
      link: '/doctors?status=pending',
    },
    {
      title: 'Versions actives',
      value: metrics?.active_apk_versions ?? 0,
      icon: Package,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      change: `${metrics?.total_apk_versions ?? 0} versions au total`,
      changeIcon: TrendingUp,
      link: '/versions',
    },
    {
      title: 'Bundles actifs',
      value: metrics?.active_bundles ?? 0,
      icon: FileCode,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      change: `${metrics?.total_bundles ?? 0} bundles au total`,
      changeIcon: TrendingUp,
      link: '/versions',
    },
  ]

  const activeVersions = (versions || []).filter((v) => v.is_active)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tableau de bord</h1>
          <p className="text-slate-500 mt-1">Vue d'ensemble de l'administration Vital KA</p>
        </div>
        <div className="flex gap-2">
          <Link to="/doctors" className="inline-flex items-center px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors">
            <Clock className="w-4 h-4 mr-2" />
            Valider médecins
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <Link key={stat.title} to={stat.link} className="block">
            <Card variant="bordered" padding="md" className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                  <p className="mt-1 text-3xl font-bold text-slate-900">{stat.value}</p>
                  <p className="mt-2 text-sm text-slate-500 flex items-center gap-1">
                    <stat.changeIcon className="w-4 h-4" />
                    {stat.change}
                  </p>
                </div>
                <div className={cn('p-3 rounded-xl', stat.bgColor)}>
                  <stat.icon className={cn('w-6 h-6', stat.color)} />
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Doctors */}
        <Card variant="bordered" padding="none">
          <CardHeader className="px-6 py-4 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Inscriptions récentes</CardTitle>
                <CardDescription>Derniers médecins inscrits</CardDescription>
              </div>
              <Link to="/doctors" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                Voir tout
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {recentDoctors?.items?.length ? (
              <div className="divide-y divide-slate-100">
                {recentDoctors.items.map((doctor) => (
                  <Link
                    key={doctor.id}
                    to={`/doctors/${doctor.id}`}
                    className="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors"
                  >
                    <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-medium">
                      {getFullName(doctor).charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">Dr {getFullName(doctor)}</p>
                      <p className="text-sm text-slate-500 truncate">{doctor.email}</p>
                    </div>
                    <Badge variant="outline" className={cn(getStatusColor(doctor.status), 'shrink-0')}>
                      {getStatusLabel(doctor.status)}
                    </Badge>
                    <span className="text-sm text-slate-400 shrink-0">{formatDateShort(doctor.created_at)}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-500">Aucun médecin inscrit</div>
            )}
          </CardContent>
        </Card>

        {/* Active Versions */}
        <Card variant="bordered" padding="none">
          <CardHeader className="px-6 py-4 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Versions actives</CardTitle>
                <CardDescription>Versions APK distribuées par canal</CardDescription>
              </div>
              <Link to="/versions" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                Voir tout
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {activeVersions.length ? (
              <div className="divide-y divide-slate-100">
                {activeVersions.map((version) => (
                  <Link
                    key={version.id}
                    to={`/versions/${version.id}`}
                    className="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors"
                  >
                    <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-green-600">
                      <Package className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">v{version.version_name} (build {version.version_code})</p>
                      <p className="text-sm text-slate-500 flex items-center gap-2">
                        <Badge variant="outline" className={cn(getStatusColor(version.channel), 'text-xs')}>
                          {getStatusLabel(version.channel)}
                        </Badge>
                        {version.is_mandatory && (
                          <Badge variant="warning" className="text-xs">Obligatoire</Badge>
                        )}
                      </p>
                    </div>
                    <span className="text-sm text-slate-400 shrink-0">{formatDateShort(version.created_at)}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-500">Aucune version active</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <Card variant="bordered" padding="md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>État des services</CardTitle>
            <CardDescription>Surveillance en temps réel de l'infrastructure</CardDescription>
          </div>
          {health && (
            <Badge
              variant={health.status === 'healthy' ? 'success' : health.status === 'degraded' ? 'warning' : 'danger'}
              className="text-sm px-3 py-1.5"
            >
              {health.status === 'healthy' ? <CheckCircle className="w-4 h-4 mr-1" /> : <AlertTriangle className="w-4 h-4 mr-1" />}
              {getStatusLabel(health.status)}
            </Badge>
          )}
        </CardHeader>
        <CardContent>
          {health && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {health.components.map((component) => (
                <div key={component.name} className="p-4 rounded-lg bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn('w-2 h-2 rounded-full', component.status === 'healthy' ? 'bg-green-500' : 'bg-red-500')} />
                    <span className="font-medium text-slate-900 capitalize">{component.name}</span>
                  </div>
                  <p className="text-sm text-slate-500">
                    {component.latency_ms !== undefined
                      ? `${component.latency_ms}ms`
                      : component.status === 'healthy' ? 'Opérationnel' : 'Indisponible'}
                  </p>
                </div>
              ))}
              <div className="p-4 rounded-lg bg-slate-50">
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="font-medium text-slate-900">Uptime</span>
                </div>
                <p className="text-sm text-slate-500">
                  {health.uptime_seconds ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : '—'}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}