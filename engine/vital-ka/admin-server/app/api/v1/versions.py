# ──────────────────────────────────────────────
# API Versions - APK, Bundles, Webhooks, Rollback
# ──────────────────────────────────────────────
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
)
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    get_db, get_current_user, get_optional_user, require_permission,
    get_client_info, log_audit, ClientInfo
)
from app.core.security import Role, Permission
from app.models import APKVersion, HologramBundle, WebhookLog, SystemConfig, ReleaseChannel, User
from app.schemas import (
    APKVersionCreateRequest, APKVersionUpdateRequest, APKVersionRollbackRequest,
    APKVersionResponse, APKVersionListResponse,
    HologramBundleCreateRequest, HologramBundleResponse, HologramBundleListResponse,
    WebhookLogResponse, WebhookConfigRequest,
    VersionCheckRequest, VersionCheckResponse,
    BundleCheckResponse,
)
from app.services.storage_service import storage_service
from app.services.email_service import email_service
from app.tasks.version_tasks import trigger_webhooks
from app.tasks.build_tasks import build_apk_task
from app.core.config import settings


router = APIRouter(prefix="/versions", tags=["Versions"])


# ──────────────────────────────────────────────
# PUBLIC: Vérification MAJ (App Mobile)
# ──────────────────────────────────────────────
@router.post("/check-update", response_model=VersionCheckResponse)
async def check_app_update(
    data: VersionCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """Vérifier MAJ disponible (public, depuis app mobile)"""
    # Trouver dernière version active pour le canal
    query = select(APKVersion).where(
        APKVersion.channel == data.channel,
        APKVersion.is_active == True,
        APKVersion.version_code > data.current_version_code,
    ).order_by(APKVersion.version_code.desc())

    result = await db.execute(query)
    latest = result.scalar_one_or_none()

    if not latest:
        return VersionCheckResponse(
            has_update=False,
            message="Aucune mise à jour disponible",
        )

    # Générer URL signée pour téléchargement
    download_url = await storage_service.get_presigned_url(
        latest.apk_file_path, expires_in=3600
    )

    return VersionCheckResponse(
        has_update=True,
        latest_version=APKVersionListResponse.model_validate(latest),
        download_url=download_url,
        is_mandatory=latest.is_mandatory,
        message=f"Version {latest.version_name} disponible",
    )


@router.post("/check-bundle", response_model=BundleCheckResponse)
async def check_bundle_update(
    current_version: str = Query(..., description="Version bundle actuelle (ex: 2024.12.01)"),
    db: AsyncSession = Depends(get_db),
):
    """Vérifier mise à jour bundle hologrammes (public)"""
    query = select(HologramBundle).where(
        HologramBundle.is_active == True,
        HologramBundle.version > current_version,
    ).order_by(HologramBundle.version.desc())

    result = await db.execute(query)
    latest = result.scalar_one_or_none()

    if not latest:
        return BundleCheckResponse(
            has_update=False,
            message="Bundle hologrammes à jour",
        )

    download_url = await storage_service.get_presigned_url(
        latest.bundle_file_path, expires_in=3600
    )

    return BundleCheckResponse(
        has_update=True,
        latest_bundle=HologramBundleListResponse.model_validate(latest),
        download_url=download_url,
        message=f"Bundle {latest.version} disponible",
    )


# ──────────────────────────────────────────────
# ADMIN: Gestion Versions APK
# ──────────────────────────────────────────────
@router.post("/apk", response_model=APKVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_apk_version(
    version_name: str = Form(...),
    version_code: int = Form(...),
    channel: ReleaseChannel = Form(ReleaseChannel.STABLE),
    changelog: Optional[str] = Form(None),
    release_notes: Optional[str] = Form(None),
    min_app_version: Optional[str] = Form(None),
    is_mandatory: bool = Form(False),
    build_number: Optional[int] = Form(None),
    git_commit: Optional[str] = Form(None),
    git_branch: Optional[str] = Form(None),
    bundle_id: Optional[UUID] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(Permission.VERSION_CREATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Upload nouvelle version APK"""
    from app.core.config import settings
    
    if not settings.enable_version_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Upload versions désactivé",
        )

    # Vérifier version_code unique
    existing = await db.execute(
        select(APKVersion).where(APKVersion.version_code == version_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version code {version_code} déjà existant",
        )

    # Vérifier version_name unique
    existing = await db.execute(
        select(APKVersion).where(APKVersion.version_name == version_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version name {version_name} déjà existant",
        )

    # Vérifier bundle si fourni
    if bundle_id:
        bundle_result = await db.execute(
            select(HologramBundle).where(HologramBundle.id == bundle_id)
        )
        if not bundle_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bundle hologrammes non trouvé",
            )

    # Vérifier type MIME APK
    if file.content_type != "application/vnd.android.package-archive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier doit être un APK",
        )

    # Vérifier taille
    max_size = settings.storage.max_apk_size_mb * 1024 * 1024 if hasattr(settings, 'storage') else 100 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"APK trop volumineux (max {max_size // (1024*1024)}MB)",
        )

    # Calculer SHA256
    import hashlib
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Upload vers MinIO
    file_path = f"apk/{version_name}/{file.filename}"
    await storage_service.upload_file(file_path, content, file.content_type)

    # Créer entrée en base
    version = APKVersion(
        version_name=version_name,
        version_code=version_code,
        channel=channel,
        apk_file_path=file_path,
        apk_file_size=len(content),
        apk_sha256=sha256_hash,
        bundle_id=bundle_id,
        changelog=changelog,
        release_notes=release_notes,
        min_app_version=min_app_version,
        is_mandatory=is_mandatory,
        build_number=build_number,
        git_commit=git_commit,
        git_branch=git_branch,
        built_by=current_user.id,
        built_at=datetime.now(timezone.utc),
    )
    db.add(version)

    await log_audit(
        db, "version.apk_upload", "apk_version", version.id,
        user=current_user, client=client,
        new_values={
            "version_name": version_name,
            "version_code": version_code,
            "channel": channel.value,
            "file_size": len(content),
        },
        success=True,
    )

    await db.commit()
    await db.refresh(version)

    # Déclencher webhooks async
    if channel == ReleaseChannel.STABLE:
        trigger_webhooks.delay(str(version.id), "version_published")

    return version


@router.get("/apk", response_model=list[APKVersionListResponse])
async def list_apk_versions(
    channel: Optional[ReleaseChannel] = None,
    active_only: bool = True,
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Lister versions APK"""
    query = select(APKVersion)

    if channel:
        query = query.where(APKVersion.channel == channel)
    if active_only:
        query = query.where(APKVersion.is_active == True)

    query = query.order_by(APKVersion.version_code.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/apk/latest", response_model=APKVersionResponse)
async def get_latest_apk_version(
    channel: ReleaseChannel = Query(ReleaseChannel.STABLE),
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Dernière version APK pour un canal"""
    result = await db.execute(
        select(APKVersion).where(
            APKVersion.channel == channel,
            APKVersion.is_active == True,
        ).order_by(APKVersion.version_code.desc())
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Aucune version trouvée")
    return version


@router.get("/apk/{version_id}", response_model=APKVersionResponse)
async def get_apk_version(
    version_id: UUID,
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Détail version APK"""
    result = await db.execute(
        select(APKVersion).options(selectinload(APKVersion.bundle))
        .where(APKVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version non trouvée")
    return version


@router.put("/apk/{version_id}", response_model=APKVersionResponse)
async def update_apk_version(
    version_id: UUID,
    data: APKVersionUpdateRequest,
    current_user: User = Depends(require_permission(Permission.VERSION_UPDATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Mettre à jour métadonnées version APK"""
    result = await db.execute(select(APKVersion).where(APKVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version non trouvée")

    old_values = {
        "channel": version.channel.value,
        "is_active": version.is_active,
        "is_mandatory": version.is_mandatory,
        "changelog": version.changelog,
    }

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(version, field, value)

    await log_audit(
        db, "version.apk_update", "apk_version", version.id,
        user=current_user, client=client,
        old_values=old_values,
        new_values=update_data,
        success=True,
    )

    await db.commit()
    await db.refresh(version)
    return version


@router.post("/apk/{version_id}/publish", response_model=APKVersionResponse)
async def publish_apk_version(
    version_id: UUID,
    current_user: User = Depends(require_permission(Permission.VERSION_UPDATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Publier version (rendre active + webhooks)"""
    result = await db.execute(select(APKVersion).where(APKVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version non trouvée")

    if version.is_active:
        raise HTTPException(status_code=400, detail="Déjà publiée")

    # Désactiver autres versions du même canal
    await db.execute(
        select(APKVersion).where(
            APKVersion.channel == version.channel,
            APKVersion.is_active == True,
            APKVersion.id != version_id,
        ).update({"is_active": False})
    )

    version.is_active = True
    version.published_at = datetime.now(timezone.utc)

    await log_audit(
        db, "version.apk_publish", "apk_version", version.id,
        user=current_user, client=client,
        new_values={"is_active": True, "published_at": version.published_at.isoformat()},
        success=True,
    )

    await db.commit()
    await db.refresh(version)

    # Webhooks
    trigger_webhooks.delay(str(version.id), "version_published")

    return version


@router.post("/apk/rollback", response_model=APKVersionResponse)
async def rollback_apk_version(
    data: APKVersionRollbackRequest,
    current_user: User = Depends(require_permission(Permission.VERSION_ROLLBACK)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Rollback vers version précédente"""
    # Trouver version cible
    target_result = await db.execute(
        select(APKVersion).where(
            APKVersion.version_code == data.target_version_code,
            APKVersion.channel == ReleaseChannel.STABLE,  # Rollback seulement stable
        )
    )
    target_version = target_result.scalar_one_or_none()
    if not target_version:
        raise HTTPException(status_code=404, detail="Version cible non trouvée")

    # Trouver version actuellement active
    current_result = await db.execute(
        select(APKVersion).where(
            APKVersion.channel == ReleaseChannel.STABLE,
            APKVersion.is_active == True,
        )
    )
    current_version = current_result.scalar_one_or_none()

    # Désactiver version actuelle
    if current_version:
        current_version.is_active = False
        current_version.deprecated_at = datetime.now(timezone.utc)

    # Activer version cible
    target_version.is_active = True
    target_version.published_at = datetime.now(timezone.utc)

    await log_audit(
        db, "version.apk_rollback", "apk_version", target_version.id,
        user=current_user, client=client,
        new_values={
            "target_version_code": data.target_version_code,
            "reason": data.reason,
            "previous_version": current_version.version_name if current_version else None,
        },
        success=True,
    )

    await db.commit()
    await db.refresh(target_version)

    # Webhooks
    trigger_webhooks.delay(str(target_version.id), "version_rollback")

    return target_version


@router.delete("/apk/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apk_version(
    version_id: UUID,
    current_user: User = Depends(require_permission(Permission.VERSION_DELETE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Supprimer version APK (soft delete - désactive)"""
    result = await db.execute(select(APKVersion).where(APKVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version non trouvée")

    if version.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer version active. Désactivez-la d'abord.",
        )

    version.is_active = False
    version.deprecated_at = datetime.now(timezone.utc)

    await log_audit(
        db, "version.apk_delete", "apk_version", version.id,
        user=current_user, client=client,
        success=True,
    )

    await db.commit()


# ──────────────────────────────────────────────
# ADMIN: Gestion Bundles Hologrammes
# ──────────────────────────────────────────────
@router.post("/bundles", response_model=HologramBundleResponse, status_code=status.HTTP_201_CREATED)
async def create_hologram_bundle(
    version: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(Permission.VERSION_CREATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Upload nouveau bundle hologrammes"""
    from app.core.config import settings
    
    if not settings.enable_version_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Upload bundles désactivé",
        )

    # Vérifier version unique
    existing = await db.execute(
        select(HologramBundle).where(HologramBundle.version == version)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bundle version {version} déjà existant",
        )

    # Vérifier type MIME (JSON)
    if file.content_type not in ("application/json", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier doit être un JSON",
        )

    # Vérifier taille
    max_size = settings.storage.max_bundle_size_mb * 1024 * 1024 if hasattr(settings, 'storage') else 500 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bundle trop volumineux (max {max_size // (1024*1024)}MB)",
        )

    # Calculer SHA256
    import hashlib
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Parser JSON pour métadonnées
    import json
    try:
        bundle_data = json.loads(content)
        domains_count = len(bundle_data.get("domains", {}))
        facts_count = sum(len(v) for v in bundle_data.get("domains", {}).values())
        pathologies_count = bundle_data.get("pathologies_count", 0)
    except Exception:
        domains_count = facts_count = pathologies_count = 0

    # Upload vers MinIO
    file_path = f"bundles/{version}/{file.filename}"
    await storage_service.upload_file(file_path, content, file.content_type)

    # Créer entrée en base
    bundle = HologramBundle(
        version=version,
        description=description,
        bundle_file_path=file_path,
        bundle_file_size=len(content),
        bundle_sha256=sha256_hash,
        domains_count=domains_count,
        facts_count=facts_count,
        pathologies_count=pathologies_count,
        metadata=bundle_data.get("metadata") if 'bundle_data' in locals() else None,
        built_by=current_user.id,
        built_at=datetime.now(timezone.utc),
    )
    db.add(bundle)

    await log_audit(
        db, "version.bundle_upload", "hologram_bundle", bundle.id,
        user=current_user, client=client,
        new_values={
            "version": version,
            "file_size": len(content),
            "domains": domains_count,
            "facts": facts_count,
        },
        success=True,
    )

    await db.commit()
    await db.refresh(bundle)

    return bundle


@router.get("/bundles", response_model=list[HologramBundleListResponse])
async def list_hologram_bundles(
    active_only: bool = True,
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Lister bundles hologrammes"""
    query = select(HologramBundle)
    if active_only:
        query = query.where(HologramBundle.is_active == True)
    query = query.order_by(HologramBundle.version.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/bundles/latest", response_model=HologramBundleResponse)
async def get_latest_bundle(
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Dernier bundle hologrammes"""
    result = await db.execute(
        select(HologramBundle).where(HologramBundle.is_active == True)
        .order_by(HologramBundle.version.desc())
    )
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Aucun bundle trouvé")
    return bundle


@router.post("/bundles/{bundle_id}/publish", response_model=HologramBundleResponse)
async def publish_hologram_bundle(
    bundle_id: UUID,
    current_user: User = Depends(require_permission(Permission.VERSION_UPDATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Publier bundle"""
    result = await db.execute(select(HologramBundle).where(HologramBundle.id == bundle_id))
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle non trouvé")

    if bundle.is_active:
        raise HTTPException(status_code=400, detail="Déjà publié")

    # Désactiver autres bundles
    await db.execute(
        select(HologramBundle).where(
            HologramBundle.is_active == True,
            HologramBundle.id != bundle_id,
        ).update({"is_active": False})
    )

    bundle.is_active = True
    bundle.published_at = datetime.now(timezone.utc)

    await log_audit(
        db, "version.bundle_publish", "hologram_bundle", bundle.id,
        user=current_user, client=client,
        new_values={"is_active": True},
        success=True,
    )

    await db.commit()
    await db.refresh(bundle)

    # Webhooks
    trigger_webhooks.delay(str(bundle.id), "bundle_published")

    return bundle


@router.get("/bundles/{bundle_id}/download")
async def download_bundle(
    bundle_id: UUID,
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Télécharger bundle (URL signée)"""
    result = await db.execute(select(HologramBundle).where(HologramBundle.id == bundle_id))
    bundle = result.scalar_one_or_none()
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle non trouvé")

    url = await storage_service.get_presigned_url(bundle.bundle_file_path, expires_in=3600)
    return {"url": url, "expires_in": 3600}


# ──────────────────────────────────────────────
# ADMIN: Webhooks
# ──────────────────────────────────────────────
@router.get("/webhooks/logs", response_model=list[WebhookLogResponse])
async def list_webhook_logs(
    version_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = Query(100, le=500),
    current_user: User = Depends(require_permission(Permission.VERSION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Logs webhooks"""
    query = select(WebhookLog).order_by(WebhookLog.created_at.desc())

    if version_id:
        query = query.where(WebhookLog.version_id == version_id)
    if event_type:
        query = query.where(WebhookLog.event_type == event_type)
    if success is not None:
        query = query.where(WebhookLog.success == success)

    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/webhooks/retry/{log_id}")
async def retry_webhook(
    log_id: UUID,
    current_user: User = Depends(require_permission(Permission.VERSION_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Réessayer webhook échoué"""
    result = await db.execute(select(WebhookLog).where(WebhookLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Log webhook non trouvé")

    if log.success:
        raise HTTPException(status_code=400, detail="Webhook déjà réussi")

    # Réessayer
    log.attempt += 1
    await db.commit()

    # Déclencher retry async
    from app.tasks.version_tasks import send_webhook
    send_webhook.delay(str(log.id))

    return {"message": "Retry déclenché", "attempt": log.attempt}