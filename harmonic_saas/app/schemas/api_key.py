from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class APIKeyCreate(APIKeyBase):
    can_read: bool = True
    can_write: bool = True
    can_delete: bool = False
    can_manage: bool = False
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    rate_limit_per_hour: int = Field(default=1000, ge=10, le=10000)

class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    can_read: Optional[bool] = None
    can_write: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_manage: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=10, le=10000)
    is_active: Optional[bool] = None

class APIKeyInDB(APIKeyBase):
    id: str
    user_id: str
    key: str
    prefix: str
    can_read: bool
    can_write: bool
    can_delete: bool
    can_manage: bool
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    last_used: Optional[datetime] = None
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class APIKey(APIKeyInDB):
    pass

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

class APIKeyListResponse(BaseModel):
    api_keys: list[APIKeyResponse]
    total: int