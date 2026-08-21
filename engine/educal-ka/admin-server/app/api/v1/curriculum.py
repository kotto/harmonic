# ──────────────────────────────────────────────
# API Programme — unités éducatives & versionnage
# (jumeau de Versions médicales : versionne les leçons publiées)
# ──────────────────────────────────────────────
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.api.deps import require_permission
from app.core.security import Permission
from app.models import CurriculumUnit, UnitStatus, User
from app.schemas import UnitResponse

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

# Chemin du moteur KA (engine/) pour lire le catalogue des unités
# Détection robuste : remonte jusqu'au dossier contenant hologram_store.py
_ENGINE_DIR = None
for _p in Path(__file__).resolve().parents:
    if (_p / "hologram_store.py").exists():
        _ENGINE_DIR = _p
        break
if _ENGINE_DIR is None:
    _ENGINE_DIR = Path(__file__).resolve().parents[5]
if settings.engine_dir:
    _ENGINE_DIR = Path(settings.engine_dir)


def _engine_units() -> list[dict]:
    """Catalogue des unités éducatives du moteur KA (educal_units)."""
    try:
        if str(_ENGINE_DIR) not in sys.path:
            sys.path.insert(0, str(_ENGINE_DIR))
        import educal_units  # type: ignore
        return educal_units.list_units()
    except Exception:
        return []


@router.get("/units", response_model=list[UnitResponse])
async def list_units(
    discipline: str | None = None,
    niveau: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CurriculumUnit).order_by(CurriculumUnit.discipline, CurriculumUnit.niveau)
    if discipline:
        stmt = stmt.where(CurriculumUnit.discipline == discipline)
    if niveau:
        stmt = stmt.where(CurriculumUnit.niveau == niveau)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/sync", response_model=dict)
async def sync_curriculum(
    admin: User = Depends(require_permission(Permission.MANAGE_UNITS)),
    db: AsyncSession = Depends(get_db),
):
    """Importe (ou met à jour) le catalogue des unités depuis le moteur KA.
    Versionnage : toute unité modifiée côté moteur incrémente sa version ici."""
    engine_units = _engine_units()
    if not engine_units:
        raise HTTPException(status_code=503, detail="Moteur KA injoignable (educal_units introuvable)")

    imported = updated = 0
    for u in engine_units:
        existing = await db.scalar(
            select(CurriculumUnit).where(CurriculumUnit.unit_id == u["id"])
        )
        payload = {
            "discipline": u.get("discipline", ""),
            "niveau": u.get("niveau", ""),
            "programme": u.get("programme", ""),
            "titre": u.get("titre", ""),
            "facts_count": u.get("nb_faits", 0),
            "hologramme_associe": u.get("hologramme"),
        }
        if existing is None:
            db.add(CurriculumUnit(unit_id=u["id"], version=1, **payload))
            imported += 1
        else:
            # Versionnage : toute modification du contenu moteur → version+
            if (existing.titre != payload["titre"]
                    or existing.facts_count != payload["facts_count"]):
                existing.version += 1
                existing.updated_at = datetime.now(timezone.utc)
            existing.discipline = payload["discipline"]
            existing.niveau = payload["niveau"]
            existing.programme = payload["programme"]
            existing.titre = payload["titre"]
            existing.facts_count = payload["facts_count"]
            existing.hologramme_associe = payload["hologramme_associe"]
            updated += 1

    await db.commit()
    total = await db.scalar(
        select(func.count()).select_from(CurriculumUnit)
        .where(CurriculumUnit.status == UnitStatus.PUBLISHED)
    )
    return {"synced": True, "imported": imported, "updated": updated,
            "catalogue_engine": len(engine_units), "publiees": total or 0}


@router.post("/units/{unit_id}/publish", response_model=UnitResponse)
async def set_unit_status(
    unit_id: str,
    action: str = "publish",  # publish | archive
    admin: User = Depends(require_permission(Permission.MANAGE_UNITS)),
    db: AsyncSession = Depends(get_db),
):
    unit = await db.scalar(select(CurriculumUnit).where(CurriculumUnit.unit_id == unit_id))
    if not unit:
        raise HTTPException(status_code=404, detail="Unité introuvable au programme")
    unit.status = UnitStatus.PUBLISHED if action == "publish" else UnitStatus.ARCHIVED
    await db.commit()
    await db.refresh(unit)
    return unit
