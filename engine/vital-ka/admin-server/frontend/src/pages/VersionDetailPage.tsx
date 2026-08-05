// ──────────────────────────────────────────────
// Version Detail Page (Publish, Rollback, Webhooks)
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Package,
  Rocket,
  ArrowDownToLine,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Copy,
  Check,
  Loader2,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { Modal, ConfirmDialog } from '../components/ui/Modal'
import { api } from '../services/api'
import { formatDate, formatFileSize, getStatusColor, getStatusLabel } from '../utils/helpers'
import type { WebhookLog } from '../types'

export function VersionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [copied, setCopied] = useState(false)
  const [showRollbackModal, setShowRollbackModal] = useState(false)
  const [rollbackTarget, setRollbackTarget] = useState('')
  const [showPublishConfirm, setShowPublishConfirm] = useState(false)

  const { data: version, isLoading } = useQuery({
    queryKey: ['version', id],
    queryFn: () => api.getVersion(id!),
    enabled: !!id,
  })

  const { data: versionsList } = useQuery({
    queryKey: ['versions'],
    queryFn: () => api.getVersions(),
  })

  const { data: webhookLogs } = useQuery({
    queryKey: ['webhook-logs'],
    queryFn: () => api.getWebhookLogs(),
  })

  const publishMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => api.publishVersion(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version', id] })
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      setShowPublishConfirm(false)
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: (targetVersionCode: number) => api.rollbackVersion(targetVersionCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version', id] })
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      setShowRollbackModal(false)
      setRollbackTarget('')
    },
  })

  const retryWebhookMutation = useMutation({
    mutationFn: (logId: string) => api.retryWebhook(logId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhook-logs'] })
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!version) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
        <AlertTriangle className="w-12 h-12 text-slate-300" />
        <p className="text-slate-500">Version introuvable</p>
        <Link to="/versions">
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour aux versions
          </Button>
        </Link>
      </div>
    )
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(`vitalka://update?channel=${version.channel}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard non disponible
    }
  }

  const webhookStatusIcon = (status: WebhookLog['status']) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'failed': return <XCircle className="w-4 h-4 text-red-600" />
      default: return <Clock className="w-4 h-4 text-yellow-600" />
    }
  }

  const rollbackOptions = (versionsList || [])
    .filter((v) => v.id !== version.id && !v.is_active)
    .map((v) => ({
      value: String(v.version_code),
      label: `v${v.version_name} (build ${v.version_code}) — ${getStatusLabel(v.channel)}`,
    }))

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/versions" className="hover:text-primary-600">Versions</Link>
        <span>/</span>
        <span className="text-slate-900 font-medium">v{version.version_name}</span>
      </div>

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-primary-100 flex items-center justify-center text-primary-600">
            <Package className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">v{version.version_name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className={getStatusColor(version.channel)}>
                Canal {getStatusLabel(version.channel)}
              </Badge>
              <Badge variant={version.is_active ? 'success' : 'outline'}>
                {version.is_active ? 'Active' : 'Inactive'}
              </Badge>
              {version.is_mandatory && <Badge variant="warning">Obligatoire</Badge>}
              <span className="text-sm text-slate-500">Build {version.version_code}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={handleCopy}>
            {copied ? (
              <>
                <Check className="w-4 h-4 mr-2 text-green-600" />
                Copié !
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 mr-2" />
                Lien de distribution
              </>
            )}
          </Button>
          {!version.is_active ? (
            <Button onClick={() => setShowPublishConfirm(true)} isLoading={publishMutation.isPending}>
              <Rocket className="w-4 h-4 mr-2" />
              Publier
            </Button>
          ) : (
            <Button variant="danger" onClick={() => setShowPublishConfirm(true)} isLoading={publishMutation.isPending}>
              <ArrowDownToLine className="w-4 h-4 mr-2" />
              Dépublier
            </Button>
          )}
          <Button variant="warning" onClick={() => setShowRollbackModal(true)}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Rollback
          </Button>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card variant="bordered">
          <CardHeader>
            <CardTitle>Informations</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <dt className="text-slate-500">Version</dt>
                <dd className="font-medium">v{version.version_name} (build {version.version_code})</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <dt className="text-slate-500">Taille APK</dt>
                <dd className="font-medium">{formatFileSize(version.apk_file_size)}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <dt className="text-slate-500">SHA-256</dt>
                <dd className="font-mono text-xs max-w-[55%] break-all">{version.apk_sha256}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <dt className="text-slate-500">Version minimale</dt>
                <dd className="font-medium">{version.min_app_version || '—'}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <dt className="text-slate-500">Créée le</dt>
                <dd className="font-medium">{formatDate(version.created_at)}</dd>
              </div>
              {version.published_at && (
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <dt className="text-slate-500">Publiée le</dt>
                  <dd className="font-medium">{formatDate(version.published_at)}</dd>
                </div>
              )}
              {version.git_commit && (
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <dt className="text-slate-500">Commit</dt>
                  <dd className="font-mono text-xs">{version.git_commit.slice(0, 12)}{version.git_branch ? ` (${version.git_branch})` : ''}</dd>
                </div>
              )}
              <div className="flex justify-between py-1">
                <dt className="text-slate-500">Fichier</dt>
                <dd className="font-medium">{version.apk_file_path}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card variant="bordered">
          <CardHeader>
            <CardTitle>Changelog</CardTitle>
          </CardHeader>
          <CardContent>
            {version.changelog ? (
              <pre className="whitespace-pre-wrap text-sm text-slate-700 bg-slate-50 rounded-lg p-4">{version.changelog}</pre>
            ) : version.release_notes ? (
              <pre className="whitespace-pre-wrap text-sm text-slate-700 bg-slate-50 rounded-lg p-4">{version.release_notes}</pre>
            ) : (
              <p className="text-sm text-slate-500">Aucun changelog fourni</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Webhook Logs */}
      <Card variant="bordered">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Notifications webhooks</CardTitle>
            <CardDescription>Livraison des notifications de mise à jour</CardDescription>
          </div>
          <Badge variant="info">{webhookLogs?.length || 0} tentatives</Badge>
        </CardHeader>
        <CardContent>
          {webhookLogs?.length ? (
            <div className="divide-y divide-slate-100">
              {webhookLogs.map((log) => (
                <div key={log.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    {webhookStatusIcon(log.status)}
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{log.webhook_url}</p>
                      <p className="text-xs text-slate-500">
                        {log.event_type} · {log.attempts} tentative(s)
                        {log.response_status && ` · HTTP ${log.response_status}`}
                        {log.last_attempt_at && ` · ${formatDate(log.last_attempt_at)}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className={getStatusColor(log.status)}>
                      {getStatusLabel(log.status)}
                    </Badge>
                    {log.status === 'failed' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => retryWebhookMutation.mutate(log.id)}
                        isLoading={retryWebhookMutation.isPending}
                        className="text-primary-600"
                        title="Réessayer"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">Aucune notification webhook envoyée</div>
          )}
        </CardContent>
      </Card>

      {/* Publish Confirm */}
      <ConfirmDialog
        isOpen={showPublishConfirm}
        onClose={() => setShowPublishConfirm(false)}
        onConfirm={() => publishMutation.mutate({ id: version.id, isActive: !version.is_active })}
        title={version.is_active ? 'Dépublier la version' : 'Publier la version'}
        message={version.is_active
          ? 'Dépublier cette version ? Les appareils ne recevront plus cette mise à jour.'
          : 'Publier cette version ? Elle sera proposée aux appareils sur le canal ' + getStatusLabel(version.channel) + '.'
        }
        confirmText={version.is_active ? 'Dépublier' : 'Publier'}
        variant={version.is_active ? 'warning' : 'primary'}
        isLoading={publishMutation.isPending}
      />

      {/* Rollback Modal */}
      <Modal
        isOpen={showRollbackModal}
        onClose={() => setShowRollbackModal(false)}
        title="Rollback de version"
        description="Revenir à une version précédente inactive"
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Version cible (build code)
            </label>
            <Select
              options={rollbackOptions}
              value={rollbackTarget}
              onChange={(e) => setRollbackTarget(e.target.value)}
              placeholder={rollbackOptions.length > 0 ? 'Sélectionner la version cible' : 'Aucune version inactive disponible'}
              disabled={rollbackOptions.length === 0}
            />
            <p className="mt-1.5 text-xs text-slate-500">
              La version cible sera publiée comme active. La version actuelle sera désactivée.
            </p>
          </div>

          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600 shrink-0 mt-0.5" />
            <p className="text-sm text-yellow-800">
              Le rollback est immédiat. Les appareils qui effectuent une vérification de mise à jour seront dirigés vers la version cible.
            </p>
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowRollbackModal(false)} disabled={rollbackMutation.isPending}>
              Annuler
            </Button>
            <Button
              variant="warning"
              onClick={() => rollbackMutation.mutate(Number(rollbackTarget))}
              isLoading={rollbackMutation.isPending}
              disabled={!rollbackTarget}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Effectuer le rollback
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}