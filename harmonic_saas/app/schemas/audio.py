from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AudioProcessingMode(str, Enum):
    HCS_RESTORE = "hcs_restore"
    HCS_SPATIAL = "hcs_spatial"
    HCS_CLARITY = "hcs_clarity"
    HCS_DYNAMIC = "hcs_dynamic"

class AudioJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AudioJobBase(BaseModel):
    job_name: Optional[str] = None
    processing_mode: AudioProcessingMode

class AudioJobCreate(AudioJobBase):
    pass

class AudioJobUpdate(BaseModel):
    status: Optional[AudioJobStatus] = None
    output_filename: Optional[str] = None
    output_filepath: Optional[str] = None
    error_message: Optional[str] = None

class AudioJobInDB(AudioJobBase):
    id: str
    user_id: str
    status: AudioJobStatus
    input_filename: Optional[str] = None
    input_filepath: Optional[str] = None
    input_filesize_bytes: Optional[int] = None
    output_filename: Optional[str] = None
    output_filepath: Optional[str] = None
    output_filesize_bytes: Optional[int] = None
    processing_time_ms: Optional[int] = None
    quality_improvement: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AudioJob(AudioJobInDB):
    pass

class AudioProcessingRequest(BaseModel):
    processing_mode: AudioProcessingMode = Field(default=AudioProcessingMode.HCS_RESTORE)
    target_profile: Optional[str] = None
    enhance_clarity: bool = Field(default=True)
    reduce_noise: bool = Field(default=True)
    expand_dynamic_range: bool = Field(default=True)
    add_spatial_channels: bool = Field(default=False)
    custom_parameters: Optional[Dict[str, Any]] = None

class AudioProcessingResponse(BaseModel):
    job_id: str
    status: AudioJobStatus
    processing_time_ms: Optional[int] = None
    quality_improvement: Optional[int] = None
    output_url: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class AudioUploadResponse(BaseModel):
    upload_id: str
    filename: str
    filesize_bytes: int
    upload_url: str
    expires_at: datetime