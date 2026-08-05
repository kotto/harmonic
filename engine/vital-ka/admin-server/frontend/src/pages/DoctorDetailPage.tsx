// ──────────────────────────────────────────────
// Doctor Detail Page (KYC Workflow)
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Mail,
  Phone,
  Stethoscope,
  Hash,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  Eye,
  Download,
  Shield,
  Calendar,
  Fingerprint,
  GraduationCap,
  MapPin,
  Loader2,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import { api } from '../services/api'
import { formatDate, formatFileSize, getStatusColor, getStatusLabel, getFullName, cn } from '../utils/helpers'
import type { KYCDocument, VerificationLog } from '../types'

const documentTypeLabels: Record<string, string> = {
  identity: "Pièce d'identité",
  medical_degree: 'Diplôme de médecine',
  license: "Licence d'exercice",
  specialty_cert: 'Certificat de spécialité',
  proof_address: "Justificatif d'adresse",
  cv: 'CV',
  other: 'Autre',
}

const documentTypeIcons: Record<string, typeof Fingerprint> = {
  identity: Fingerprint,
  medical_degree: GraduationCap,
  license: Shield,
  specialty_cert: GraduationCap,
  proof_address: MapPin,
  cv: FileText,
  other: FileText,
}

const logActionLabels: Record<string, string> = {
  created: 'Création du compte',
  submitted: 'Soumission KYC',
  reviewed: 'Dossier examiné',
  validated: 'Validation',
  rejected: 'Rejet',
  suspended: 'Suspension',
}

const logActionIcons: Record<string, typeof Clock> = {
  validated: CheckCircle,
  rejected: XCircle,
  suspended: AlertTriangle,
  submitted: Clock,
  reviewed: Eye,
  created: Clock,
}

interface DocVerifyState {
  doc: KYCDocument
  action: 'approve' | 'reject'
}

