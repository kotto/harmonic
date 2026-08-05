// ──────────────────────────────────────────────
// Metrics Page (Résumé opérationnel)
// ──────────────────────────────────────────────
import { useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  RefreshCw,
  Users,
  Package,
  FileCode,
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { api } from '../services/api'
import { cn } from '../utils/helpers'

export function MetricsPage() {
  const { data: metrics, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: () => api.getMetricsSummary(),
    refetchInterval: 60000,
  })

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  })

  const formatUptime = (seconds?: number): string => {
    if (!seconds) return '—'
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (days > 0) return `${days}j ${hours}h ${minutes}m`
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  const metricCards = [
    {
      title: 'Médecins inscrits',
      value: metrics?.total_doctors ?? '—',
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      sub: `${metrics?.validated_doctors ?? 0} validés · ${metrics?.pending_doctors ?? 0} en attente · ${metrics?.rejected_doctors ?? 0} rejetés`,
    },
    {
      title: 'Versions APK',
      value: metrics?.total_apk_versions ?? '—',
      icon: Package,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      sub: `${metrics?.active_apk_versions ?? 0} versions actives`,
    },
    {
      title: 'Bundles hologrammes',
      value: metrics?.total_bundles ?? '—',
      icon: FileCode,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      sub: `${metrics?.active_bundles ?? 0} bundles actifs`,
    },
    {
      title: 'Uptime API',
      value: formatUptime(metrics?.uptime_seconds),
      icon: Clock,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
      sub: 'Depuis le démarrage du service',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Métriques système</h1>
          <p className="text-slate-500 mt-1">Indicateurs opérationnels de la plateforme Vital KA</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} isLoading={isFetching}>
          <RefreshCw className={cn('w-4 h-4 mr-2', isFetching && 'animate-spin')} />
          Actualiser
        </Button>
      </div>

      {isLoading ? (
        <div className="min-h-[40vh] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      ) : (
        <>
          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {metricCards.map((metric) => (
              <Card key={metric.title} variant="bordered" padding="md">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-500">{metric.title}</p>
                    <p className="mt-1 text-3xl font-bold text-slate-900">{metric.value}</p>
                    <p className="mt-2 text-xs text-slate-500">{metric.sub}</p>
                  </div>
                  <div className={cn('p-3 rounded-xl', metric.bgColor)}>
                    <metric.icon className={cn('w-5 h-5', metric.color)} />
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Health Detail */}
          <Card variant="bordered">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-primary-600" />
                  État des services
                </CardTitle>
                <CardDescription>Latence et disponibilité des composants</CardDescription>
              </div>
              {health && (
                <Badge
                  variant={health.status === 'healthy' ? 'success' : health.status === 'degraded' ? 'warning' : 'danger'}
                  className="text-sm px-3 py-1.5"
                >
                  {health.status === 'healthy' ? (
                    <CheckCircle className="w-4 h-4 mr-1" />
                  ) : (
                    <XCircle className="w-4 h-4 mr-1" />
                  )}
                  {health.status}
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              {health?.components.length ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {health.components.map((component) => (
                    <div key={component.name} className="p-4 rounded-lg bg-slate-50">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={cn(
                          'w-2.5 h-2.5 rounded-full',
                          component.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                        )} />
                        <span className="font-medium text-slate-900 capitalize">{component.name}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <Badge variant={component.status === 'healthy' ? 'success' : 'danger'} className="text-xs">
                          {component.status}
                        </Badge>
                        {component.latency_ms !== undefined && (
                          <span className="text-xs text-slate-500">{component.latency_ms}ms</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">Aucune donnée de santé disponible</div>
              )}
            </CardContent>
          </Card>

          {/* Note sur les métriques détaillées */}
          <Card variant="bordered">
            <CardContent>
              <div className="p-4 rounded-lg bg-primary-50 border border-primary-100 flex items-start gap-3">
                <BarChart3 className="w-5 h-5 text-primary-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-900">Métriques détaillées Prometheus</p>
                  <p className="text-sm text-slate-600 mt-1">
                    Le endpoint <code className="font-mono text-xs bg-slate-100 rounded px-1 py-0.5">GET /admin/health</code> expose l'état
                    en temps réel des composants. Les métriques complètes sont collectées par Prometheus
                    et visualisables dans Grafana (voir docker-compose, port 3000).
                  </p>
                  <div className="mt-3 flex gap-3 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" /> Médecins
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Package className="w-3.5 h-3.5" /> Versions APK
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <FileCode className="w-3.5 h-3.5" /> Bundles
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}