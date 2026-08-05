# ──────────────────────────────────────────────
# Tasks - Build Android APK
# ──────────────────────────────────────────────
from celery import shared_task
import subprocess
import os
import shutil
from pathlib import Path

from app.tasks.celery_app import celery_app
from app.core.database import get_db_context
from app.core.config import settings
from app.services.storage_service import storage_service
from app.models import APKVersion
from sqlalchemy import select


@shared_task(bind=True, max_retries=2, default_retry_delay=300, time_limit=3600)
def build_apk_task(
    self,
    version_name: str,
    version_code: int,
    channel: str = "stable",
    git_commit: str = None,
    git_branch: str = "main",
    bundle_id: str = None,
):
    """Builder APK Android depuis le code source"""
    import asyncio
    return asyncio.run(_build_apk_async(
        version_name, version_code, channel, git_commit, git_branch, bundle_id
    ))


async def _build_apk_async(
    version_name: str,
    version_code: int,
    channel: str,
    git_commit: str,
    git_branch: str,
    bundle_id: str,
):
    android_path = Path(settings.android_project_path)
    
    if not android_path.exists():
        raise Exception(f"Android project not found at {android_path}")

    # Sync assets d'abord
    sync_result = subprocess.run(
        ["node", "scripts/sync-assets.mjs"],
        cwd=android_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if sync_result.returncode != 0:
        raise Exception(f"Asset sync failed: {sync_result.stderr}")

    # Capacitor sync
    cap_sync = subprocess.run(
        ["npx", "cap", "sync", "android"],
        cwd=android_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if cap_sync.returncode != 0:
        raise Exception(f"Capacitor sync failed: {cap_sync.stderr}")

    # Build Gradle
    gradlew = android_path / "android" / "gradlew"
    if not gradlew.exists():
        raise Exception("gradlew not found")

    # Variables d'environnement pour le build
    env = os.environ.copy()
    env["JAVA_HOME"] = "/usr/lib/jvm/java-21-openjdk"  # Ajuster selon système

    build_result = subprocess.run(
        ["./gradlew", "assembleDebug" if channel != "stable" else "assembleRelease"],
        cwd=android_path / "android",
        capture_output=True,
        text=True,
        timeout=600,  # 10 min max
        env=env,
    )

    if build_result.returncode != 0:
        raise Exception(f"Gradle build failed: {build_result.stderr}")

    # Trouver APK généré
    apk_pattern = "app/build/outputs/apk/**/*.apk"
    apk_files = list((android_path / "android").glob(apk_pattern))
    if not apk_files:
        raise Exception("No APK generated")

    apk_path = apk_files[0]  # Prendre le premier

    # Lire APK et calculer hash
    apk_content = apk_path.read_bytes()
    import hashlib
    sha256_hash = hashlib.sha256(apk_content).hexdigest()

    # Upload vers MinIO
    minio_path = f"apk/{version_name}/{apk_path.name}"
    await storage_service.upload_file(minio_path, apk_content, "application/vnd.android.package-archive")

    # Créer entrée en base
    async with get_db_context() as db:
        # Vérifier bundle si fourni
        bundle_uuid = None
        if bundle_id:
            from uuid import UUID
            bundle_result = await db.execute(
                select(__import__('app.models.version', fromlist=['HologramBundle']).HologramBundle)
                .where(__import__('app.models.version', fromlist=['HologramBundle']).HologramBundle.id == UUID(bundle_id))
            )
            if bundle_result.scalar_one_or_none():
                bundle_uuid = UUID(bundle_id)

        version = APKVersion(
            version_name=version_name,
            version_code=version_code,
            channel=channel,
            apk_file_path=minio_path,
            apk_file_size=len(apk_content),
            apk_sha256=sha256_hash,
            bundle_id=bundle_uuid,
            git_commit=git_commit,
            git_branch=git_branch,
            built_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        )
        db.add(version)
        await db.commit()
        await db.refresh(version)

    return {
        "version_id": str(version.id),
        "version_name": version_name,
        "version_code": version_code,
        "apk_path": minio_path,
        "size": len(apk_content),
        "sha256": sha256_hash,
    }


@shared_task
def build_bundle_task(
    version: str,
    description: str = None,
):
    """Builder bundle hologrammes (déclenche script Python)"""
    import asyncio
    return asyncio.run(_build_bundle_async(version, description))


async def _build_bundle_async(version: str, description: str = None):
    """Lancer script build_hologram_bundle.py"""
    # Chemin vers le script de build
    script_path = Path(settings.android_project_path).parent / "data" / "build_hologram_bundle.py"
    
    if not script_path.exists():
        # Essayer chemin alternatif
        script_path = Path("/vital-ka/data/build_hologram_bundle.py")
    
    if not script_path.exists():
        raise Exception(f"Build script not found at {script_path}")

    # Exécuter script
    result = subprocess.run(
        ["python", str(script_path), "--version", version],
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise Exception(f"Bundle build failed: {result.stderr}")

    # Trouver bundle généré
    bundle_files = list(Path("/vital-ka/data").glob(f"hologram_bundle_{version}*.json"))
    if not bundle_files:
        bundle_files = list(Path(".").glob(f"hologram_bundle_{version}*.json"))
    
    if not bundle_files:
        raise Exception("No bundle generated")

    bundle_path = bundle_files[0]
    bundle_content = bundle_path.read_bytes()
    import hashlib
    sha256_hash = hashlib.sha256(bundle_content).hexdigest()

    # Upload
    minio_path = f"bundles/{version}/{bundle_path.name}"
    await storage_service.upload_file(minio_path, bundle_content, "application/json")

    # Parser métadonnées
    import json
    bundle_data = json.loads(bundle_content)
    domains_count = len(bundle_data.get("domains", {}))
    facts_count = sum(len(v) for v in bundle_data.get("domains", {}).values())
    pathologies_count = bundle_data.get("pathologies_count", 0)

    # Créer entrée en base
    async with get_db_context() as db:
        from app.models import HologramBundle
        from uuid import uuid4
        
        bundle = HologramBundle(
            id=uuid4(),
            version=version,
            description=description,
            bundle_file_path=minio_path,
            bundle_file_size=len(bundle_content),
            bundle_sha256=sha256_hash,
            domains_count=domains_count,
            facts_count=facts_count,
            pathologies_count=pathologies_count,
            metadata=bundle_data.get("metadata"),
            built_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        )
        db.add(bundle)
        await db.commit()
        await db.refresh(bundle)

    return {
        "bundle_id": str(bundle.id),
        "version": version,
        "size": len(bundle_content),
        "sha256": sha256_hash,
    }