from pydantic import BaseModel, UUID4, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class CampaignStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


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


class Client(ClientBase):
    id: UUID4
    user_id: UUID4
    social_accounts: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Video Clip Schemas
class VideoClipBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration: float
    start_time: float
    end_time: float
    content_type: Optional[str] = None
    suggested_caption: Optional[str] = None
    suggested_hashtags: List[str] = []


class VideoClip(VideoClipBase):
    id: UUID4
    campaign_id: UUID4
    video_url: str
    thumbnail_url: Optional[str] = None
    platform_versions: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


# Post Schemas
class PostBase(BaseModel):
    content: str
    platforms: List[Platform]
    scheduled_time: datetime
    media_urls: Optional[List[str]] = []
    video_clip_id: Optional[UUID4] = None


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    content: Optional[str] = None
    platforms: Optional[List[Platform]] = None
    scheduled_time: Optional[datetime] = None
    status: Optional[PostStatus] = None


class SocialPost(PostBase):
    id: UUID4
    client_id: UUID4
    campaign_id: Optional[UUID4] = None
    video_clip: Optional[VideoClip] = None
    status: PostStatus
    published_at: Optional[datetime] = None
    platform_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    campaign_name: Optional[str] = None

    class Config:
        from_attributes = True


# Campaign Schemas
class CampaignBase(BaseModel):
    name: str
    duration_weeks: int
    platforms: List[Platform]


class CampaignCreate(CampaignBase):
    pass


class Campaign(CampaignBase):
    id: UUID4
    client_id: UUID4
    original_video_url: str
    status: CampaignStatus
    progress: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CampaignWithClips(Campaign):
    video_clips: List[VideoClip] = [] 