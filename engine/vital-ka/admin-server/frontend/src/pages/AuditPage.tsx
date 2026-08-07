// ──────────────────────────────────────────────
// Audit Logs Page
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Download,
  Shield,
  User,
  Settings,
  Package,
  Users,
  FileText,
  Eye,
} from 'lucide-react'
import { Table, Pagination } from '../components/ui/Table'
import { Card, CardContent } from '../components/ui/Card'

import { Select } from '../components/ui/Select'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { api } from '../services/api'
import { formatDate, cn } from '../utils/helpers'
import type { AuditLog, AuditFilters } from '../types'

const resourceOptions = [
  { value: '', label: 'Toutes les ressources' },
  { value: 'user', label: 'Utilisateurs' },
  { value: 'doctor', label: 'Médecins' },
  { value: 'apk_version', label: 'Versions APK' },
  { value: 'hologram_bundle', label: 'Bundles' },
  { value: 'system_config', label: 'Configuration' },
  { value: 'backup', label: 'Sauvegardes' },
  { value: 'auth', label: 'Authentification' },
]

const actionOptions = [
  { value: '', label: 'Toutes les actions' },
  { value: 'create', label: 'Création' },
  { value: 'read', label: 'Lecture' },
  { value: 'update', label: 'Modification' },
  { value: 'delete', label: 'Suppression' },
  { value: 'login', label: 'Connexion' },
  { value: 'logout', label: 'Déconnexion' },
  { value: 'validate', label: 'Validation' },
  { value: 'reject', label: 'Rejet' },
  { value: 'suspend', label: 'Suspension' },
  { value: 'publish', label: 'Publication' },
  { value: 'rollback', label: 'Rollback' },
  { value: 'backup', label: 'Sauvegarde' },
]

const resourceIcons: Record<string, typeof User> = {
  user: User,
  doctor: Users,
  apk_version: Package,
  system_config: Settings,
  auth: Shield,
  default: FileText,
}

