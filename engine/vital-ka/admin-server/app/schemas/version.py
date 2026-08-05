# ──────────────────────────────────────────────
# Schémas Pydantic - Versions & Bundles
# ──────────────────────────────────────────────
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, HttpUrl


class ReleaseChannel(str, Enum):
    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"


# ──────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────
class APKVersionCreateRequest(BaseModel):
    """Création version APK (metadata, fichier via multipart)"""
    version_name: str = Field(..., pattern=r"^\d+\.\d+\.\d+(-.+)?$", max_length=50)
    version_code: int = Field(..., gt=0)
    channel: ReleaseChannel = ReleaseChannel.STABLE
    changelog: Optional[str] = None
    release_notes: Optional[str] = None
    min_app_version: Optional[str] = Field(None, max_length=50)
    is_mandatory: bool = False
    build_number: Optional[int] = None
    git_commit: Optional[str] = Field(None, max_length=40)
    git_branch: Optional[str] = Field(None, max_length=100)


class APKVersionUpdateRequest(BaseModel):
    """Mise à jour version APK"""
    channel: Optional[ReleaseChannel] = None
    changelog: Optional[str] = None
    release_notes: Optional[str] = None
    min_app_version: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_mandatory: Optional[bool] = None


class APKVersionRollbackRequest(BaseModel):
    """Rollback vers version précédente"""
    target_version_code: int = Field(..., gt=0)
    reason: str = Field(..., min_length=10, max_length=1000)


class HologramBundleCreateRequest(BaseModel):
    """Création bundle hologrammes (metadata, fichier via multipart)"""
    version: str = Field(..., pattern=r"^\d{4}\.\d{2}\.\d{2}$", max_length=50)
    description: Optional[str] = None


class WebhookConfigRequest(BaseModel):
    """Configuration webhook"""
    urls: list[HttpUrl]
    retry_attempts: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300)


# ──────────────────────────────────────────────
# Responses
# ──────────────────────────────────────────────
class APKVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_name: str
    version_code: int
    channel: ReleaseChannel
    apk_file_path: str
    apk_file_size: int
    apk_sha256: str
    bundle_id: Optional[UUID]
    changelog: Optional[str]
    release_notes: Optional[str]
    min_app_version: Optional[str]
    build_number: Optional[int]
    git_commit: Optional[str]
    git_branch: Optional[str]
    built_by: Optional[UUID]
    built_at: Optional[datetime]
    is_active: bool
    is_mandatory: bool
    created_at: datetime
    published_at: Optional[datetime]
    deprecated_at: Optional[datetime]


class APKVersionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_name: str
    version_code: int
    channel: ReleaseChannel
    apk_file_size: int
    is_active: bool
    is_mandatory: bool
    created_at: datetime
    published_at: Optional[datetime]


class HologramBundleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: str
    description: Optional[str]
    bundle_file_path: str
    bundle_file_size: int
    bundle_sha256: str
    domains_count: int
    facts_count: int
    pathologies_count: int
    metadata: Optional[dict] = Field(None, validation_alias="metadata_json", serialization_alias="metadata")
    built_by: Optional[UUID]
    built_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    published_at: Optional[datetime]


class HologramBundleListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: str
    bundle_file_size: int
    domains_count: int
    facts_count: int
    pathologies_count: int
    is_active: bool
    created_at: datetime
    published_at: Optional[datetime]


class WebhookLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_id: UUID
    url: str
    event_type: str
    payload: dict
    status_code: Optional[int]
    response_body: Optional[str]
    success: bool
    error_message: Optional[str]
    attempt: int
    created_at: datetime
    completed_at: Optional[datetime]


# ──────────────────────────────────────────────
# Public API (pour apps mobiles)
# ──────────────────────────────────────────────
class VersionCheckRequest(BaseModel):
    """Requête vérification MAJ (depuis app mobile)"""
    current_version_code: int = Field(..., gt=0)
    current_version_name: str = Field(..., max_length=50)
    channel: ReleaseChannel = ReleaseChannel.STABLE
    platform: str = Field(default="android", pattern="^(android|ios|web)$")
    device_id: Optional[str] = None


class VersionCheckResponse(BaseModel):
    """Réponse vérification MAJ"""
    has_update: bool
    latest_version: Optional[APKVersionListResponse] = None
    download_url: Optional[str] = None  # URL signée MinIO
    is_mandatory: bool = False
    message: Optional[str] = None


class BundleCheckResponse(BaseModel):
    """Réponse vérification bundle hologrammes"""
    has_update: bool
    latest_bundle: Optional[HologramBundleListResponse] = None
    download_url: Optional[str] = None
    message: Optional[str] = None