export function DoctorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const [verifyState, setVerifyState] = useState<DocVerifyState | null>(null)
  const [verifyNotes, setVerifyNotes] = useState('')
  const [showDocModal, setShowDocModal] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<KYCDocument | null>(null)
  const [actionState, setActionState] = useState<'validate' | 'reject' | 'suspend' | null>(null)
  const [actionNotes, setActionNotes] = useState('')

  const { data: doctor, isLoading } = useQuery({
    queryKey: ['doctor', id],
    queryFn: () => api.getDoctor(id!),
    enabled: !!id,
  })

  const verifyDocMutation = useMutation({
    mutationFn: ({ docId, isVerified, reason }: { docId: string; isVerified: boolean; reason?: string }) =>
      api.verifyDoctorDocument(id!, docId, isVerified, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', id] })
      setVerifyState(null)
      setVerifyNotes('')
    },
  })

  const validateMutation = useMutation({
    mutationFn: (notes?: string) => api.validateDoctor(id!, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', id] })
      setActionState(null)
      setActionNotes('')
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => api.rejectDoctor(id!, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', id] })
      setActionState(null)
      setActionNotes('')
    },
  })

  const suspendMutation = useMutation({
    mutationFn: (reason: string) => api.suspendDoctor(id!, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', id] })
      setActionState(null)
      setActionNotes('')
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!doctor) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
        <AlertTriangle className="w-12 h-12 text-slate-300" />
        <p className="text-slate-500">Médecin introuvable</p>
        <Link to="/doctors">
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour à la liste
          </Button>
        </Link>
      </div>
    )
  }

  const pendingDocs = doctor.documents.filter((d) => !d.is_verified && !d.rejection_reason)
  const approvedDocs = doctor.documents.filter((d) => d.is_verified)
  const rejectedDocs = doctor.documents.filter((d) => !d.is_verified && d.rejection_reason)

  const handleConfirmAction = async () => {
    if (!actionState) return
    try {
      if (actionState === 'validate') {
        await validateMutation.mutateAsync(actionNotes || undefined)
      } else if (actionState === 'reject') {
        await rejectMutation.mutateAsync(actionNotes)
      } else if (actionState === 'suspend') {
        await suspendMutation.mutateAsync(actionNotes)
      }
    } catch (error) {
      console.error('Action failed:', error)
    }
  }

  const handleConfirmVerify = async () => {
    if (!verifyState) return
    try {
      await verifyDocMutation.mutateAsync({
        docId: verifyState.doc.id,
        isVerified: verifyState.action === 'approve',
        reason: verifyState.action === 'reject' ? verifyNotes : undefined,
      })
    } catch (error) {
      console.error('Verify failed:', error)
    }
  }

  const renderDocumentCard = (doc: KYCDocument) => {
    const Icon = documentTypeIcons[doc.document_type] || FileText
    const verified = doc.is_verified
    const rejected = !doc.is_verified && !!doc.rejection_reason

    return (
      <div
        key={doc.id}
        className="p-4 rounded-lg border border-slate-200 hover:border-primary-300 hover:shadow-sm transition-all cursor-pointer"
        onClick={() => {
          setSelectedDoc(doc)
          setShowDocModal(true)
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
              verified ? 'bg-green-100 text-green-600' : rejected ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'
            )}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="font-medium text-slate-900 truncate">{documentTypeLabels[doc.document_type]}</p>
              <p className="text-sm text-slate-500 truncate">{doc.file_name} · {formatFileSize(doc.file_size)}</p>
            </div>
          </div>
          <Badge variant="outline" className={cn(verified ? 'bg-green-100 text-green-800' : rejected ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800', 'shrink-0')}>
            {verified ? 'Vérifié' : rejected ? 'Rejeté' : 'En attente'}
          </Badge>
        </div>
        {doc.rejection_reason && (
          <p className="mt-2 text-sm text-slate-500 line-clamp-2">Motif : {doc.rejection_reason}</p>
        )}
        <div className="mt-3 flex items-center gap-3">
          <button
            className="inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700"
            onClick={(e) => {
              e.stopPropagation()
              setSelectedDoc(doc)
              setShowDocModal(true)
            }}
          >
            <Eye className="w-3.5 h-3.5" />
            Aperçu
          </button>
          {!verified && (
            <>
              <button
                className="inline-flex items-center gap-1 text-xs font-medium text-green-600 hover:text-green-700"
                onClick={(e) => {
                  e.stopPropagation()
                  setVerifyState({ doc, action: 'approve' })
                  setVerifyNotes('')
                }}
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Approuver
              </button>
              <button
                className="inline-flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-700"
                onClick={(e) => {
                  e.stopPropagation()
                  setVerifyState({ doc, action: 'reject' })
                  setVerifyNotes('')
                }}
              >
                <XCircle className="w-3.5 h-3.5" />
                Rejeter
              </button>
            </>
          )}
        </div>
      </div>
    )
  }

  const actionTitle =
    actionState === 'validate' ? 'Valider le médecin'
      : actionState === 'reject' ? 'Rejeter le médecin'
      : 'Suspendre le médecin'

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/doctors" className="hover:text-primary-600">Médecins</Link>
        <span>/</span>
        <span className="text-slate-900 font-medium">Dr {getFullName(doctor)}</span>
      </div>

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-xl font-bold">
            {getFullName(doctor).charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Dr {getFullName(doctor)}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className={getStatusColor(doctor.status)}>
                {getStatusLabel(doctor.status)}
              </Badge>
              <span className="text-sm text-slate-500">Inscrit le {formatDate(doctor.created_at)}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {doctor.status === 'pending' || doctor.status === 'under_review' ? (
            <>
              <Button variant="danger" onClick={() => setActionState('reject')}>
                <XCircle className="w-4 h-4 mr-2" />
                Rejeter
              </Button>
              <Button onClick={() => setActionState('validate')}>
                <CheckCircle className="w-4 h-4 mr-2" />
                Valider
              </Button>
            </>
          ) : doctor.status === 'validated' ? (
            <Button variant="danger" onClick={() => setActionState('suspend')}>
              <AlertTriangle className="w-4 h-4 mr-2" />
              Suspendre
            </Button>
          ) : null}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Profile Info */}
        <div className="space-y-6">
          <Card variant="bordered">
            <CardHeader>
              <CardTitle>Informations professionnelles</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-slate-500">Email</p>
                  <a href={`mailto:${doctor.email}`} className="font-medium text-slate-900 hover:text-primary-600">
                    {doctor.email}
                  </a>
                </div>
              </div>

              {doctor.phone && (
                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-500">Téléphone</p>
                    <p className="font-medium text-slate-900">{doctor.phone}</p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-3">
                <Stethoscope className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-slate-500">Spécialité</p>
                  <p className="font-medium text-slate-900">{doctor.specialty || '—'}</p>
                  {doctor.sub_specialty && (
                    <p className="text-sm text-slate-500">{doctor.sub_specialty}</p>
                  )}
                  {doctor.years_experience !== undefined && doctor.years_experience !== null && (
                    <p className="text-sm text-slate-500">{doctor.years_experience} ans d'expérience</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Hash className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-slate-500">Numéro de licence</p>
                  <p className="font-medium text-slate-900">{doctor.license_number}</p>
                </div>
              </div>

              {doctor.city && (
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-500">Localisation</p>
                    <p className="font-medium text-slate-900">
                      {[doctor.city, doctor.country].filter(Boolean).join(', ')}
                    </p>
                  </div>
                </div>
              )}

              {doctor.validated_at && (
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-500">Validé le</p>
                    <p className="font-medium text-slate-900">{formatDate(doctor.validated_at)}</p>
                  </div>
                </div>
              )}

              {doctor.rejection_reason && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-100">
                  <p className="text-xs text-red-500 uppercase font-medium mb-1">Motif du rejet</p>
                  <p className="text-sm text-red-800">{doctor.rejection_reason}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* KYC Progress */}
          <Card variant="bordered">
            <CardHeader>
              <CardTitle>Progression KYC</CardTitle>
              <CardDescription>Documents requis pour la validation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-500">Documents vérifiés</span>
                  <span className="font-medium">{approvedDocs.length}/{doctor.documents.length}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      doctor.documents.length > 0 && approvedDocs.length === doctor.documents.length
                        ? 'bg-green-500'
                        : 'bg-primary-600'
                    )}
                    style={{ width: `${doctor.documents.length > 0 ? (approvedDocs.length / doctor.documents.length) * 100 : 0}%` }}
                  />
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2">
                  <div className="text-center p-2 rounded-lg bg-yellow-50">
                    <p className="text-lg font-bold text-yellow-600">{pendingDocs.length}</p>
                    <p className="text-xs text-slate-500">En attente</p>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-green-50">
                    <p className="text-lg font-bold text-green-600">{approvedDocs.length}</p>
                    <p className="text-xs text-slate-500">Vérifiés</p>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-red-50">
                    <p className="text-lg font-bold text-red-600">{rejectedDocs.length}</p>
                    <p className="text-xs text-slate-500">Rejetés</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Documents & Logs */}
        <div className="lg:col-span-2 space-y-6">
          <Card variant="bordered">
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle>Documents KYC</CardTitle>
                <CardDescription>Documents soumis par le médecin</CardDescription>
              </div>
              <Badge variant="info">{doctor.documents.length} documents</Badge>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {doctor.documents.map((doc) => renderDocumentCard(doc))}
              </div>
              {doctor.documents.length === 0 && (
                <div className="text-center py-8 text-slate-500">Aucun document soumis</div>
              )}
            </CardContent>
          </Card>

          <Card variant="bordered">
            <CardHeader>
              <CardTitle>Journal de vérification</CardTitle>
              <CardDescription>Historique des actions sur ce dossier</CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="relative border-l border-slate-200 ml-3 space-y-6">
                {doctor.verification_logs.map((log: VerificationLog) => {
                  const Icon = logActionIcons[log.action] || Clock
                  return (
                    <li key={log.id} className="ml-6">
                      <span className="absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full bg-white border border-slate-200">
                        <Icon className={cn(
                          'w-4 h-4',
                          log.action === 'validated' ? 'text-green-600'
                            : log.action === 'rejected' ? 'text-red-600'
                            : log.action === 'suspended' ? 'text-yellow-600'
                            : 'text-slate-400'
                        )} />
                      </span>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium text-slate-900 text-sm">
                          {logActionLabels[log.action] || log.action}
                        </p>
                        <span className="text-xs text-slate-400">{formatDate(log.created_at)}</span>
                      </div>
                      {log.to_status && (
                        <p className="mt-0.5 text-xs text-slate-500">
                          Statut : {log.from_status ? getStatusLabel(log.from_status) + ' → ' : ''}{getStatusLabel(log.to_status)}
                        </p>
                      )}
                      {log.notes && <p className="mt-1 text-sm text-slate-500">{log.notes}</p>}
                    </li>
                  )
                })}
                {doctor.verification_logs.length === 0 && (
                  <li className="ml-6 text-sm text-slate-500">Aucun événement de vérification</li>
                )}
              </ol>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Doctor Action Modal */}
      <Modal
        isOpen={!!actionState}
        onClose={() => { setActionState(null); setActionNotes('') }}
        title={actionTitle}
        description={`Dr ${getFullName(doctor)} — ${doctor.email}`}
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            {actionState === 'validate' && "Le compte sera activé et une notification email sera envoyée au médecin."}
            {actionState === 'reject' && "Le médecin sera notifié par email avec le motif du rejet."}
            {actionState === 'suspend' && "Le compte sera désactivé immédiatement. Le médecin en sera informé."}
          </p>

          <div>
            <label htmlFor="action-notes" className="block text-sm font-medium text-slate-700 mb-1.5">
              {actionState === 'validate' ? 'Notes (optionnel)' : 'Motif (obligatoire, min. 10 caractères)'}
            </label>
            <textarea
              id="action-notes"
              rows={3}
              value={actionNotes}
              onChange={(e) => setActionNotes(e.target.value)}
              placeholder={
                actionState === 'validate'
                  ? 'Commentaire interne...'
                  : actionState === 'reject'
                    ? 'Ex: documents illisibles, identité non vérifiable...'
                    : 'Ex: exercice illégal constaté...'
              }
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
            />
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => { setActionState(null); setActionNotes('') }}
              disabled={validateMutation.isPending || rejectMutation.isPending || suspendMutation.isPending}>
              Annuler
            </Button>
            <Button
              variant={actionState === 'validate' ? 'primary' : 'danger'}
              onClick={handleConfirmAction}
              isLoading={validateMutation.isPending || rejectMutation.isPending || suspendMutation.isPending}
              disabled={actionState !== 'validate' && actionNotes.trim().length < 10}
            >
              {actionState === 'validate' ? 'Valider' : actionState === 'reject' ? 'Rejeter' : 'Suspendre'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Document Verify Modal */}
      <Modal
        isOpen={!!verifyState}
        onClose={() => { setVerifyState(null); setVerifyNotes('') }}
        title={verifyState?.action === 'approve' ? 'Approuver le document' : 'Rejeter le document'}
        description={verifyState ? documentTypeLabels[verifyState.doc.document_type] : undefined}
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            {verifyState?.action === 'approve'
              ? "Le document sera marqué comme vérifié. Le médecin en sera notifié."
              : "Le document sera rejeté. Le médecin devra en soumettre un nouveau."}
          </p>

          {verifyState?.action === 'reject' && (
            <div>
              <label htmlFor="verify-notes" className="block text-sm font-medium text-slate-700 mb-1.5">
                Motif du rejet (obligatoire, min. 10 caractères)
              </label>
              <textarea
                id="verify-notes"
                rows={3}
                value={verifyNotes}
                onChange={(e) => setVerifyNotes(e.target.value)}
                placeholder="Ex: document illisible, photo non conforme..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
              />
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => { setVerifyState(null); setVerifyNotes('') }} disabled={verifyDocMutation.isPending}>
              Annuler
            </Button>
            <Button
              variant={verifyState?.action === 'approve' ? 'primary' : 'danger'}
              onClick={handleConfirmVerify}
              isLoading={verifyDocMutation.isPending}
              disabled={verifyState?.action === 'reject' && verifyNotes.trim().length < 10}
            >
              {verifyState?.action === 'approve' ? 'Approuver' : 'Rejeter'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Document Preview Modal */}
      <Modal
        isOpen={showDocModal && !!selectedDoc}
        onClose={() => setShowDocModal(false)}
        title={selectedDoc ? documentTypeLabels[selectedDoc.document_type] : ''}
        size="lg"
      >
        {selectedDoc && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="w-5 h-5 text-slate-400 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium text-slate-900 truncate">{selectedDoc.file_name}</p>
                  <p className="text-sm text-slate-500">
                    {formatFileSize(selectedDoc.file_size)} · Déposé le {formatDate(selectedDoc.created_at)}
                  </p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  selectedDoc.is_verified ? 'bg-green-100 text-green-800'
                    : selectedDoc.rejection_reason ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800',
                  'shrink-0'
                )}
              >
                {selectedDoc.is_verified ? 'Vérifié' : selectedDoc.rejection_reason ? 'Rejeté' : 'En attente'}
              </Badge>
            </div>

            <div className="aspect-video bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-center overflow-hidden">
              {selectedDoc.mime_type?.startsWith('image/') ? (
                <img
                  src={`/api/v1/doctors/${doctor.id}/documents/${selectedDoc.id}/download`}
                  alt={selectedDoc.file_name}
                  className="max-w-full max-h-96 object-contain rounded-lg"
                />
              ) : (
                <div className="text-center text-slate-400 p-8">
                  <FileText className="w-12 h-12 mx-auto mb-2" />
                  <p>Aperçu non disponible pour ce type de fichier</p>
                  <a
                    href={`/api/v1/doctors/${doctor.id}/documents/${selectedDoc.id}/download`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-primary-600 hover:text-primary-700"
                  >
                    <Download className="w-4 h-4" />
                    Télécharger le fichier
                  </a>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <Button
                variant="ghost"
                onClick={() => window.open(`/api/v1/doctors/${doctor.id}/documents/${selectedDoc.id}/download`, '_blank')}
              >
                <Download className="w-4 h-4 mr-2" />
                Télécharger
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}