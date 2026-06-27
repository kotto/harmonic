from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
import os

from app.core.config import settings

# Détection automatique SQLite vs PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Configuration du moteur SQLAlchemy
if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Nécessaire pour SQLite avec FastAPI
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis (optionnel)
redis_client = None
try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
except Exception:
    pass  # Redis non disponible, continuer sans

# MongoDB (optionnel)
mongo_db = None
try:
    from pymongo import MongoClient
    mongo_client = MongoClient(settings.MONGODB_URL)
    mongo_db = mongo_client.get_database()
except Exception:
    pass  # MongoDB non disponible, continuer sans

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    return redis_client

def get_mongo():
    return mongo_db
