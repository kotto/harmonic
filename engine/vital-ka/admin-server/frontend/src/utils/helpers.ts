// ──────────────────────────────────────────────
// Utility Functions
// ──────────────────────────────────────────────
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatDateShort(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    // Doctor statuses
    pending: 'bg-yellow-100 text-yellow-800',
    under_review: 'bg-blue-100 text-blue-800',
    validated: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    suspended: 'bg-gray-100 text-gray-800',
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    // Document statuses
    approved: 'bg-green-100 text-green-800',
    // Version channels
    alpha: 'bg-purple-100 text-purple-800',
    beta: 'bg-orange-100 text-orange-800',
    stable: 'bg-green-100 text-green-800',
    // Webhook statuses
    success: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    // Health statuses
    healthy: 'bg-green-100 text-green-800',
    degraded: 'bg-yellow-100 text-yellow-800',
    unhealthy: 'bg-red-100 text-red-800',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: 'En attente',
    under_review: 'En cours de validation',
    validated: 'Validé',
    rejected: 'Rejeté',
    suspended: 'Suspendu',
    active: 'Actif',
    inactive: 'Inactif',
    approved: 'Approuvé',
    alpha: 'Alpha',
    beta: 'Bêta',
    stable: 'Stable',
    success: 'Succès',
    failed: 'Échec',
    healthy: 'Sain',
    degraded: 'Dégradé',
    unhealthy: 'Critique',
  }
  return labels[status] || status
}

export function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    admin: 'Administrateur',
    validator: 'Validateur',
    doctor: 'Médecin',
    patient: 'Patient',
  }
  return labels[role] || role
}

export function getFullName(user: { first_name?: string; last_name?: string } | null | undefined): string {
  if (!user) return ''
  return [user.first_name, user.last_name].filter(Boolean).join(' ') || 'Utilisateur'
}

export function getInitials(user: { first_name?: string; last_name?: string } | null | undefined): string {
  if (!user) return '?'
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || '?'
}

export function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    admin: 'bg-red-100 text-red-800',
    validator: 'bg-blue-100 text-blue-800',
    doctor: 'bg-green-100 text-green-800',
    patient: 'bg-purple-100 text-purple-800',
  }
  return colors[role] || 'bg-gray-100 text-gray-800'
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return `${text.slice(0, length)}...`
}

export function generateAvatarUrl(name: string): string {
  const encodedName = encodeURIComponent(name)
  return `https://ui-avatars.com/api/?name=${encodedName}&background=0ea5e9&color=fff&size=128`
}