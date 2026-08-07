# ──────────────────────────────────────────────
# Celery Configuration
# ──────────────────────────────────────────────
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


# ──────────────────────────────────────────────
# Celery App
# ──────────────────────────────────────────────
celery_app = Celery(
    "vitalka_admin",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.version_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.backup_tasks",
        "app.tasks.build_tasks",
    ],
)

# Configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # Worker
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result backend
    result_expires=3600,
    result_extended=True,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        # Nettoyage tokens blacklist toutes les heures
        "cleanup-blacklist": {
            "task": "app.tasks.maintenance.cleanup_blacklist",
            "schedule": crontab(minute=0),  # Chaque heure
        },
        # Vérifier santé backends toutes les 5 min
        "health-check-backends": {
            "task": "app.tasks.maintenance.health_check_backends",
            "schedule": crontab(minute="*/5"),
        },
        # Backup automatique quotidien à 2h du matin
        "daily-backup": {
            "task": "app.tasks.backup_tasks.create_scheduled_backup",
            "schedule": crontab(hour=2, minute=0),
        },
        # Nettoyage fichiers anciens (rétention)
        "cleanup-old-files": {
            "task": "app.tasks.maintenance.cleanup_old_files",
            "schedule": crontab(hour=3, minute=0),
        },
        # Sync métriques Prometheus
        "sync-metrics": {
            "task": "app.tasks.maintenance.sync_prometheus_metrics",
            "schedule": crontab(minute="*/10"),
        },
    },
    
    # Routing
    task_routes={
        "app.tasks.build_tasks.*": {"queue": "build"},
        "app.tasks.backup_tasks.*": {"queue": "backup"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.version_tasks.*": {"queue": "versions"},
        "app.tasks.maintenance.*": {"queue": "maintenance"},
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# ──────────────────────────────────────────────
# Auto-discovery
# ──────────────────────────────────────────────
celery_app.autodiscover_tasks([
    "app.tasks.version_tasks",
    "app.tasks.notification_tasks",
    "app.tasks.backup_tasks",
    "app.tasks.build_tasks",
    "app.tasks.maintenance",
])