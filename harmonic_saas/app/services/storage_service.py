import boto3
import logging
from typing import Optional
from datetime import datetime, timedelta
import uuid
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    # S3 client
    _s3_client = None
    
    @classmethod
    def get_s3_client(cls):
        """
        Get S3 client with lazy initialization
        """
        if cls._s3_client is None:
            cls._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        
        return cls._s3_client
    
    @staticmethod
    def generate_presigned_url(
        bucket: str,
        key: str,
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> str:
        """
        Generate presigned URL for S3 object
        """
        try:
            s3_client = StorageService.get_s3_client()
            
            url = s3_client.generate_presigned_url(
                ClientMethod=method,
                Params={
                    'Bucket': bucket,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            
            logger.debug(f"Generated presigned URL for {bucket}/{key}")
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise
    
    @staticmethod
    def upload_audio_file(
        content: bytes,
        filename: str,
        user_id: str,
        bucket: Optional[str] = None
    ) -> str:
        """
        Upload audio file to S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            # Generate S3 key
            date_prefix = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"audio/{date_prefix}/{user_id}/{filename}"
            
            # Upload to S3
            s3_client = StorageService.get_s3_client()
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=content,
                ContentType='application/octet-stream'
            )
            
            logger.info(f"Audio file uploaded to S3: {s3_key}")
            
            # Generate presigned URL for download
            download_url = StorageService.generate_presigned_url(
                bucket=bucket,
                key=s3_key,
                expiration=86400  # 24 hours
            )
            
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload audio file: {str(e)}")
            raise
    
    @staticmethod
    def upload_video_file(
        content: bytes,
        filename: str,
        user_id: str,
        bucket: Optional[str] = None
    ) -> str:
        """
        Upload video file to S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            # Generate S3 key
            date_prefix = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"video/{date_prefix}/{user_id}/{filename}"
            
            # Upload to S3
            s3_client = StorageService.get_s3_client()
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=content,
                ContentType='application/octet-stream'
            )
            
            logger.info(f"Video file uploaded to S3: {s3_key}")
            
            # Generate presigned URL for download
            download_url = StorageService.generate_presigned_url(
                bucket=bucket,
                key=s3_key,
                expiration=86400  # 24 hours
            )
            
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload video file: {str(e)}")
            raise
    
    @staticmethod
    def download_file(
        s3_key: str,
        bucket: Optional[str] = None
    ) -> bytes:
        """
        Download file from S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            s3_client = StorageService.get_s3_client()
            response = s3_client.get_object(
                Bucket=bucket,
                Key=s3_key
            )
            
            content = response['Body'].read()
            
            logger.debug(f"File downloaded from S3: {s3_key}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise
    
    @staticmethod
    def delete_file(
        s3_key: str,
        bucket: Optional[str] = None
    ) -> bool:
        """
        Delete file from S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            s3_client = StorageService.get_s3_client()
            s3_client.delete_object(
                Bucket=bucket,
                Key=s3_key
            )
            
            logger.info(f"File deleted from S3: {s3_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False
    
    @staticmethod
    def list_user_files(
        user_id: str,
        file_type: str = "audio",
        bucket: Optional[str] = None
    ) -> list[dict]:
        """
        List user's files in S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            s3_client = StorageService.get_s3_client()
            
            # List objects with prefix
            prefix = f"{file_type}/"
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            files = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Check if file belongs to user
                    if f"/{user_id}/" in obj['Key']:
                        files.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified']
                        })
            
            logger.debug(f"Listed {len(files)} files for user {user_id}")
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list user files: {str(e)}")
            return []
    
    @staticmethod
    def get_file_info(
        s3_key: str,
        bucket: Optional[str] = None
    ) -> Optional[dict]:
        """
        Get file information from S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            s3_client = StorageService.get_s3_client()
            
            response = s3_client.head_object(
                Bucket=bucket,
                Key=s3_key
            )
            
            file_info = {
                'key': s3_key,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response['LastModified'],
                'etag': response['ETag']
            }
            
            logger.debug(f"Retrieved file info for: {s3_key}")
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None
    
    @staticmethod
    def generate_upload_url(
        user_id: str,
        filename: str,
        file_type: str = "audio",
        expiration: int = 3600,
        bucket: Optional[str] = None
    ) -> dict:
        """
        Generate presigned URL for direct upload to S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            # Generate unique filename
            file_ext = os.path.splitext(filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Generate S3 key
            date_prefix = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"{file_type}/{date_prefix}/{user_id}/{unique_filename}"
            
            # Generate presigned POST URL
            s3_client = StorageService.get_s3_client()
            
            conditions = [
                ["content-length-range", 1, settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024],
                ["starts-with", "$Content-Type", "audio/" if file_type == "audio" else "video/"]
            ]
            
            response = s3_client.generate_presigned_post(
                Bucket=bucket,
                Key=s3_key,
                Conditions=conditions,
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated upload URL for: {s3_key}")
            
            return {
                'upload_url': response['url'],
                'fields': response['fields'],
                's3_key': s3_key,
                'filename': unique_filename
            }
            
        except Exception as e:
            logger.error(f"Failed to generate upload URL: {str(e)}")
            raise
    
    @staticmethod
    def cleanup_old_files(
        days_old: int = 30,
        bucket: Optional[str] = None
    ) -> int:
        """
        Cleanup old files from S3
        """
        try:
            if bucket is None:
                bucket = settings.AWS_S3_BUCKET
            
            s3_client = StorageService.get_s3_client()
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # List all objects
            response = s3_client.list_objects_v2(Bucket=bucket)
            
            deleted_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        # Delete old file
                        s3_client.delete_object(
                            Bucket=bucket,
                            Key=obj['Key']
                        )
                        
                        deleted_count += 1
                        
                        logger.debug(f"Deleted old file: {obj['Key']}")
            
            logger.info(f"Cleaned up {deleted_count} old files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return 0