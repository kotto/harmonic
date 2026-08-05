// ──────────────────────────────────────────────
// Profile Page
// ──────────────────────────────────────────────
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Mail,
  Shield,
  KeyRound,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Save,
  LogOut,
  Clock,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { formatDate, getRoleColor, getRoleLabel, getFullName, getInitials } from '../utils/helpers'

export function ProfilePage() {
  const { user, refreshUser, logout } = useAuth()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const changePasswordMutation = useMutation({
    mutationFn: ({ current, next }: { current: string; next: string }) =>
      api.changePassword(current, next),
    onSuccess: () => {
      setSuccess(true)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => setSuccess(false), 3000)
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Erreur lors du changement de mot de passe')
    },
  })

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (newPassword.length < 12) {
      setError('Le nouveau mot de passe doit contenir au moins 12 caractères.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Les nouveaux mots de passe ne correspondent pas.')
      return
    }

    changePasswordMutation.mutate({ current: currentPassword, next: newPassword })
  }

  if (!user) return null

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Mon profil</h1>
        <p className="text-slate-500 mt-1">Informations du compte et sécurité</p>
      </div>

      {/* Profile Info */}
      <Card variant="bordered">
        <CardHeader>
          <CardTitle>Informations du compte</CardTitle>
          <CardDescription>Vos informations personnelles</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6 mb-8">
            <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-2xl font-bold">
              {getInitials(user)}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{getFullName(user)}</h2>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={getRoleColor(user.role)}>
                  {getRoleLabel(user.role)}
                </Badge>
                <Badge variant="success">Actif</Badge>
              </div>
            </div>
          </div>

          <dl className="space-y-4">
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-slate-400" />
              <div>
                <dt className="text-xs text-slate-500 uppercase font-medium">Email</dt>
                <dd className="font-medium text-slate-900">{user.email}</dd>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-slate-400" />
              <div>
                <dt className="text-xs text-slate-500 uppercase font-medium">Rôle</dt>
                <dd className="font-medium text-slate-900">{getRoleLabel(user.role)}</dd>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-slate-400" />
              <div>
                <dt className="text-xs text-slate-500 uppercase font-medium">Compte créé le</dt>
                <dd className="font-medium text-slate-900">{formatDate(user.created_at)}</dd>
              </div>
            </div>
            {user.last_login && (
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-slate-400" />
                <div>
                  <dt className="text-xs text-slate-500 uppercase font-medium">Dernière connexion</dt>
                  <dd className="font-medium text-slate-900">{formatDate(user.last_login)}</dd>
                </div>
              </div>
            )}
          </dl>
        </CardContent>
        <CardFooter>
          <Button variant="outline" onClick={() => refreshUser()}>
            Actualiser les informations
          </Button>
        </CardFooter>
      </Card>

      {/* Change Password */}
      <Card variant="bordered">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-primary-600" />
            Changer le mot de passe
          </CardTitle>
          <CardDescription>Mettez à jour votre mot de passe régulièrement (min. 12 caractères)</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">Mot de passe modifié avec succès !</p>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
            <div className="relative">
              <Input
                label="Mot de passe actuel"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-slate-400 hover:text-slate-600"
                aria-label={showPassword ? 'Masquer' : 'Afficher'}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            <Input
              label="Nouveau mot de passe"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              hint="Au moins 12 caractères"
              required
              autoComplete="new-password"
            />
            <Input
              label="Confirmer le nouveau mot de passe"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
            />

            <Button type="submit" isLoading={changePasswordMutation.isPending}>
              <Save className="w-4 h-4 mr-2" />
              Mettre à jour le mot de passe
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card variant="bordered" className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-700">Zone de danger</CardTitle>
          <CardDescription>Actions irréversibles</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-lg bg-red-50 border border-red-100">
            <div>
              <p className="font-medium text-slate-900">Se déconnecter</p>
              <p className="text-sm text-slate-500">Terminer votre session sur cet appareil</p>
            </div>
            <Button variant="danger" onClick={() => logout()}>
              <LogOut className="w-4 h-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}