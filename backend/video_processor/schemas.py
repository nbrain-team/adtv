from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VideoJobResponse(BaseModel):
    jobId: str
    status: str
    progress: int

class VideoClipResponse(BaseModel):
    id: str
    title: str
    description: str
    duration: float
    startTime: float
    endTime: float
    platform: str
    thumbnail: Optional[str] = None
    status: str
    url: Optional[str] = None

class VideoJobStatus(BaseModel):
    jobId: str
    status: str
    progress: int
    error: Optional[str] = None
    clips: List[VideoClipResponse] = []

class ProcessVideoRequest(BaseModel):
    platforms: List[str] = ["instagram", "youtube", "facebook"] 