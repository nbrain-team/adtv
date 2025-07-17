from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

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
    brand_colors: Optional[List[str]] = None
    logo_url: Optional[str] = None

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
    auto_post_enabled: Optional[bool] = None
    default_post_times: Optional[List[str]] = None
    hashtag_sets: Optional[Dict[str, List[str]]] = None

class ClientResponse(ClientBase):
    id: str
    facebook_page_name: Optional[str] = None
    instagram_username: Optional[str] = None
    auto_post_enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ClientDetailResponse(ClientResponse):
    facebook_page_id: Optional[str] = None
    instagram_account_id: Optional[str] = None
    default_post_times: Optional[List[str]] = None
    hashtag_sets: Optional[Dict[str, List[str]]] = None
    
class FacebookConnect(BaseModel):
    page_id: str
    page_name: str
    access_token: str

class InstagramConnect(BaseModel):
    account_id: str
    username: str

class ScheduledPostCreate(BaseModel):
    client_id: str
    campaign_id: Optional[str] = None
    content: str
    media_urls: Optional[List[str]] = []
    video_clip_ids: Optional[List[str]] = []
    platforms: List[str]  # ["facebook", "instagram"]
    platform_specific_content: Optional[Dict[str, str]] = {}
    scheduled_time: datetime

class ScheduledPostResponse(BaseModel):
    id: str
    client_id: str
    campaign_id: Optional[str] = None
    content: str
    media_urls: List[str]
    video_clip_ids: List[str]
    platforms: List[str]
    scheduled_time: datetime
    status: str
    published_at: Optional[datetime] = None
    facebook_post_id: Optional[str] = None
    instagram_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 