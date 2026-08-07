# ──────────────────────────────────────────────
# API Admin - Health, Config, Audit, Backups
# ──────────────────────────────────────────────
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta

from fastapi import (
    APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
)
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db, get_current_user, require_permission, get_client_info,
    log_audit, ClientInfo
)
from app.core.security import Permission, Role
from app.models import (
    User, Doctor, APKVersion, HologramBundle, SystemConfig, AuditLog,
    UserRole, UserStatus, DoctorStatus, DEFAULT_CONFIGS
)
from app.schemas import (
    HealthResponse, ComponentHealth, ServiceHealth,
    SystemConfigUpdate, SystemConfigResponse, SystemConfigBulkUpdate,
    AuditLogFilters, AuditLogResponse, AuditSearchResponse,
    BackupInfo, BackupTriggerRequest, BackupStatus,
    MetricsSummary, AdminUserCreateRequest, AdminUserUpdateRequest, AdminUserResponse,
)
from app.services.storage_service import storage_service
from app.tasks.backup_tasks import create_backup_task
from app.core.config import settings


router = APIRouter(prefix="/admin", tags=["Admin"])


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    """Health check complet (public pour load balancer)"""
    import time
    start = time.time()

    components = []
    overall_status = ServiceHealth.HEALTHY

    # Database
    db_start = time.time()
    try:
        await db.execute(select(1))
        db_latency = (time.time() - db_start) * 1000
        components.append(ComponentHealth(
            name="database",
            status=ServiceHealth.HEALTHY,
            latency_ms=db_latency,
            details={"pool_size": 10},
        ))
    except Exception as e:
        components.append(ComponentHealth(
            name="database",
            status=ServiceHealth.UNHEALTHY,
            details={"error": str(e)},
        ))
        overall_status = ServiceHealth.UNHEALTHY

    # Redis
    redis_start = time.time()
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        redis_latency = (time.time() - redis_start) * 1000
        components.append(ComponentHealth(
            name="redis",
            status=ServiceHealth.HEALTHY,
            latency_ms=redis_latency,
        ))
    except Exception as e:
        components.append(ComponentHealth(
            name="redis",
            status=ServiceHealth.UNHEALTHY,
            details={"error": str(e)},
        ))
        overall_status = ServiceHealth.DEGRADED if overall_status == ServiceHealth.HEALTHY else overall_status

    # MinIO
    minio_start = time.time()
    try:
        await storage_service.health_check()
        minio_latency = (time.time() - minio_start) * 1000
        components.append(ComponentHealth(
            name="minio",
            status=ServiceHealth.HEALTHY,
            latency_ms=minio_latency,
        ))
    except Exception as e:
        components.append(ComponentHealth(
            name="minio",
            status=ServiceHealth.DEGRADED,
            details={"error": str(e)},
        ))
        overall_status = ServiceHealth.DEGRADED if overall_status == ServiceHealth.HEALTHY else overall_status

    # Backends Python (optionnel)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            for name, url in [
                ("voice", "http://voice-backend:8001/health"),
                ("hologram", "http://hologram-backend:8002/health"),
                ("inference", "http://inference-backend:8003/health"),
            ]:
                try:
                    resp = await client.get(url)
                    components.append(ComponentHealth(
                        name=name,
                        status=ServiceHealth.HEALTHY if resp.status_code == 200 else ServiceHealth.DEGRADED,
                    ))
                except Exception:
                    components.append(ComponentHealth(
                        name=name,
                        status=ServiceHealth.DEGRADED,
                    ))
    except Exception:
        pass

    uptime = time.time() - start

    return HealthResponse(
        status=overall_status,
        version=settings.app.version if hasattr(settings, 'app') else "2.1.0",
        timestamp=datetime.now(timezone.utc),
        components=components,
        uptime_seconds=uptime,
    )


@router.get("/health/live")
async def liveness():
    """Liveness probe (Kubernetes)"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe (Kubernetes)"""
    try:
        await db.execute(select(1))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")


