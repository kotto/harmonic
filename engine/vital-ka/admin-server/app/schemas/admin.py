# ──────────────────────────────────────────────
# Schémas Pydantic - Admin & Système
# ──────────────────────────────────────────────
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl


# ──────────────────────────────────────────────
# Health & Status
# ──────────────────────────────────────────────
class ServiceHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    name: str
    status: ServiceHealth
    latency_ms: Optional[float] = None
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ServiceHealth
    version: str
    timestamp: datetime
    components: list[ComponentHealth]
    uptime_seconds: float


# ──────────────────────────────────────────────
# System Config
# ──────────────────────────────────────────────
class SystemConfigUpdate(BaseModel):
    """Mise à jour configuration"""
    value: Any
    updated_by: Optional[UUID] = None


class SystemConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: Any
    description: Optional[str]
    category: str
    is_public: bool
    is_sensitive: bool
    schema: Optional[dict]
    updated_at: datetime


class SystemConfigBulkUpdate(BaseModel):
    """Mise à jour multiple configs"""
    configs: dict[str, Any]


# ──────────────────────────────────────────────
# Audit
# ──────────────────────────────────────────────
class AuditLogFilters(BaseModel):
    user_id: Optional[UUID] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    success: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID]
    user_email: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[UUID]
    old_values: Optional[dict]
    new_values: Optional[dict]
    metadata: Optional[dict] = Field(None, validation_alias="metadata_json", serialization_alias="metadata")
    success: bool
    error_message: Optional[str]
    created_at: datetime


class AuditSearchResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ──────────────────────────────────────────────
# Backups
# ──────────────────────────────────────────────
class BackupStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: BackupStatus
    size_bytes: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[dict] = Field(None, validation_alias="metadata_json", serialization_alias="metadata")


class BackupTriggerRequest(BaseModel):
    """Déclencher backup manuel"""
    name: Optional[str] = None
    include_database: bool = True
    include_storage: bool = True


# ──────────────────────────────────────────────
# Metrics (Prometheus)
# ──────────────────────────────────────────────
class MetricsSummary(BaseModel):
    """Résumé métriques pour dashboard"""
    total_doctors: int
    pending_doctors: int
    validated_doctors: int
    rejected_doctors: int
    total_apk_versions: int
    active_apk_versions: int
    total_bundles: int
    active_bundles: int
    storage_used_bytes: int
    storage_available_bytes: int
    api_requests_24h: int
    avg_response_time_ms: float
    error_rate_24h: float