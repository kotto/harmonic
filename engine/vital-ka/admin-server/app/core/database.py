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


# Engine global
# SQLite ne supporte pas les kwargs de pool → on ne les passe qu'en PostgreSQL
_IS_SQLITE = (settings.database_url or "").startswith("sqlite")
_engine_kwargs = dict(echo=settings.log_level == "DEBUG")
if not _IS_SQLITE:
    _engine_kwargs.update(
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
engine: AsyncEngine = create_async_engine(settings.database_url, **_engine_kwargs)

# Mode local SQLite : rendre PG_UUID / JSONB compatibles (comme dans les tests)
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


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager pour scripts/tasks Celery"""
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
    # Import explicite : enregistre TOUS les modèles dans Base.metadata
    # (sinon create_all ne crée rien si les routes n'ont pas encore importé les modèles)
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fermer les connexions"""
    await engine.dispose()