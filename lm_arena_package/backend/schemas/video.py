from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class VideoProcessingMode(str, Enum):
    HCS_4K_CLARITY = "hcs_4k_clarity"
    HCS_8K_MASTER = "hcs_8k_master"
    HCS_HDR_VISION = "hcs_hdr_vision"
    HCS_FRAME_GEN = "hcs_frame_gen"
    HCS_MOVIE_CONTINUOUS = "hcs_movie_continuous"

class VideoJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VideoJobBase(BaseModel):
    job_name: Optional[str] = None
    processing_mode: VideoProcessingMode

class VideoJobCreate(VideoJobBase):
    pass

class VideoJobUpdate(BaseModel):
    status: Optional[VideoJobStatus] = None
    output_filename: Optional[str] = None
    output_filepath: Optional[str] = None
    error_message: Optional[str] = None

class VideoJobInDB(VideoJobBase):
    id: str
    user_id: str
    status: VideoJobStatus
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

class VideoJob(VideoJobInDB):
    pass

class VideoProcessingRequest(BaseModel):
    processing_mode: VideoProcessingMode = Field(default=VideoProcessingMode.HCS_4K_CLARITY)
    target_resolution: Optional[str] = None
    target_fps: Optional[int] = None
    enable_hdr: bool = Field(default=False)
    enable_frame_gen: bool = Field(default=False)
    enable_continuous: bool = Field(default=False)
    custom_parameters: Optional[Dict[str, Any]] = None

class VideoProcessingResponse(BaseModel):
    job_id: str
    status: VideoJobStatus
    processing_time_ms: Optional[int] = None
    quality_improvement: Optional[int] = None
    output_url: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class VideoUploadResponse(BaseModel):
    upload_id: str
    filename: str
    filesize_bytes: int
    upload_url: str
    expires_at: datetime