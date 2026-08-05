// ──────────────────────────────────────────────
// Forgot / Reset Password Pages
// ──────────────────────────────────────────────
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Shield, Mail, ArrowLeft, KeyRound, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent } from '../components/ui/Card'
import { api } from '../services/api'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setError(null)
    try {
      await api.requestPasswordReset(email)
      setStatus('success')
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'envoi')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-12 h-12 rounded-xl bg-primary-600 flex items-center justify-center">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-slate-900">Vital KA</span>
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Mot de passe oublié</h1>
          <p className="mt-2 text-slate-600">Entrez votre email pour recevoir un lien de réinitialisation</p>
        </div>

        <Card variant="elevated" padding="lg">
          <CardContent>
            {status === 'success' ? (
              <div className="text-center space-y-4">
                <div className="mx-auto w-14 h-14 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-7 h-7 text-green-600" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900">Email envoyé !</h2>
                <p className="text-sm text-slate-500">
                  Si un compte existe pour <strong>{email}</strong>, vous recevrez un lien de réinitialisation dans quelques minutes.
                </p>
                <Link to="/login" className="block">
                  <Button variant="outline" className="w-full">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Retour à la connexion
                  </Button>
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {status === 'error' && error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm">{error}</p>
                  </div>
                )}

                <Input
                  label="Email"
                  type="email"
                  placeholder="admin@vital-ka.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={status === 'loading'}
                  required
                  autoFocus
                />

                <Button type="submit" className="w-full" isLoading={status === 'loading'}>
                  <Mail className="w-4 h-4 mr-2" />
                  Envoyer le lien
                </Button>

                <div className="text-center">
                  <Link to="/login" className="text-sm text-primary-600 hover:text-primary-700">
                    <ArrowLeft className="w-3.5 h-3.5 inline mr-1" />
                    Retour à la connexion
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.')
      return
    }
    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.')
      return
    }
    if (!token) {
      setError('Token de réinitialisation manquant.')
      return
    }

    setStatus('loading')
    setError(null)
    try {
      await api.resetPassword(token, password)
      setStatus('success')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Erreur lors de la réinitialisation')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-12 h-12 rounded-xl bg-primary-600 flex items-center justify-center">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-slate-900">Vital KA</span>
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Nouveau mot de passe</h1>
          <p className="mt-2 text-slate-600">Définissez un nouveau mot de passe pour votre compte</p>
        </div>

        <Card variant="elevated" padding="lg">
          <CardContent>
            {status === 'success' ? (
              <div className="text-center space-y-4">
                <div className="mx-auto w-14 h-14 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-7 h-7 text-green-600" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900">Mot de passe modifié !</h2>
                <p className="text-sm text-slate-500">Redirection vers la page de connexion...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {status === 'error' && error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm">{error}</p>
                  </div>
                )}

                <Input
                  label="Nouveau mot de passe"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={status === 'loading'}
                  hint="Au moins 8 caractères"
                  required
                  autoFocus
                />
                <Input
                  label="Confirmer le mot de passe"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={status === 'loading'}
                  required
                />

                <Button type="submit" className="w-full" isLoading={status === 'loading'}>
                  <KeyRound className="w-4 h-4 mr-2" />
                  Réinitialiser le mot de passe
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}