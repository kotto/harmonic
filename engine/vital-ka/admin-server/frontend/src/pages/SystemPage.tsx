// ──────────────────────────────────────────────
// System Page (Health, Config, Backups)
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Server,
  Database,
  Cpu,
  HardDrive,
  Activity,
  RefreshCw,
  Save,
  Eye,
  EyeOff,
  Plus,
  Settings2,
  CheckCircle,
  Loader2,
  AlertTriangle,
  Mail,
  Box,
  Layers,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Modal, ConfirmDialog } from '../components/ui/Modal'
import { Input } from '../components/ui/Input'
import { api } from '../services/api'
import { formatDate, formatFileSize, getStatusColor, getStatusLabel, cn } from '../utils/helpers'
import type { SystemConfig } from '../types'

const serviceIcons: Record<string, typeof Server> = {
  database: Database,
  postgres: Database,
  redis: Layers,
  minio: Box,
  api: Server,
  worker: Cpu,
  celery: Cpu,
  smtp: Mail,
  default: Server,
}

// Conversion string <-> valeur JSON pour l'édition
function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}

function parseValue(raw: string): unknown {
  const trimmed = raw.trim()
  if (trimmed === '') return ''
  try {
    return JSON.parse(trimmed)
  } catch {
    return trimmed // garder comme chaîne si pas JSON valide
  }
}

