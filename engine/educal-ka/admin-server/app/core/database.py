# ──────────────────────────────────────────────
# Base de données - SQLAlchemy Async
# ──────────────────────────────────────────────
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base pour tous les modèles SQLAlchemy"""
    pass


# Engine global (SQLite local par défaut)
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
)

# Mode local SQLite : rendre PG_UUID / JSONB compatibles (comme vital-ka)
_IS_SQLITE = (settings.database_url or "").startswith("sqlite")
if _IS_SQLITE:
    from sqlalchemy.dialects.postgresql import UUID as _PG_UUID, JSONB as _PG_JSONB
    from sqlalchemy.ext.compiler import compiles

    @compiles(_PG_UUID, "sqlite")
    def _compile_pg_uuid_sqlite(type_, compiler, **kw):
        return "CHAR(36)"

    @compiles(_PG_JSONB, "sqlite")
    def _compile_pg_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dépendance FastAPI pour obtenir une session DB"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialiser la base de données (créer tables si pas existantes)"""
    import app.models  # noqa: F401 — enregistre tous les modèles
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fermer les connexions"""
    await engine.dispose()
