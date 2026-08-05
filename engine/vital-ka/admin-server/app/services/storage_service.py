# ──────────────────────────────────────────────
# Service Storage (MinIO/S3)
# ──────────────────────────────────────────────
from typing import Optional, BinaryIO
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
import io

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        self._bucket_ready = False

    def _ensure_bucket(self):
        """Créer bucket s'il n'existe pas (lazy — appelé au premier usage)"""
        if self._bucket_ready:
            return
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                # Policy publique pour certains dossiers
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket}/apk/*"],
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket}/bundles/*"],
                        },
                    ],
                }
                import json
                self.client.set_bucket_policy(self.bucket, json.dumps(policy))
            self._bucket_ready = True
        except (S3Error, Exception) as e:
            print(f"MinIO bucket error (retry au prochain usage): {e}")

    async def upload_file(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload fichier vers MinIO"""
        self._ensure_bucket()
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return object_name
        except S3Error as e:
            raise Exception(f"Upload failed: {e}")

    async def download_file(self, object_name: str) -> bytes:
        """Télécharger fichier depuis MinIO"""
        self._ensure_bucket()
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Download failed: {e}")

    async def delete_file(self, object_name: str) -> bool:
        """Supprimer fichier"""
        self._ensure_bucket()
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    async def get_presigned_url(
        self,
        object_name: str,
        expires_in: int = 3600,
    ) -> str:
        """Générer URL signée pour téléchargement"""
        self._ensure_bucket()
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=expires_in),
            )
            return url
        except S3Error as e:
            raise Exception(f"Presigned URL failed: {e}")

    async def file_exists(self, object_name: str) -> bool:
        """Vérifier existence fichier"""
        self._ensure_bucket()
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    async def get_file_info(self, object_name: str) -> dict:
        """Infos fichier"""
        self._ensure_bucket()
        try:
            stat = self.client.stat_object(self.bucket, object_name)
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
            }
        except S3Error as e:
            raise Exception(f"File info failed: {e}")

    async def list_files(self, prefix: str = "", limit: int = 1000) -> list[dict]:
        """Lister fichiers"""
        self._ensure_bucket()
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix, recursive=True)
            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                }
                for obj in list(objects)[:limit]
            ]
        except S3Error as e:
            raise Exception(f"List files failed: {e}")

    async def get_storage_usage(self) -> dict:
        """Utilisation stockage"""
        self._ensure_bucket()
        try:
            # Approximation via list objects
            total_size = 0
            count = 0
            objects = self.client.list_objects(self.bucket, recursive=True)
            for obj in objects:
                total_size += obj.size
                count += 1
            return {
                "used_bytes": total_size,
                "object_count": count,
                "available_bytes": -1,  # MinIO ne donne pas l'espace disque
            }
        except S3Error:
            return {"used_bytes": 0, "object_count": 0, "available_bytes": -1}

    async def list_backups(self, limit: int = 50) -> list[dict]:
        """Lister backups"""
        self._ensure_bucket()
        try:
            objects = self.client.list_objects(self.bucket, prefix="backups/", recursive=True)
            backups = []
            for obj in sorted(objects, key=lambda x: x.last_modified, reverse=True)[:limit]:
                backups.append({
                    "id": obj.object_name,
                    "name": obj.object_name.split("/")[-1],
                    "size_bytes": obj.size,
                    "created_at": obj.last_modified,
                    "status": "completed",
                })
            return backups
        except S3Error:
            return []

    async def health_check(self) -> bool:
        """Health check MinIO"""
        try:
            self.client.list_buckets()
            return True
        except Exception:
            return False


storage_service = StorageService()