export function SystemPage() {
  const queryClient = useQueryClient()
  const [showSecretKeys, setShowSecretKeys] = useState<Set<string>>(new Set())
  const [editingConfig, setEditingConfig] = useState<SystemConfig | null>(null)
  const [editValue, setEditValue] = useState('')
  const [showBackupConfirm, setShowBackupConfirm] = useState(false)
  const [showNewConfigModal, setShowNewConfigModal] = useState(false)
  const [newConfig, setNewConfig] = useState({ key: '', value: '', description: '', is_sensitive: false })

  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  })

  const { data: configs, isLoading: configsLoading } = useQuery({
    queryKey: ['configs'],
    queryFn: () => api.getConfigs(),
  })

  const { data: backups, isLoading: backupsLoading } = useQuery({
    queryKey: ['backups'],
    queryFn: () => api.getBackups(),
  })

  const updateConfigMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => api.updateConfig(key, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configs'] })
      setEditingConfig(null)
      setEditValue('')
    },
  })

  const createBackupMutation = useMutation({
    mutationFn: () => api.createBackup(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] })
      setShowBackupConfirm(false)
    },
  })

  const toggleSecret = (key: string) => {
    setShowSecretKeys((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const handleSaveConfig = () => {
    if (!editingConfig) return
    updateConfigMutation.mutate({ key: editingConfig.key, value: parseValue(editValue) })
  }

  const handleCreateConfig = async () => {
    if (!newConfig.key || !newConfig.value) return
    try {
      await api.updateConfig(newConfig.key, parseValue(newConfig.value))
      queryClient.invalidateQueries({ queryKey: ['configs'] })
      setShowNewConfigModal(false)
      setNewConfig({ key: '', value: '', description: '', is_sensitive: false })
    } catch (error) {
      console.error('Create config failed:', error)
    }
  }

  const renderServiceStatus = () => {
    if (!health) return null
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {health.components.map((component) => {
          const Icon = serviceIcons[component.name] || serviceIcons.default
          return (
            <div
              key={component.name}
              className={cn(
                'p-4 rounded-xl border transition-colors',
                component.status === 'healthy'
                  ? 'border-green-200 bg-green-50/50'
                  : 'border-red-200 bg-red-50/50'
              )}
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-10 h-10 rounded-lg flex items-center justify-center',
                  component.status === 'healthy' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                )}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-slate-900 capitalize truncate">{component.name}</p>
                  <p className="text-xs text-slate-500 truncate">Service</p>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <Badge variant="outline" className={getStatusColor(component.status)}>
                  {getStatusLabel(component.status)}
                </Badge>
                {component.latency_ms !== undefined && (
                  <span className="text-xs text-slate-500">{component.latency_ms}ms</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Administration système</h1>
          <p className="text-slate-500 mt-1">Santé, configuration et sauvegardes de l'infrastructure</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetchHealth()} disabled={healthLoading}>
            <RefreshCw className={cn('w-4 h-4 mr-2', healthLoading && 'animate-spin')} />
            Actualiser
          </Button>
          <Button onClick={() => setShowBackupConfirm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Sauvegarde
          </Button>
        </div>
      </div>

      {/* System Health */}
      <Card variant="bordered">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" />
              État du système
            </CardTitle>
            <CardDescription>Dernière vérification : {health ? formatDate(health.timestamp) : '...'}</CardDescription>
          </div>
          {health && (
            <Badge
              variant={health.status === 'healthy' ? 'success' : health.status === 'degraded' ? 'warning' : 'danger'}
              className="text-sm px-3 py-1.5"
            >
              {health.status === 'healthy' ? (
                <CheckCircle className="w-4 h-4 mr-1" />
              ) : (
                <AlertTriangle className="w-4 h-4 mr-1" />
              )}
              {getStatusLabel(health.status)} · API v{health.version}
            </Badge>
          )}
        </CardHeader>
        <CardContent>{renderServiceStatus()}</CardContent>
      </Card>

      {/* Configuration */}
      <Card variant="bordered">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-primary-600" />
              Configuration système
            </CardTitle>
            <CardDescription>Paramètres de l'application modifiables à chaud</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => setShowNewConfigModal(true)}>
            <Plus className="w-4 h-4 mr-1" />
            Nouvelle clé
          </Button>
        </CardHeader>
        <CardContent>
          {configsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
            </div>
          ) : configs?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Clé</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Valeur</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Catégorie</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {configs.map((config) => {
                    const isVisible = showSecretKeys.has(config.key)
                    const valueStr = stringifyValue(config.value)
                    return (
                      <tr key={config.key} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <code className="font-mono text-xs text-primary-700 bg-primary-50 rounded px-2 py-0.5">{config.key}</code>
                            {config.is_sensitive && (
                              <Badge variant="warning" className="text-[10px] px-1.5">Secret</Badge>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm text-slate-700 max-w-[200px] truncate">
                              {config.is_sensitive && !isVisible ? '••••••••••••' : valueStr}
                            </span>
                            {config.is_sensitive && (
                              <button
                                onClick={() => toggleSecret(config.key)}
                                className="text-slate-400 hover:text-slate-600 shrink-0"
                                title={isVisible ? 'Masquer' : 'Afficher'}
                              >
                                {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className="text-xs">{config.category}</Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-500">{config.description || '—'}</td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingConfig(config)
                              setEditValue(valueStr)
                            }}
                          >
                            Modifier
                          </Button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-slate-500 mb-4">Aucune configuration en base. Initialisez les valeurs par défaut.</p>
              <Button onClick={() => api.initDefaultConfigs().then(() => queryClient.invalidateQueries({ queryKey: ['configs'] }))}>
                Initialiser les configs par défaut
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backups */}
      <Card variant="bordered">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-primary-600" />
            Sauvegardes
          </CardTitle>
          <CardDescription>Historique des sauvegardes de la base de données et des fichiers</CardDescription>
        </CardHeader>
        <CardContent>
          {backupsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
            </div>
          ) : backups?.length ? (
            <div className="divide-y divide-slate-100">
              {backups.map((backup) => (
                <div key={backup.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500">
                      <HardDrive className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{backup.name || backup.id}</p>
                      <p className="text-xs text-slate-500">
                        {formatDate(backup.started_at)} · {backup.size_bytes !== undefined && backup.size_bytes !== null
                          ? formatFileSize(backup.size_bytes)
                          : 'en cours...'}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className={getStatusColor(backup.status)}>
                    {backup.status === 'completed' ? 'Terminée' : backup.status === 'running' ? 'En cours' : backup.status === 'failed' ? 'Échec' : 'En attente'}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">Aucune sauvegarde disponible</div>
          )}
        </CardContent>
      </Card>

      {/* Edit Config Modal */}
      <Modal
        isOpen={!!editingConfig}
        onClose={() => {
          setEditingConfig(null)
          setEditValue('')
        }}
        title="Modifier la configuration"
        description={editingConfig?.description}
        size="md"
      >
        {editingConfig && (
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-slate-700 mb-1.5">Clé</p>
              <code className="font-mono text-sm text-primary-700 bg-primary-50 rounded px-2 py-1">{editingConfig.key}</code>
            </div>
            <div>
              <label htmlFor="config-value" className="block text-sm font-medium text-slate-700 mb-1.5">
                Valeur
              </label>
              <Input
                id="config-value"
                type={editingConfig.is_sensitive && !showSecretKeys.has(editingConfig.key) ? 'password' : 'text'}
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                hint={editingConfig.is_sensitive ? 'Valeur sensible — ne la divulguez pas. Utilisez du JSON pour les objets.' : 'Utilisez du JSON pour les valeurs non-chaîne (ex: {"enabled": true}).'}
              />
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setEditingConfig(null)}>
                Annuler
              </Button>
              <Button
                onClick={handleSaveConfig}
                isLoading={updateConfigMutation.isPending}
                disabled={!editValue}
              >
                <Save className="w-4 h-4 mr-2" />
                Enregistrer
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* New Config Modal */}
      <Modal
        isOpen={showNewConfigModal}
        onClose={() => setShowNewConfigModal(false)}
        title="Nouvelle clé de configuration"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Clé"
            placeholder="app.maintenance_mode"
            value={newConfig.key}
            onChange={(e) => setNewConfig({ ...newConfig, key: e.target.value })}
          />
          <Input
            label="Valeur"
            placeholder="false"
            value={newConfig.value}
            onChange={(e) => setNewConfig({ ...newConfig, value: e.target.value })}
          />
          <Input
            label="Description"
            placeholder="Description de la clé..."
            value={newConfig.description}
            onChange={(e) => setNewConfig({ ...newConfig, description: e.target.value })}
          />
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={newConfig.is_sensitive}
              onChange={(e) => setNewConfig({ ...newConfig, is_sensitive: e.target.checked })}
              className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-700">Valeur sensible (masquée par défaut)</span>
          </label>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowNewConfigModal(false)}>
              Annuler
            </Button>
            <Button onClick={handleCreateConfig} disabled={!newConfig.key || !newConfig.value}>
              <Plus className="w-4 h-4 mr-2" />
              Créer
            </Button>
          </div>
        </div>
      </Modal>

      {/* Backup Confirm */}
      <ConfirmDialog
        isOpen={showBackupConfirm}
        onClose={() => setShowBackupConfirm(false)}
        onConfirm={() => createBackupMutation.mutate()}
        title="Créer une sauvegarde"
        message="Lancer une sauvegarde complète de la base de données et des fichiers ? Cette opération peut prendre plusieurs minutes."
        confirmText="Lancer la sauvegarde"
        variant="primary"
        isLoading={createBackupMutation.isPending}
      />
    </div>
  )
}