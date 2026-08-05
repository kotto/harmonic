// ──────────────────────────────────────────────
// Versions Page (APK & Bundles Management)
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Package,
  Upload,
  Rocket,
  ArrowUp,
  Copy,
  Check,
  Trash2,
  AlertTriangle,
  FileCode,
} from 'lucide-react'
import { Table } from '../components/ui/Table'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Modal, ConfirmDialog } from '../components/ui/Modal'
import { FileUpload } from '../components/ui/FileUpload'
import { api } from '../services/api'
import { formatDate, formatFileSize, getStatusColor, getStatusLabel } from '../utils/helpers'
import type { APKVersionListResponse, ReleaseChannel } from '../types'

const channelOptions: Array<{ value: '' | ReleaseChannel; label: string }> = [
  { value: '', label: 'Tous les canaux' },
  { value: 'alpha', label: 'Alpha' },
  { value: 'beta', label: 'Bêta' },
  { value: 'stable', label: 'Stable' },
]

export function VersionsPage() {
  const queryClient = useQueryClient()
  const [channel, setChannel] = useState<'' | ReleaseChannel>('')
  const [search, setSearch] = useState('')
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showUploadBundleModal, setShowUploadBundleModal] = useState(false)
  const [showPublishConfirm, setShowPublishConfirm] = useState<APKVersionListResponse | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<APKVersionListResponse | null>(null)
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null)

  const { data: versions, isLoading } = useQuery({
    queryKey: ['versions'],
    queryFn: () => api.getVersions(),
  })

  const { data: bundles } = useQuery({
    queryKey: ['bundles'],
    queryFn: () => api.getBundles(),
  })

  const publishMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => api.publishVersion(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      setShowPublishConfirm(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteVersion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      setShowDeleteConfirm(null)
    },
  })

  const filteredVersions = (versions || []).filter((v) => {
    const matchesChannel = !channel || v.channel === channel
    const matchesSearch =
      !search ||
      v.version_name.toLowerCase().includes(search.toLowerCase()) ||
      String(v.version_code).includes(search)
    return matchesChannel && matchesSearch
  })

  const handleCopyUrl = async (version: APKVersionListResponse) => {
    try {
      const latest = await api.getLatestVersion(version.channel)
      if (latest && latest.id === version.id) {
        await navigator.clipboard.writeText(`vitalka://update?channel=${version.channel}`)
        setCopiedUrl(version.id)
        setTimeout(() => setCopiedUrl(null), 2000)
      }
    } catch {
      // ignore — lien de canal indisponible
    }
  }

  const columns = [
    {
      key: 'version',
      header: 'Version',
      render: (v: APKVersionListResponse) => (
        <Link to={`/versions/${v.id}`} className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center text-primary-600">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <p className="font-medium text-slate-900">v{v.version_name}</p>
            <p className="text-sm text-slate-500">Build {v.version_code}</p>
          </div>
        </Link>
      ),
    },
    {
      key: 'channel',
      header: 'Canal',
      render: (v: APKVersionListResponse) => (
        <Badge variant="outline" className={getStatusColor(v.channel)}>
          {getStatusLabel(v.channel)}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (v: APKVersionListResponse) => (
        <div className="flex items-center gap-2">
          <Badge variant={v.is_active ? 'success' : 'outline'}>
            {v.is_active ? 'Active' : 'Inactive'}
          </Badge>
          {v.is_mandatory && <Badge variant="warning">Obligatoire</Badge>}
        </div>
      ),
    },
    {
      key: 'size',
      header: 'Taille',
      render: (v: APKVersionListResponse) => formatFileSize(v.apk_file_size),
    },
    {
      key: 'published_at',
      header: 'Publication',
      render: (v: APKVersionListResponse) => v.published_at ? formatDate(v.published_at) : <span className="text-slate-400">—</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (v: APKVersionListResponse) => (
        <div className="flex items-center gap-1">
          <button
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="Copier le lien de distribution"
            onClick={() => handleCopyUrl(v)}
          >
            {copiedUrl === v.id ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
          </button>
          {!v.is_active ? (
            <button
              className="p-1.5 rounded-lg text-green-600 hover:bg-green-50 transition-colors"
              title="Publier cette version"
              onClick={() => setShowPublishConfirm(v)}
            >
              <Rocket className="w-4 h-4" />
            </button>
          ) : (
            <button
              className="p-1.5 rounded-lg text-yellow-600 hover:bg-yellow-50 transition-colors"
              title="Dépublier"
              onClick={() => setShowPublishConfirm(v)}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          )}
          <button
            className="p-1.5 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
            title="Supprimer"
            onClick={() => setShowDeleteConfirm(v)}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Gestion des versions</h1>
          <p className="text-slate-500 mt-1">Publication APK, bundles hologrammes et canaux de distribution</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setShowUploadBundleModal(true)}>
            <FileCode className="w-4 h-4 mr-2" />
            Bundle
          </Button>
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload className="w-4 h-4 mr-2" />
            Upload APK
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card variant="bordered" padding="md">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Rechercher une version..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-xs"
            />
          </div>
          <Select
            options={channelOptions}
            value={channel}
            onChange={(e) => setChannel((e.target.value || '') as '' | ReleaseChannel)}
            className="w-full sm:w-48"
          />
        </div>
      </Card>

      {/* Versions Table */}
      <Card variant="bordered" padding="none">
        <CardHeader className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Versions APK</CardTitle>
              <CardDescription>{filteredVersions.length} version(s)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={filteredVersions}
            keyExtractor={(v) => v.id}
            isLoading={isLoading}
            emptyMessage="Aucune version trouvée"
            striped
            hoverable
          />
        </CardContent>
      </Card>

      {/* Bundles */}
      <Card variant="bordered" padding="none">
        <CardHeader className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Bundles hologrammes</CardTitle>
              <CardDescription>Données holographiques distribuées avec les versions</CardDescription>
            </div>
            <Badge variant="info">{bundles?.length || 0} bundles</Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {bundles?.length ? (
            <div className="divide-y divide-slate-100">
              {bundles.map((bundle) => (
                <div key={bundle.id} className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-green-600 shrink-0">
                      <FileCode className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900 truncate">{bundle.bundle_name}</p>
                      <p className="text-sm text-slate-500">
                        v{bundle.version} · {formatFileSize(bundle.bundle_file_size)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <Badge variant={bundle.is_active ? 'success' : 'outline'}>
                      {bundle.is_active ? 'Actif' : 'Inactif'}
                    </Badge>
                    <span className="text-sm text-slate-400">{formatDate(bundle.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">Aucun bundle hologramme</div>
          )}
        </CardContent>
      </Card>

      {/* Upload APK Modal */}
      <UploadApkModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['versions'] })
          setShowUploadModal(false)
        }}
      />

      {/* Upload Bundle Modal */}
      <UploadBundleModal
        isOpen={showUploadBundleModal}
        onClose={() => setShowUploadBundleModal(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['bundles'] })
          setShowUploadBundleModal(false)
        }}
      />

      {/* Publish Confirmation */}
      <ConfirmDialog
        isOpen={!!showPublishConfirm}
        onClose={() => setShowPublishConfirm(null)}
        onConfirm={() => showPublishConfirm && publishMutation.mutate({ id: showPublishConfirm.id, isActive: !showPublishConfirm.is_active })}
        title={showPublishConfirm?.is_active ? 'Dépublier la version' : 'Publier la version'}
        message={
          showPublishConfirm?.is_active
            ? 'Dépublier la version v' + showPublishConfirm?.version_name + ' ? Les appareils ne recevront plus cette mise à jour.'
            : 'Publier la version v' + showPublishConfirm?.version_name + ' ? Elle sera proposée aux appareils sur le canal ' + getStatusLabel(showPublishConfirm?.channel || '') + '.'
        }
        confirmText={showPublishConfirm?.is_active ? 'Dépublier' : 'Publier'}
        variant={showPublishConfirm?.is_active ? 'warning' : 'primary'}
        isLoading={publishMutation.isPending}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(null)}
        onConfirm={() => showDeleteConfirm && deleteMutation.mutate(showDeleteConfirm.id)}
        title="Supprimer la version"
        message={'Supprimer définitivement la version v' + (showDeleteConfirm?.version_name || '') + ' ? Cette action est irréversible.'}
        confirmText="Supprimer"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}

// ──────────────────────────────────────────────
// Upload APK Modal
// ──────────────────────────────────────────────
interface UploadApkModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

function UploadApkModal({ isOpen, onClose, onSuccess }: UploadApkModalProps) {
  const [form, setForm] = useState({
    version_name: '',
    version_code: '',
    channel: 'alpha',
    is_mandatory: false,
    changelog: '',
  })
  const [apkFile, setApkFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setError(null)
    if (!form.version_name || !form.version_code || !apkFile) {
      setError('Veuillez remplir tous les champs obligatoires (version, code, fichier APK).')
      return
    }
    if (isNaN(Number(form.version_code)) || Number(form.version_code) < 1) {
      setError('Le code de version doit être un nombre positif.')
      return
    }
    if (!apkFile.name.endsWith('.apk')) {
      setError('Le fichier doit être un APK (.apk).')
      return
    }

    setIsSubmitting(true)
    try {
      await api.createVersion({
        version_name: form.version_name,
        version_code: Number(form.version_code),
        channel: form.channel,
        is_mandatory: form.is_mandatory,
        changelog: form.changelog || undefined,
        file: apkFile,
      })
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'upload.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Uploader une nouvelle version"
      description="Publiez un APK sur le canal de votre choix"
      size="lg"
    >
      <div className="space-y-5">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="version-name" className="block text-sm font-medium text-slate-700 mb-1.5">
              Version (ex: 2.1.1)
            </label>
            <Input
              id="version-name"
              placeholder="2.1.1"
              value={form.version_name}
              onChange={(e) => setForm({ ...form, version_name: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="version-code" className="block text-sm font-medium text-slate-700 mb-1.5">
              Code de build (croissant)
            </label>
            <Input
              id="version-code"
              type="number"
              min="1"
              placeholder="211"
              value={form.version_code}
              onChange={(e) => setForm({ ...form, version_code: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Canal de distribution
            </label>
            <Select
              options={[
                { value: 'alpha', label: 'Alpha - Testeurs internes' },
                { value: 'beta', label: 'Bêta - Testeurs externes' },
                { value: 'stable', label: 'Stable - Production' },
              ]}
              value={form.channel}
              onChange={(e) => setForm({ ...form, channel: e.target.value })}
            />
          </div>
          <div className="flex items-end pb-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_mandatory}
                onChange={(e) => setForm({ ...form, is_mandatory: e.target.checked })}
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-slate-700">Mise à jour obligatoire</span>
            </label>
          </div>
        </div>

        <div>
          <label htmlFor="changelog" className="block text-sm font-medium text-slate-700 mb-1.5">
            Changelog
          </label>
          <textarea
            id="changelog"
            rows={4}
            placeholder="Liste des changements de cette version..."
            value={form.changelog}
            onChange={(e) => setForm({ ...form, changelog: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Fichier APK <span className="text-red-500">*</span>
          </label>
          <FileUpload
            accept=".apk"
            maxSize={200 * 1024 * 1024}
            label="Déposer le fichier APK"
            hint="Le fichier APK à distribuer"
            onUpload={async (files) => {
              setApkFile(files[0])
              return [files[0]]
            }}
          />
        </div>

        <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Annuler
          </Button>
          <Button onClick={handleSubmit} isLoading={isSubmitting} disabled={isSubmitting}>
            <Upload className="w-4 h-4 mr-2" />
            {isSubmitting ? 'Upload en cours...' : 'Uploader la version'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

// ──────────────────────────────────────────────
// Upload Bundle Modal
// ──────────────────────────────────────────────
interface UploadBundleModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

function UploadBundleModal({ isOpen, onClose, onSuccess }: UploadBundleModalProps) {
  const [version, setVersion] = useState('')
  const [description, setDescription] = useState('')
  const [bundleFile, setBundleFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setError(null)
    if (!version || !bundleFile) {
      setError('Veuillez fournir la version et le fichier du bundle.')
      return
    }
    setIsSubmitting(true)
    try {
      await api.createBundle({
        version,
        description: description || undefined,
        file: bundleFile,
      })
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'upload.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Uploader un bundle hologramme"
      size="md"
    >
      <div className="space-y-5">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        <Input
          label="Version du bundle"
          placeholder="1.0.0"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
        />

        <div>
          <label htmlFor="bundle-desc" className="block text-sm font-medium text-slate-700 mb-1.5">
            Description (optionnel)
          </label>
          <textarea
            id="bundle-desc"
            rows={3}
            placeholder="Contenu du bundle hologramme..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Fichier bundle <span className="text-red-500">*</span>
          </label>
          <FileUpload
            accept=".zip,.json"
            maxSize={100 * 1024 * 1024}
            label="Déposer le fichier bundle"
            hint="Archive zip ou json des données holographiques"
            onUpload={async (files) => {
              setBundleFile(files[0])
              return [files[0]]
            }}
          />
        </div>

        <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Annuler
          </Button>
          <Button onClick={handleSubmit} isLoading={isSubmitting} disabled={isSubmitting}>
            <Upload className="w-4 h-4 mr-2" />
            {isSubmitting ? 'Upload en cours...' : 'Uploader le bundle'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}