# ──────────────────────────────────────────────
# System Config
# ──────────────────────────────────────────────
@router.get("/config", response_model=list[SystemConfigResponse])
async def list_config(
    category: Optional[str] = None,
    public_only: bool = False,
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Lister configuration système"""
    query = select(SystemConfig)
    if category:
        query = query.where(SystemConfig.category == category)
    if public_only:
        query = query.where(SystemConfig.is_public == True)

    query = query.order_by(SystemConfig.category, SystemConfig.key)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/config/{key}", response_model=SystemConfigResponse)
async def get_config(
    key: str,
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Obtenir une config"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.put("/config/{key}", response_model=SystemConfigResponse)
async def update_config(
    key: str,
    data: SystemConfigUpdate,
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_WRITE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Mettre à jour configuration"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    config = result.scalar_one_or_none()

    old_values = {"value": config.value} if config else None

    if config:
        # Valider schema si présent
        if config.schema:
            # TODO: validation JSON Schema
            pass
        config.value = data.value
        config.updated_by = current_user.id
        config.updated_at = datetime.now(timezone.utc)
    else:
        # Créer nouvelle config
        config = SystemConfig(
            key=key,
            value=data.value,
            updated_by=current_user.id,
        )
        db.add(config)

    await log_audit(
        db, "admin.config_update", "config", None,
        user=current_user, client=client,
        old_values=old_values,
        new_values={"value": data.value, "key": key},
        success=True,
    )

    await db.commit()
    await db.refresh(config)
    return config


@router.post("/config/bulk", response_model=list[SystemConfigResponse])
async def bulk_update_config(
    data: SystemConfigBulkUpdate,
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_WRITE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Mise à jour multiple configs"""
    updated = []
    for key, value in data.configs.items():
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalar_one_or_none()

        if config:
            config.value = value
            config.updated_by = current_user.id
            config.updated_at = datetime.now(timezone.utc)
        else:
            config = SystemConfig(key=key, value=value, updated_by=current_user.id)
            db.add(config)

        updated.append(config)

    await log_audit(
        db, "admin.config_bulk_update", "config", None,
        user=current_user, client=client,
        new_values=data.configs,
        success=True,
    )

    await db.commit()
    for c in updated:
        await db.refresh(c)
    return updated


@router.post("/config/init-defaults")
async def init_default_configs(
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Initialiser configs par défaut"""
    created = 0
    for key, cfg in DEFAULT_CONFIGS.items():
        existing = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        if not existing.scalar_one_or_none():
            config = SystemConfig(
                key=key,
                value=cfg["value"],
                description=cfg["description"],
                category=cfg["category"],
                is_public=cfg.get("is_public", False),
                is_sensitive=cfg.get("is_sensitive", False),
                schema=cfg.get("schema"),
            )
            db.add(config)
            created += 1

    await db.commit()
    return {"created": created, "message": f"{created} configurations par défaut créées"}


# ──────────────────────────────────────────────
# Audit Logs
# ──────────────────────────────────────────────
@router.get("/audit", response_model=AuditSearchResponse)
async def search_audit_logs(
    filters: AuditLogFilters = Depends(),
    current_user: User = Depends(require_permission(Permission.ADMIN_AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Recherche logs d'audit"""
    query = select(AuditLog)

    conditions = []
    if filters.user_id:
        conditions.append(AuditLog.user_id == filters.user_id)
    if filters.action:
        conditions.append(AuditLog.action.ilike(f"%{filters.action}%"))
    if filters.resource_type:
        conditions.append(AuditLog.resource_type == filters.resource_type)
    if filters.resource_id:
        conditions.append(AuditLog.resource_id == filters.resource_id)
    if filters.success is not None:
        conditions.append(AuditLog.success == filters.success)
    if filters.date_from:
        conditions.append(AuditLog.created_at >= filters.date_from)
    if filters.date_to:
        conditions.append(AuditLog.created_at <= filters.date_to)

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Pagination
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditSearchResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size,
    )


@router.get("/audit/stats")
async def audit_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_permission(Permission.ADMIN_AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Statistiques audit"""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Actions par type
    action_stats = await db.execute(
        select(AuditLog.action, func.count())
        .where(AuditLog.created_at >= since)
        .group_by(AuditLog.action)
        .order_by(func.count().desc())
        .limit(20)
    )

    # Succès/Échecs
    success_stats = await db.execute(
        select(AuditLog.success, func.count())
        .where(AuditLog.created_at >= since)
        .group_by(AuditLog.success)
    )

    # Top utilisateurs
    user_stats = await db.execute(
        select(AuditLog.user_email, func.count())
        .where(AuditLog.created_at >= since, AuditLog.user_email.is_not(None))
        .group_by(AuditLog.user_email)
        .order_by(func.count().desc())
        .limit(10)
    )

    return {
        "period_days": days,
        "by_action": dict(action_stats.all()),
        "by_success": dict(success_stats.all()),
        "top_users": dict(user_stats.all()),
    }


# ──────────────────────────────────────────────
# Backups
# ──────────────────────────────────────────────
@router.post("/backups", response_model=BackupInfo, status_code=status.HTTP_202_ACCEPTED)
async def trigger_backup(
    data: BackupTriggerRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission(Permission.ADMIN_BACKUP_CREATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Déclencher backup manuel"""
    import uuid
    backup_id = uuid.uuid4()

    backup_name = data.name or f"manual-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    # Créer entrée en base (table backups à créer si nécessaire)
    # Pour l'instant, lancer task Celery directement
    create_backup_task.delay(
        str(backup_id),
        backup_name,
        data.include_database,
        data.include_storage,
        str(current_user.id),
    )

    await log_audit(
        db, "admin.backup_trigger", "backup", backup_id,
        user=current_user, client=client,
        new_values={
            "name": backup_name,
            "include_database": data.include_database,
            "include_storage": data.include_storage,
        },
        success=True,
    )

    return BackupInfo(
        id=backup_id,
        name=backup_name,
        status=BackupStatus.PENDING,
        started_at=datetime.now(timezone.utc),
    )


@router.get("/backups", response_model=list[BackupInfo])
async def list_backups(
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_permission(Permission.ADMIN_AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Lister backups (depuis MinIO ou table)"""
    # Pour l'instant, lister depuis MinIO bucket backups
    backups = await storage_service.list_backups(limit)
    return backups


# ──────────────────────────────────────────────
# Metrics Summary (Dashboard)
# ──────────────────────────────────────────────
@router.get("/metrics/summary", response_model=MetricsSummary)
async def metrics_summary(
    current_user: User = Depends(require_permission(Permission.ADMIN_METRICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Résumé métriques pour dashboard admin"""
    # Docteurs
    total_doctors = await db.scalar(select(func.count(Doctor.id)))
    pending_doctors = await db.scalar(
        select(func.count(Doctor.id)).where(Doctor.status == DoctorStatus.PENDING)
    )
    validated_doctors = await db.scalar(
        select(func.count(Doctor.id)).where(Doctor.status == DoctorStatus.VALIDATED)
    )
    rejected_doctors = await db.scalar(
        select(func.count(Doctor.id)).where(Doctor.status == DoctorStatus.REJECTED)
    )

    # Versions
    total_apk_versions = await db.scalar(select(func.count(APKVersion.id)))
    active_apk_versions = await db.scalar(
        select(func.count(APKVersion.id)).where(APKVersion.is_active == True)
    )

    # Bundles
    total_bundles = await db.scalar(select(func.count(HologramBundle.id)))
    active_bundles = await db.scalar(
        select(func.count(HologramBundle.id)).where(HologramBundle.is_active == True)
    )

    # Storage
    storage_info = await storage_service.get_storage_usage()

    # API metrics (depuis Prometheus ou table)
    # Pour l'instant, valeurs par défaut
    api_requests_24h = 0
    avg_response_time_ms = 0.0
    error_rate_24h = 0.0

    return MetricsSummary(
        total_doctors=total_doctors or 0,
        pending_doctors=pending_doctors or 0,
        validated_doctors=validated_doctors or 0,
        rejected_doctors=rejected_doctors or 0,
        total_apk_versions=total_apk_versions or 0,
        active_apk_versions=active_apk_versions or 0,
        total_bundles=total_bundles or 0,
        active_bundles=active_bundles or 0,
        storage_used_bytes=storage_info.get("used_bytes", 0),
        storage_available_bytes=storage_info.get("available_bytes", 0),
        api_requests_24h=api_requests_24h,
        avg_response_time_ms=avg_response_time_ms,
        error_rate_24h=error_rate_24h,
    )


# ──────────────────────────────────────────────
# Admin Users Management
# ──────────────────────────────────────────────
@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    data: AdminUserCreateRequest,
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_WRITE)),  # Super admin
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Créer utilisateur admin/validator"""
    # Vérifier email unique
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
    )
    db.add(user)

    await log_audit(
        db, "admin.user_create", "user", user.id,
        user=current_user, client=client,
        new_values={"email": data.email, "role": data.role.value},
        success=True,
    )

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/users", response_model=list[AdminUserResponse])
async def list_admin_users(
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    current_user: User = Depends(require_permission(Permission.ADMIN_AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Lister utilisateurs admin"""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
    query = query.order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.ADMIN_AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Détail utilisateur admin"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: UUID,
    data: AdminUserUpdateRequest,
    current_user: User = Depends(require_permission(Permission.ADMIN_CONFIG_WRITE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Mettre à jour utilisateur admin"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Empêcher auto-modification rôle
    if user.id == current_user.id and data.role and data.role != user.role:
        raise HTTPException(status_code=400, detail="Impossible de modifier son propre rôle")

    old_values = {
        "role": user.role.value,
        "status": user.status.value,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)

    await log_audit(
        db, "admin.user_update", "user", user.id,
        user=current_user, client=client,
        old_values=old_values,
        new_values=update_data,
        success=True,
    )

    await db.commit()
    await db.refresh(user)
    return user