export function AuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({
    page: 1,
    page_size: 20,
    action: undefined,
    resource_type: undefined,
  })
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: () => api.getAuditLogs(filters),
  })

  const handleFilterChange = (key: keyof AuditFilters, value: unknown) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }))
  }

  const getActionColor = (action: string) => {
    const colors: Record<string, string> = {
      create: 'bg-green-100 text-green-800',
      read: 'bg-blue-100 text-blue-800',
      update: 'bg-yellow-100 text-yellow-800',
      delete: 'bg-red-100 text-red-800',
      login: 'bg-green-100 text-green-800',
      logout: 'bg-slate-100 text-slate-800',
      validate: 'bg-green-100 text-green-800',
      reject: 'bg-red-100 text-red-800',
      suspend: 'bg-orange-100 text-orange-800',
      publish: 'bg-purple-100 text-purple-800',
      rollback: 'bg-orange-100 text-orange-800',
      backup: 'bg-indigo-100 text-indigo-800',
    }
    return colors[action] || 'bg-slate-100 text-slate-800'
  }

  const columns = [
    {
      key: 'timestamp',
      header: 'Horodatage',
      render: (log: AuditLog) => (
        <div>
          <p className="font-medium text-slate-900">{formatDate(log.created_at)}</p>
        </div>
      ),
    },
    {
      key: 'user',
      header: 'Utilisateur',
      render: (log: AuditLog) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-xs font-bold shrink-0">
            {(log.user_email || 'S').charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="font-medium text-slate-900 truncate max-w-[180px]">{log.user_email || 'Système'}</p>
            {log.user_role && <p className="text-xs text-slate-500">{log.user_role}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (log: AuditLog) => (
        <Badge variant="outline" className={getActionColor(log.action)}>
          {log.action}
        </Badge>
      ),
    },
    {
      key: 'resource',
      header: 'Ressource',
      render: (log: AuditLog) => {
        const Icon = resourceIcons[log.resource_type] || resourceIcons.default
        return (
          <div className="flex items-center gap-2">
            <Icon className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-slate-900">{log.resource_type}</span>
          </div>
        )
      },
    },
    {
      key: 'status',
      header: 'Résultat',
      render: (log: AuditLog) => (
        <Badge variant={log.success ? 'success' : 'danger'}>
          {log.success ? 'Succès' : 'Échec'}
        </Badge>
      ),
    },
    {
      key: 'ip',
      header: 'IP',
      render: (log: AuditLog) => log.ip_address || <span className="text-slate-400">—</span>,
    },
    {
      key: 'view',
      header: '',
      render: (log: AuditLog) => (
        <button
          onClick={() => setSelectedLog(log)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
          title="Voir les détails"
        >
          <Eye className="w-4 h-4" />
        </button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Journal d'audit</h1>
          <p className="text-slate-500 mt-1">Traçabilité de toutes les actions d'administration</p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            if (!data) return
            const blob = new Blob([JSON.stringify(data.items, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.json`
            a.click()
            URL.revokeObjectURL(url)
          }}
        >
          <Download className="w-4 h-4 mr-2" />
          Exporter
        </Button>
      </div>

      {/* Filters */}
      <Card variant="bordered" padding="md">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Select
            options={resourceOptions}
            value={filters.resource_type || ''}
            onChange={(e) => handleFilterChange('resource_type', e.target.value || undefined)}
            placeholder="Filtrer par ressource"
          />
          <Select
            options={actionOptions}
            value={filters.action || ''}
            onChange={(e) => handleFilterChange('action', e.target.value || undefined)}
            placeholder="Filtrer par action"
          />
          <Select
            options={[
              { value: '', label: 'Tous les résultats' },
              { value: 'true', label: 'Succès uniquement' },
              { value: 'false', label: 'Échecs uniquement' },
            ]}
            value={filters.success === undefined ? '' : String(filters.success)}
            onChange={(e) => handleFilterChange('success', e.target.value === '' ? undefined : e.target.value === 'true')}
            placeholder="Filtrer par résultat"
          />
        </div>
      </Card>

      {/* Audit Table */}
      <Card variant="bordered" padding="none">
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={data?.items || []}
            keyExtractor={(log) => log.id}
            isLoading={isLoading}
            emptyMessage="Aucun log d'audit trouvé"
            striped
            hoverable
          />
        </CardContent>
        {data && data.total_pages > 1 && (
          <div className="px-6 py-4 border-t border-slate-100">
            <Pagination
              currentPage={data.page}
              totalPages={data.total_pages}
              onPageChange={handlePageChange}
            />
          </div>
        )}
      </Card>

      {/* Details Modal */}
      <Modal
        isOpen={!!selectedLog}
        onClose={() => setSelectedLog(null)}
        title="Détails de l'événement"
        size="lg"
      >
        {selectedLog && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 uppercase font-medium">Horodatage</p>
                <p className="font-medium mt-1">{formatDate(selectedLog.created_at)}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 uppercase font-medium">Action</p>
                <Badge variant="outline" className={cn('mt-1', getActionColor(selectedLog.action))}>
                  {selectedLog.action}
                </Badge>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 uppercase font-medium">Ressource</p>
                <p className="font-medium mt-1">{selectedLog.resource_type}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 uppercase font-medium">ID Ressource</p>
                <code className="text-sm text-slate-700">{selectedLog.resource_id || '—'}</code>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 uppercase font-medium">Utilisateur</p>
                <p className="font-medium mt-1">{selectedLog.user_email || 'Système'}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 uppercase font-medium">Adresse IP</p>
                <p className="font-mono font-medium mt-1">{selectedLog.ip_address || '—'}</p>
              </div>
            </div>

            {selectedLog.new_values && Object.keys(selectedLog.new_values).length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Nouvelles valeurs</p>
                <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 overflow-x-auto text-xs">
                  {JSON.stringify(selectedLog.new_values, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.old_values && Object.keys(selectedLog.old_values).length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Anciennes valeurs</p>
                <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 overflow-x-auto text-xs">
                  {JSON.stringify(selectedLog.old_values, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Métadonnées</p>
                <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 overflow-x-auto text-xs">
                  {JSON.stringify(selectedLog.metadata, null, 2)}
                </pre>
              </div>
            )}

            {!selectedLog.success && selectedLog.error_message && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800 mb-1">Erreur</p>
                <p className="text-sm text-red-700">{selectedLog.error_message}</p>
              </div>
            )}

            {selectedLog.user_agent && (
              <div>
                <p className="text-sm font-medium text-slate-700 mb-1">User-Agent</p>
                <p className="text-sm text-slate-500 break-all">{selectedLog.user_agent}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}