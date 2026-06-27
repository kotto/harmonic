from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UsageRecord(BaseModel):
    id: str
    user_id: str
    api_key_id: Optional[str] = None
    endpoint: str
    method: str = "POST"
    tokens_used: int = 0
    audio_seconds: float = 0.0
    video_seconds: float = 0.0
    cost: float = 0.0
    timestamp: datetime
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class UsageSummary(BaseModel):
    user_id: str
    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    total_tokens: int = 0
    total_audio_seconds: float = 0.0
    total_video_seconds: float = 0.0
    total_cost: float = 0.0
    successful_requests: int = 0
    failed_requests: int = 0
