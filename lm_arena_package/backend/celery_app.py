from celery import Celery
import logging
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "harmonic_saas",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.audio_tasks",
        "app.tasks.video_tasks",
        "app.tasks.email_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_concurrency=4,
    
    # Beat schedule
    beat_schedule={
        # Cleanup old jobs every day at 2 AM
        "cleanup-old-jobs": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_jobs",
            "schedule": timedelta(days=1),
            "options": {"queue": "cleanup"}
        },
        
        # Send usage reports every Monday at 9 AM
        "send-usage-reports": {
            "task": "app.tasks.email_tasks.send_weekly_usage_reports",
            "schedule": timedelta(weeks=1),
            "options": {"queue": "email"}
        },
        
        # Update analytics every hour
        "update-analytics": {
            "task": "app.tasks.analytics_tasks.update_analytics",
            "schedule": timedelta(hours=1),
            "options": {"queue": "analytics"}
        },
        
        # Check subscription renewals every day at 6 AM
        "check-subscription-renewals": {
            "task": "app.tasks.billing_tasks.check_subscription_renewals",
            "schedule": timedelta(days=1),
            "options": {"queue": "billing"}
        }
    },
    
    # Task routes
    task_routes={
        "app.tasks.audio_tasks.*": {"queue": "audio"},
        "app.tasks.video_tasks.*": {"queue": "video"},
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.tasks.billing_tasks.*": {"queue": "billing"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"}
    },
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Task time limits
    task_time_limit=1800,  # 30 minutes
    task_soft_time_limit=1500,  # 25 minutes
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True
)

# Set up logging for Celery
celery_app.conf.worker_hijack_root_logger = False

@celery_app.task(bind=True)
def debug_task(self):
    """
    Debug task to test Celery setup
    """
    logger.info(f"Debug task executed: {self.request.id}")
    return {"status": "success", "task_id": self.request.id}

if __name__ == "__main__":
    celery_app.start()