from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Harmonic AI SaaS"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:9000"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Database
    DATABASE_URL: str = "postgresql://harmonic:harmonic123@localhost:5432/harmonic_saas"
    REDIS_URL: str = "redis://localhost:6379/0"
    MONGODB_URL: str = "mongodb://localhost:27017/harmonic_saas"
    
    # External Services
    AUDIO_SERVICE_URL: str = "http://localhost:9017"
    VIDEO_SERVICE_URL: str = "http://localhost:9018"
    LM_ARENA_SERVICE_URL: str = "http://localhost:8000"
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "eu-west-1"
    AWS_S3_BUCKET: str = "harmonic-ai-saas"
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "noreply@harmonic-ai.com"
    EMAILS_FROM_NAME: str = "Harmonic AI"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".mp3", ".wav", ".flac", ".m4a", ".aac"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()