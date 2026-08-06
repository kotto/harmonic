# ──────────────────────────────────────────────
# Configuration Centralisée (Pydantic Settings)
# ──────────────────────────────────────────────
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ──────────────────────────────────────────────
    # Sécurité / JWT
    # ──────────────────────────────────────────────
    jwt_secret_key: str = Field(..., description="Clé secrète JWT (openssl rand -hex 32)")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ──────────────────────────────────────────────
    # Base de données
    # ──────────────────────────────────────────────
    # Mode local (défaut) : SQLite fichier — démarrage sans infrastructure.
    # Production : PostgreSQL asyncpg (ex: postgresql+asyncpg://user:pass@host/db)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./ka_vital.db",
        description="URL de base de données (PostgreSQL asyncpg en production, SQLite en local)",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ──────────────────────────────────────────────
    # Redis
    # ──────────────────────────────────────────────
    redis_url: str = Field(default=None, description="URL Redis (optionnel en local)")
    redis_max_connections: int = 50

    # ──────────────────────────────────────────────
    # MinIO / S3
    # ──────────────────────────────────────────────
    minio_endpoint: str = Field(default=None, description="Endpoint MinIO (host:port)")
    minio_access_key: str = Field(default=None, description="Access Key MinIO")
    minio_secret_key: str = Field(default=None, description="Secret Key MinIO")
    minio_bucket: str = "assets"
    minio_secure: bool = False  # True en prod avec TLS

    # ──────────────────────────────────────────────
    # Email (SMTP)
    # ──────────────────────────────────────────────
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "noreply@vitalka.local"
    smtp_use_tls: bool = True

    # ──────────────────────────────────────────────
    # Frontend / CORS
    # ──────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ──────────────────────────────────────────────
    # Projet Android (build APK)
    # ──────────────────────────────────────────────
    android_project_path: str = "/vital-ka/android"

    # ──────────────────────────────────────────────
    # Logging
    # ──────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"  # json ou console

    # ──────────────────────────────────────────────
    # Monitoring
    # ──────────────────────────────────────────────
    prometheus_metrics_enabled: bool = True
    metrics_port: int = 9090

    # ──────────────────────────────────────────────
    # Feature Flags (config runtime)
    # ──────────────────────────────────────────────
    enable_doctor_registration: bool = True
    enable_version_upload: bool = True
    enable_public_api: bool = False

    # ──────────────────────────────────────────────
    # Pagination
    # ──────────────────────────────────────────────
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()