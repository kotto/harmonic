// ──────────────────────────────────────────────
// Types — Contrats API réels du backend
// ──────────────────────────────────────────────

// ──────────────────────────────────────────────
// Auth & Users
// ──────────────────────────────────────────────
export type UserRole = 'admin' | 'validator'
export type UserStatus = 'active' | 'inactive' | 'locked'

export interface UserInfo {
  id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  status: UserStatus
  last_login?: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
  remember_me?: boolean
}

export interface LoginResponse {
  user: UserInfo
  tokens: TokenResponse
}

export interface AdminUserResponse {
  id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  status: UserStatus
  failed_login_attempts: number
  locked_until?: string
  last_login?: string
  totp_enabled: boolean
  created_at: string
  updated_at: string
}

// ──────────────────────────────────────────────
// Doctors & KYC
// ──────────────────────────────────────────────
export type DoctorStatus =
  | 'pending'
  | 'under_review'
  | 'validated'
  | 'rejected'
  | 'suspended'
  | 'expired'

export type KYCDocumentType =
  | 'identity'
  | 'medical_degree'
  | 'license'
  | 'specialty_cert'
  | 'proof_address'
  | 'cv'
  | 'other'

export interface KYCDocument {
  id: string
  document_type: KYCDocumentType
  file_name: string
  file_size: number
  mime_type: string
  is_verified: boolean
  verified_at?: string
  rejection_reason?: string
  created_at: string
}

export interface VerificationLog {
  id: string
  action: string
  from_status?: DoctorStatus
  to_status?: DoctorStatus
  performed_by?: string
  notes?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface Doctor {
  id: string
  email: string
  first_name: string
  last_name: string
  phone?: string
  license_number: string
  specialty?: string
  sub_specialty?: string
  years_experience?: number
  country: string
  city?: string
  practice_address?: string
  coordinates?: { lat: number; lng: number }
  status: DoctorStatus
  validated_by?: string
  validated_at?: string
  rejection_reason?: string
  is_active: boolean
  last_login?: string
  login_count: number
  created_at: string
  updated_at: string
  documents: KYCDocument[]
  verification_logs: VerificationLog[]
}

export interface DoctorListResponse {
  id: string
  email: string
  first_name: string
  last_name: string
  license_number: string
  specialty?: string
  city?: string
  country: string
  status: DoctorStatus
  validated_at?: string
  created_at: string
}

export interface DoctorSearchResponse {
  items: DoctorListResponse[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ──────────────────────────────────────────────
// Versions APK & Bundles
// ──────────────────────────────────────────────
export type ReleaseChannel = 'alpha' | 'beta' | 'stable'

export interface APKVersion {
  id: string
  version_name: string
  version_code: number
  channel: ReleaseChannel
  apk_file_path: string
  apk_file_size: number
  apk_sha256: string
  bundle_id?: string
  changelog?: string
  release_notes?: string
  min_app_version?: string
  build_number?: number
  git_commit?: string
  git_branch?: string
  built_by?: string
  built_at?: string
  is_active: boolean
  is_mandatory: boolean
  created_at: string
  published_at?: string
  deprecated_at?: string
}

export interface APKVersionListResponse {
  id: string
  version_name: string
  version_code: number
  channel: ReleaseChannel
  apk_file_size: number
  is_active: boolean
  is_mandatory: boolean
  created_at: string
  published_at?: string
}

export interface HologramBundle {
  id: string
  bundle_name: string
  version: string
  bundle_file_path: string
  bundle_file_size: number
  bundle_sha256: string
  description?: string
  is_active: boolean
  published_at?: string
  created_at: string
}

export interface VersionCheckResponse {
  has_update: boolean
  latest_version_code?: number
  latest_version_name?: string
  download_url?: string
  is_mandatory?: boolean
  changelog?: string
  channel?: ReleaseChannel
}

export interface WebhookLog {
  id: string
  webhook_url: string
  event_type: string
  status: 'pending' | 'success' | 'failed'
  attempts: number
  response_status?: number
  response_body?: string
  last_attempt_at?: string
  created_at: string
}

// ──────────────────────────────────────────────
// Admin & Système
// ──────────────────────────────────────────────
export interface ComponentHealth {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  latency_ms?: number
  details?: Record<string, unknown>
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  timestamp: string
  components: ComponentHealth[]
  uptime_seconds: number
}

export interface SystemConfig {
  key: string
  value: unknown
  description?: string
  category: string
  is_public: boolean
  is_sensitive: boolean
  schema?: Record<string, unknown>
  updated_at: string
}

export interface BackupInfo {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  size_bytes?: number
  started_at: string
  completed_at?: string
  error_message?: string
  metadata?: Record<string, unknown>
}

export interface AuditLog {
  id: string
  user_id?: string
  user_email?: string
  user_role?: string
  ip_address?: string
  user_agent?: string
  action: string
  resource_type: string
  resource_id?: string
  old_values?: Record<string, unknown>
  new_values?: Record<string, unknown>
  metadata?: Record<string, unknown>
  success: boolean
  error_message?: string
  created_at: string
}

export interface AuditSearchResponse {
  items: AuditLog[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface AuditStats {
  total_events: number
  total_success: number
  total_failed: number
  top_actions: Array<{ action: string; count: number }>
  top_users: Array<{ user_email: string; count: number }>
  actions_24h: number
}

export interface MetricsSummary {
  total_doctors: number
  pending_doctors: number
  validated_doctors: number
  rejected_doctors: number
  total_apk_versions: number
  active_apk_versions: number
  total_bundles: number
  active_bundles: number
  // champs supplémentaires (fin du fichier schéma)
  uptime_seconds?: number
  requests_24h?: number
  errors_24h?: number
}

// ──────────────────────────────────────────────
// Pagination & Filtres
// ──────────────────────────────────────────────
export interface DoctorFilters {
  page?: number
  page_size?: number
  status?: DoctorStatus
  specialty?: string
  city?: string
  country?: string
  validated_only?: boolean
  query?: string
}

export interface AuditFilters {
  page?: number
  page_size?: number
  user_id?: string
  action?: string
  resource_type?: string
  success?: boolean
  date_from?: string
  date_to?: string
}