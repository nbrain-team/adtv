from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    facebook = "facebook"
    instagram = "instagram"
    tiktok = "tiktok"

class PostStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"

class CampaignStatus(str, Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"

# Client Schemas
class ClientBase(BaseModel):
    name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    brand_colors: Optional[List[str]] = []
    logo_url: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    name: Optional[str] = None

class ClientResponse(ClientBase):
    id: str
    user_id: str
    social_accounts: Dict = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Social Media Post Schemas
class PostBase(BaseModel):
    content: str
    platforms: List[PlatformType]
    scheduled_time: datetime
    media_urls: Optional[List[str]] = []
    video_clip_id: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None
    platforms: Optional[List[PlatformType]] = None
    scheduled_time: Optional[datetime] = None
    media_urls: Optional[List[str]] = None
    status: Optional[PostStatus] = None

class PostResponse(PostBase):
    id: str
    client_id: str
    campaign_id: Optional[str] = None
    status: PostStatus
    published_at: Optional[datetime] = None
    platform_data: Dict = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Video Clip Campaign Schemas
class CampaignCreate(BaseModel):
    name: str
    duration_weeks: int = Field(ge=1, le=8)
    platforms: List[PlatformType]

class CampaignResponse(BaseModel):
    id: str
    client_id: str
    name: str
    original_video_url: str
    duration_weeks: int
    platforms: List[PlatformType]
    status: CampaignStatus
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Video Clip Schemas
class VideoClipResponse(BaseModel):
    id: str
    campaign_id: str
    title: str
    description: Optional[str] = None
    duration: float
    start_time: float
    end_time: float
    video_url: str
    thumbnail_url: Optional[str] = None
    platform_versions: Dict = {}
    suggested_caption: Optional[str] = None
    suggested_hashtags: List[str] = []
    content_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Calendar View Schema
class CalendarPostResponse(BaseModel):
    id: str
    content: str
    platforms: List[PlatformType]
    scheduled_time: datetime
    status: PostStatus
    media_urls: List[str] = []
    video_clip: Optional[VideoClipResponse] = None
    campaign_name: Optional[str] = None
    
    class Config:
        from_attributes = True 