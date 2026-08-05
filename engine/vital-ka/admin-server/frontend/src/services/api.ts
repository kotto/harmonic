// ──────────────────────────────────────────────
// API Service — Routes réelles du backend
// ──────────────────────────────────────────────
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  UserInfo,
  TokenResponse,
  Doctor,
  DoctorSearchResponse,
  DoctorFilters,
  KYCDocument,
  VerificationLog,
  APKVersion,
  APKVersionListResponse,
  HologramBundle,
  VersionCheckResponse,
  WebhookLog,
  SystemConfig,
  HealthResponse,
  BackupInfo,

  AuditSearchResponse,
  AuditStats,
  MetricsSummary,
  AuditFilters,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

class ApiService {
  private client: AxiosInstance
  private refreshTokenPromise: Promise<string> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true
          try {
            const newToken = await this.refreshAccessToken()
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
            }
            return this.client(originalRequest)
          } catch (refreshError) {
            this.clearSession()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }
        return Promise.reject(error)
      }
    )
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise
    }

    this.refreshTokenPromise = (async () => {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) throw new Error('No refresh token')

      const response = await axios.post<TokenResponse>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      })
      const { access_token, refresh_token } = response.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      this.refreshTokenPromise = null
      return access_token
    })()

    return this.refreshTokenPromise
  }

  private clearSession() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // ──────────────────────────────────────────────
  // Auth
  // ──────────────────────────────────────────────
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', {
      ...credentials,
      remember_me: credentials.remember_me ?? false,
    })
    const { user, tokens } = response.data
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    localStorage.setItem('user', JSON.stringify(user))
    return response.data
  }

  async logoutApi(): Promise<void> {
    try {
      await this.client.post('/auth/logout')
    } finally {
      this.clearSession()
    }
  }

  async getCurrentUser(): Promise<UserInfo> {
    const response = await this.client.get<UserInfo>('/auth/me')
    return response.data
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await this.client.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  }

  async requestPasswordReset(email: string): Promise<void> {
    await this.client.post('/auth/forgot-password', { email })
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.client.post('/auth/reset-password', { token, new_password: newPassword })
  }

  // ──────────────────────────────────────────────
  // Doctors (admin/validator)
  // ──────────────────────────────────────────────
  async getDoctors(filters: DoctorFilters = {}): Promise<DoctorSearchResponse> {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value))
      }
    })
    const response = await this.client.get<DoctorSearchResponse>(`/doctors?${params.toString()}`)
    return response.data
  }

  async getDoctor(id: string): Promise<Doctor> {
    const response = await this.client.get<Doctor>(`/doctors/${id}`)
    return response.data
  }

  async validateDoctor(id: string, notes?: string): Promise<Doctor> {
    const response = await this.client.post<Doctor>(`/doctors/${id}/validate`, { notes })
    return response.data
  }

  async rejectDoctor(id: string, reason: string, notes?: string): Promise<Doctor> {
    const response = await this.client.post<Doctor>(`/doctors/${id}/reject`, { reason, notes })
    return response.data
  }

  async suspendDoctor(id: string, reason: string): Promise<Doctor> {
    const response = await this.client.post<Doctor>(`/doctors/${id}/suspend`, { reason })
    return response.data
  }

  async getDoctorDocuments(doctorId: string): Promise<KYCDocument[]> {
    const response = await this.client.get<KYCDocument[]>(`/doctors/${doctorId}/documents`)
    return response.data
  }

  async verifyDoctorDocument(doctorId: string, documentId: string, isVerified: boolean, rejectionReason?: string): Promise<KYCDocument> {
    const response = await this.client.post<KYCDocument>(`/doctors/${doctorId}/documents/${documentId}/verify`, {
      is_verified: isVerified,
      rejection_reason: rejectionReason,
    })
    return response.data
  }

  async getVerificationLogs(doctorId: string): Promise<VerificationLog[]> {
    const response = await this.client.get<VerificationLog[]>(`/doctors/${doctorId}/logs`)
    return response.data
  }

  // ──────────────────────────────────────────────
  // Versions APK & Bundles
  // ──────────────────────────────────────────────
  async getVersions(): Promise<APKVersionListResponse[]> {
    const response = await this.client.get<APKVersionListResponse[]>('/versions/apk')
    return response.data
  }

  async getLatestVersion(channel: string): Promise<APKVersion> {
    const response = await this.client.get<APKVersion>('/versions/apk/latest', {
      params: { channel },
    })
    return response.data
  }

  async getVersion(id: string): Promise<APKVersion> {
    const response = await this.client.get<APKVersion>(`/versions/apk/${id}`)
    return response.data
  }

  async createVersion(data: {
    version_name: string
    version_code: number
    channel: string
    changelog?: string
    release_notes?: string
    min_app_version?: string
    is_mandatory: boolean
    file: File
    bundle_id?: string
  }): Promise<APKVersion> {
    const formData = new FormData()
    formData.append('version_name', data.version_name)
    formData.append('version_code', String(data.version_code))
    formData.append('channel', data.channel)
    formData.append('is_mandatory', String(data.is_mandatory))
    if (data.changelog) formData.append('changelog', data.changelog)
    if (data.release_notes) formData.append('release_notes', data.release_notes)
    if (data.min_app_version) formData.append('min_app_version', data.min_app_version)
    if (data.bundle_id) formData.append('bundle_id', data.bundle_id)
    formData.append('file', data.file)

    const response = await this.client.post<APKVersion>('/versions/apk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000, // 10 minutes pour gros APK
    })
    return response.data
  }

  async updateVersion(id: string, data: Partial<Pick<APKVersion, 'channel' | 'changelog' | 'is_active' | 'is_mandatory'>>): Promise<APKVersion> {
    const response = await this.client.put<APKVersion>(`/versions/apk/${id}`, data)
    return response.data
  }

  async publishVersion(id: string, isActive: boolean): Promise<APKVersion> {
    const response = await this.client.post<APKVersion>(`/versions/apk/${id}/publish`, {
      is_active: isActive,
    })
    return response.data
  }

  async rollbackVersion(targetVersionCode: number): Promise<APKVersion> {
    const response = await this.client.post<APKVersion>('/versions/apk/rollback', {
      target_version_code: targetVersionCode,
    })
    return response.data
  }

  async deleteVersion(id: string): Promise<void> {
    await this.client.delete(`/versions/apk/${id}`)
  }

  async getBundles(): Promise<HologramBundle[]> {
    const response = await this.client.get<HologramBundle[]>('/versions/bundles')
    return response.data
  }

  async createBundle(data: { version: string; description?: string; file: File }): Promise<HologramBundle> {
    const formData = new FormData()
    formData.append('version', data.version)
    if (data.description) formData.append('description', data.description)
    formData.append('file', data.file)

    const response = await this.client.post<HologramBundle>('/versions/bundles', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    })
    return response.data
  }

  // Public : vérification de mise à jour (utilisé par l'app mobile)
  async checkUpdate(currentVersionCode: number, currentVersionName: string, channel: string): Promise<VersionCheckResponse> {
    const response = await this.client.post<VersionCheckResponse>('/versions/check-update', {
      current_version_code: currentVersionCode,
      current_version_name: currentVersionName,
      channel,
    })
    return response.data
  }

  async getWebhookLogs(): Promise<WebhookLog[]> {
    const response = await this.client.get<WebhookLog[]>('/versions/webhooks/logs')
    return response.data
  }

  async retryWebhook(logId: string): Promise<WebhookLog> {
    const response = await this.client.post<WebhookLog>(`/versions/webhooks/retry/${logId}`)
    return response.data
  }

  // ──────────────────────────────────────────────
  // Admin
  // ──────────────────────────────────────────────
  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/admin/health')
    return response.data
  }

  async getHealthLive(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/admin/health/live')
    return response.data
  }

  async getConfigs(): Promise<SystemConfig[]> {
    const response = await this.client.get<SystemConfig[]>('/admin/config')
    return response.data
  }

  async updateConfig(key: string, value: unknown): Promise<SystemConfig> {
    const response = await this.client.put<SystemConfig>(`/admin/config/${key}`, { value })
    return response.data
  }

  async initDefaultConfigs(): Promise<void> {
    await this.client.post('/admin/config/init-defaults')
  }

  async getAuditLogs(filters: AuditFilters = {}): Promise<AuditSearchResponse> {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value))
      }
    })
    const response = await this.client.get<AuditSearchResponse>(`/admin/audit?${params.toString()}`)
    return response.data
  }

  async getAuditStats(): Promise<AuditStats> {
    const response = await this.client.get<AuditStats>('/admin/audit/stats')
    return response.data
  }

  async createBackup(name?: string): Promise<BackupInfo> {
    const response = await this.client.post<BackupInfo>('/admin/backups', { name })
    return response.data
  }

  async getBackups(): Promise<BackupInfo[]> {
    const response = await this.client.get<BackupInfo[]>('/admin/backups')
    return response.data
  }

  async getMetricsSummary(): Promise<MetricsSummary> {
    const response = await this.client.get<MetricsSummary>('/admin/metrics/summary')
    return response.data
  }

  // ──────────────────────────────────────────────
  // Admin Users
  // ──────────────────────────────────────────────
  async getAdminUsers(): Promise<import('../types').AdminUserResponse[]> {
    const response = await this.client.get<import('../types').AdminUserResponse[]>('/admin/users')
    return response.data
  }

  async createAdminUser(data: {
    email: string
    password: string
    first_name: string
    last_name: string
    role: 'admin' | 'validator'
  }): Promise<import('../types').AdminUserResponse> {
    const response = await this.client.post<import('../types').AdminUserResponse>('/admin/users', data)
    return response.data
  }

  async updateAdminUser(id: string, data: Partial<import('../types').AdminUserResponse>): Promise<import('../types').AdminUserResponse> {
    const response = await this.client.put<import('../types').AdminUserResponse>(`/admin/users/${id}`, data)
    return response.data
  }
}

export const api = new ApiService()