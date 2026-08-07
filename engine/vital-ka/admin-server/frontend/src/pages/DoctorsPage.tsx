// ──────────────────────────────────────────────
// Doctors List Page
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Search,
  Download,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react'
import { Table, Pagination } from '../components/ui/Table'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { api } from '../services/api'
import { formatDate, getStatusColor, getStatusLabel, getFullName, cn } from '../utils/helpers'
import type { DoctorListResponse, DoctorFilters, DoctorStatus } from '../types'

const statusOptions: Array<{ value: '' | DoctorStatus; label: string }> = [
  { value: '', label: 'Tous les statuts' },
  { value: 'pending', label: 'En attente' },
  { value: 'under_review', label: 'En cours' },
  { value: 'validated', label: 'Validé' },
  { value: 'rejected', label: 'Rejeté' },
  { value: 'suspended', label: 'Suspendu' },
]

interface ActionState {
  type: 'validate' | 'reject' | 'suspend'
  doctor: DoctorListResponse
}

export function DoctorsPage() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<DoctorFilters>({
    page: 1,
    page_size: 10,
    query: '',
    status: undefined,
  })
  const [actionState, setActionState] = useState<ActionState | null>(null)
  const [actionNotes, setActionNotes] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['doctors', filters],
    queryFn: () => api.getDoctors(filters),
  })

  const validateMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) => api.validateDoctor(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors'] })
      setActionState(null)
      setActionNotes('')
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => api.rejectDoctor(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors'] })
      setActionState(null)
      setActionNotes('')
    },
  })

  const suspendMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => api.suspendDoctor(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors'] })
      setActionState(null)
      setActionNotes('')
    },
  })

  const handleFilterChange = (key: keyof DoctorFilters, value: unknown) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }))
  }

  const isPending = validateMutation.isPending || rejectMutation.isPending || suspendMutation.isPending

  const handleConfirm = async () => {
    if (!actionState) return
    const { type, doctor } = actionState
    try {
      if (type === 'validate') {
        await validateMutation.mutateAsync({ id: doctor.id, notes: actionNotes || undefined })
      } else if (type === 'reject') {
        await rejectMutation.mutateAsync({ id: doctor.id, reason: actionNotes })
      } else if (type === 'suspend') {
        await suspendMutation.mutateAsync({ id: doctor.id, reason: actionNotes })
      }
    } catch (error) {
      console.error('Action failed:', error)
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Médecin',
      render: (doctor: DoctorListResponse) => (
        <Link to={`/doctors/${doctor.id}`} className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-medium text-sm">
            {getFullName(doctor).charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-medium text-slate-900">{getFullName(doctor)}</p>
            <p className="text-sm text-slate-500">{doctor.email}</p>
          </div>
        </Link>
      ),
    },
    {
      key: 'specialty',
      header: 'Spécialité',
      render: (doctor: DoctorListResponse) => doctor.specialty || <span className="text-slate-400">—</span>,
    },
    {
      key: 'license_number',
      header: 'Licence',
      render: (doctor: DoctorListResponse) => doctor.license_number,
    },
    {
      key: 'city',
      header: 'Ville',
      render: (doctor: DoctorListResponse) => doctor.city || <span className="text-slate-400">—</span>,
    },
    {
      key: 'status',
      header: 'Statut',
      render: (doctor: DoctorListResponse) => (
        <Badge variant="outline" className={cn(getStatusColor(doctor.status), 'capitalize')}>
          {getStatusLabel(doctor.status)}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      header: 'Inscription',
      render: (doctor: DoctorListResponse) => formatDate(doctor.created_at),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (doctor: DoctorListResponse) => (
        <div className="flex items-center gap-2">
          <Link
            to={`/doctors/${doctor.id}`}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="Voir détails"
          >
            <Eye className="w-4 h-4" />
          </Link>
          {doctor.status === 'pending' || doctor.status === 'under_review' ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActionState({ type: 'validate', doctor })}
                className="text-green-600 hover:bg-green-50"
                title="Valider"
              >
                <CheckCircle className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActionState({ type: 'reject', doctor })}
                className="text-red-600 hover:bg-red-50"
                title="Rejeter"
              >
                <XCircle className="w-4 h-4" />
              </Button>
            </>
          ) : doctor.status === 'validated' ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setActionState({ type: 'suspend', doctor })}
              className="text-yellow-600 hover:bg-yellow-50"
              title="Suspendre"
            >
              <AlertTriangle className="w-4 h-4" />
            </Button>
          ) : null}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Gestion des médecins</h1>
          <p className="text-slate-500 mt-1">Inscription, validation KYC et suivi des praticiens</p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            if (!data) return
            const blob = new Blob([JSON.stringify(data.items, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `medecins-${new Date().toISOString().slice(0, 10)}.json`
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
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Rechercher par nom, email, licence..."
              value={filters.query || ''}
              onChange={(e) => handleFilterChange('query', e.target.value)}
              className="pl-9"
            />
          </div>
          <Select
            options={statusOptions}
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', (e.target.value || undefined) as DoctorStatus | undefined)}
            className="w-full sm:w-48"
          />
        </div>
      </Card>

      {/* Table */}
      <Card variant="bordered" padding="none">
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={data?.items || []}
            keyExtractor={(doctor) => doctor.id}
            isLoading={isLoading}
            emptyMessage="Aucun médecin trouvé"
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

      {/* Action Modal */}
      <Modal
        isOpen={!!actionState}
        onClose={() => {
          setActionState(null)
          setActionNotes('')
        }}
        title={
          actionState?.type === 'validate'
            ? 'Valider le médecin'
            : actionState?.type === 'reject'
              ? 'Rejeter le médecin'
              : 'Suspendre le médecin'
        }
        description={
          actionState
            ? `Dr ${getFullName(actionState.doctor)} — ${actionState.doctor.email}`
            : undefined
        }
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            {actionState?.type === 'validate' && "Le compte sera activé et une notification email sera envoyée au médecin."}
            {actionState?.type === 'reject' && "Le médecin sera notifié par email avec le motif du rejet."}
            {actionState?.type === 'suspend' && "Le compte sera désactivé immédiatement. Le médecin en sera informé."}
          </p>

          <div>
            <label htmlFor="action-notes" className="block text-sm font-medium text-slate-700 mb-1.5">
              {actionState?.type === 'validate' ? 'Notes (optionnel)' : 'Motif (obligatoire, min. 10 caractères)'}
            </label>
            <textarea
              id="action-notes"
              rows={3}
              value={actionNotes}
              onChange={(e) => setActionNotes(e.target.value)}
              placeholder={
                actionState?.type === 'validate'
                  ? 'Commentaire interne...'
                  : actionState?.type === 'reject'
                    ? 'Ex: documents illisibles, identité non vérifiable...'
                    : 'Ex: exercice illégal constaté...'
              }
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
            />
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => { setActionState(null); setActionNotes('') }} disabled={isPending}>
              Annuler
            </Button>
            <Button
              variant={actionState?.type === 'validate' ? 'primary' : 'danger'}
              onClick={handleConfirm}
              isLoading={isPending}
              disabled={
                (actionState?.type === 'reject' || actionState?.type === 'suspend') &&
                actionNotes.trim().length < 10
              }
            >
              {actionState?.type === 'validate' ? 'Valider' : actionState?.type === 'reject' ? 'Rejeter' : 'Suspendre'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}