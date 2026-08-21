# ──────────────────────────────────────────────
# Configuration Centralisée (Pydantic Settings)
# ──────────────────────────────────────────────
from functools import lru_cache
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
    jwt_secret_key: str = "educal-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h (session élève)

    # ──────────────────────────────────────────────
    # Base de données — SQLite local par défaut
    # ──────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./educal.db"

    # ──────────────────────────────────────────────
    # CORS
    # ──────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8001"]

    # ──────────────────────────────────────────────
    # Logging
    # ──────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "console"  # json ou console

    # ──────────────────────────────────────────────
    # Écosystème : moteur KA (catalogue des unités éducatives)
    # ──────────────────────────────────────────────
    engine_dir: str | None = None  # détecté automatiquement sinon

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
