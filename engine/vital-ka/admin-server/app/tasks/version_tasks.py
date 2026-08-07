# ──────────────────────────────────────────────
# Tasks - Versions & Webhooks
# ──────────────────────────────────────────────
from celery import shared_task
from typing import Optional
import httpx
import json

from app.tasks.celery_app import celery_app
from app.core.database import get_db_context
from app.core.config import settings
from app.services.storage_service import storage_service
from app.models import APKVersion, HologramBundle, WebhookLog, SystemConfig
from sqlalchemy import select


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_webhooks(self, version_id: str, event_type: str):
    """Déclencher webhooks pour événement version/bundle"""
    import asyncio
    asyncio.run(_trigger_webhooks_async(version_id, event_type))


async def _trigger_webhooks_async(version_id: str, event_type: str):
    async with get_db_context() as db:
        # Récupérer URLs webhook depuis config
        config_result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.key.in_([
                    "webhooks.version_published_urls",
                    "webhooks.bundle_published_urls",
                    "webhooks.retry_attempts",
                    "webhooks.timeout_seconds",
                ])
            )
        )
        configs = {c.key: c.value.get("value") for c in config_result.scalars().all()}
        
        urls = configs.get(f"webhooks.{event_type}_urls", [])
        retry_attempts = configs.get("webhooks.retry_attempts", 3)
        timeout = configs.get("webhooks.timeout_seconds", 30)
        
        if not urls:
            return  # Pas de webhooks configurés

        # Récupérer version ou bundle
        if event_type.startswith("version"):
            result = await db.execute(select(APKVersion).where(APKVersion.id == version_id))
            entity = result.scalar_one_or_none()
            payload = {
                "event": event_type,
                "version": {
                    "id": str(entity.id),
                    "version_name": entity.version_name,
                    "version_code": entity.version_code,
                    "channel": entity.channel.value,
                    "download_url": await storage_service.get_presigned_url(entity.apk_file_path),
                    "changelog": entity.changelog,
                    "is_mandatory": entity.is_mandatory,
                } if entity else None,
            }
        else:
            result = await db.execute(select(HologramBundle).where(HologramBundle.id == version_id))
            entity = result.scalar_one_or_none()
            payload = {
                "event": event_type,
                "bundle": {
                    "id": str(entity.id),
                    "version": entity.version,
                    "download_url": await storage_service.get_presigned_url(entity.bundle_file_path),
                    "domains_count": entity.domains_count,
                    "facts_count": entity.facts_count,
                } if entity else None,
            }

        if not entity:
            return

        # Envoyer vers chaque URL
        async with httpx.AsyncClient(timeout=timeout) as client:
            for url in urls:
                for attempt in range(1, retry_attempts + 1):
                    log = WebhookLog(
                        version_id=entity.id if hasattr(entity, 'version_code') else None,
                        bundle_id=entity.id if hasattr(entity, 'version') else None,
                        url=url,
                        event_type=event_type,
                        payload=payload,
                        attempt=attempt,
                    )
                    db.add(log)
                    await db.flush()

                    try:
                        resp = await client.post(url, json=payload)
                        log.status_code = resp.status_code
                        log.response_body = resp.text[:1000] if resp.text else None
                        log.success = 200 <= resp.status_code < 300
                        log.completed_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
                        break  # Succès, pas de retry
                    except Exception as e:
                        log.error_message = str(e)
                        log.success = False
                        if attempt == retry_attempts:
                            log.completed_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
                    
                    await db.commit()

        await db.commit()


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_webhook(self, log_id: str):
    """Réessayer un webhook spécifique"""
    import asyncio
    asyncio.run(_send_webhook_async(log_id))


async def _send_webhook_async(log_id: str):
    async with get_db_context() as db:
        from app.models import WebhookLog
        result = await db.execute(select(WebhookLog).where(WebhookLog.id == log_id))
        log = result.scalar_one_or_none()
        if not log or log.success:
            return

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(log.url, json=log.payload)
                log.status_code = resp.status_code
                log.response_body = resp.text[:1000] if resp.text else None
                log.success = 200 <= resp.status_code < 300
                log.completed_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            except Exception as e:
                log.error_message = str(e)
                log.success = False
            
            await db.commit()


@shared_task
def notify_version_available(version_id: str, tester_emails: list[str]):
    """Notifier testeurs nouvelle version disponible"""
    # TODO: Implémenter notification email/push
    pass