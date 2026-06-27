from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import redis
from pymongo import MongoClient

from app.core.config import settings

# PostgreSQL
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis
redis_client = redis.Redis.from_url(settings.REDIS_URL)

# MongoDB
mongo_client = MongoClient(settings.MONGODB_URL)
mongo_db = mongo_client.get_database()

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