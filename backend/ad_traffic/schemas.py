from pydantic import BaseModel, EmailStr, validator
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
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"


class CampaignStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


# Client schemas
class ClientBase(BaseModel):
    name: str
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    brand_colors: Optional[List[str]] = []
    logo_url: Optional[str] = None
    social_accounts: Optional[Dict[str, str]] = {}
    # New fields
    daily_budget: Optional[float] = 0.0
    ad_duration_days: Optional[int] = 7
    geo_targeting: Optional[List[str]] = []


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    brand_colors: Optional[List[str]] = None
    logo_url: Optional[str] = None
    social_accounts: Optional[Dict[str, str]] = None
    daily_budget: Optional[float] = None
    ad_duration_days: Optional[int] = None
    geo_targeting: Optional[List[str]] = None


class Client(ClientBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
    
    @validator('email', pre=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v


# Post schemas
class PostBase(BaseModel):
    content: str
    platforms: List[Platform]
    scheduled_time: datetime
    video_clip_id: Optional[str] = None
    media_urls: Optional[List[str]] = []  # Add media_urls to base schema


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: Optional[str] = None
    platforms: Optional[List[Platform]] = None
    scheduled_time: Optional[datetime] = None
    status: Optional[PostStatus] = None
    media_urls: Optional[List[str]] = None  # Add media_urls to update schema


class PostApproval(BaseModel):
    approved: bool
    notes: Optional[str] = None


class SocialPost(PostBase):
    id: str
    client_id: str
    campaign_id: Optional[str] = None
    status: PostStatus
    published_time: Optional[datetime] = None
    platform_post_ids: Optional[Dict[str, str]] = {}
    media_urls: Optional[List[str]] = []  # Changed from Dict to List
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = {}
    budget_spent: Optional[float] = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None
    campaign_name: Optional[str] = None  # Added for response
    # Removed video_clip field to prevent circular reference issues

    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2
    
    @validator('platforms', pre=True)
    def convert_platforms(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                return [v]
        return v
    
    @validator('media_urls', pre=True)
    def ensure_media_urls_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            # Convert dict to list
            return list(v.values()) if v else []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return list(parsed.values()) if parsed else []
                return parsed if isinstance(parsed, list) else []
            except:
                return []
        return v if isinstance(v, list) else []


# Campaign schemas
class CampaignBase(BaseModel):
    name: str
    duration_weeks: int
    platforms: List[Platform]
    start_date: Optional[datetime] = None


class CampaignCreate(CampaignBase):
    pass


class Campaign(CampaignBase):
    id: str
    client_id: str
    original_video_url: str
    video_urls: Optional[List[str]] = []
    status: CampaignStatus
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Video clip schemas
class VideoClip(BaseModel):
    id: str
    campaign_id: str
    source_video_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    duration: float
    start_time: float
    end_time: float
    video_url: str
    thumbnail_url: Optional[str] = None
    platform_versions: Optional[Dict[str, str]] = {}
    suggested_caption: Optional[str] = None
    suggested_hashtags: Optional[List[str]] = []
    content_type: Optional[str] = None
    aspect_ratio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignWithClips(Campaign):
    video_clips: List[VideoClip] = [] 