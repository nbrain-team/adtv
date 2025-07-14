"""
API Schemas for Marketing Campaign Generator
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.database import CampaignStatus, ContentStatus, Platform

# Client Schemas
class ClientBase(BaseModel):
    name: str
    company: str
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    competitors: Optional[List[str]] = None
    social_accounts: Optional[Dict[str, str]] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    competitors: Optional[List[str]] = None
    social_accounts: Optional[Dict[str, str]] = None

class ClientResponse(ClientBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Campaign Schemas
class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    topics: List[str] = Field(..., min_items=1, max_items=5)
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def end_date_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class CampaignCreate(CampaignBase):
    client_id: str
    platforms: List[str] = Field(..., min_items=1)
    
    @validator('platforms')
    def validate_platforms(cls, v):
        valid_platforms = [p.value for p in Platform]
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f'Invalid platform: {platform}')
        return v

class CampaignResponse(CampaignBase):
    id: str
    client_id: str
    status: CampaignStatus
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True

class CampaignDetail(CampaignResponse):
    client: ClientResponse
    content_items: List['ContentItemResponse']
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None

class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus
    notes: Optional[str] = None

# Content Item Schemas
class ContentItemBase(BaseModel):
    platform: Platform
    content: str
    title: Optional[str] = None  # For emails
    hashtags: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None
    scheduled_date: Optional[datetime] = None

class ContentItemResponse(ContentItemBase):
    id: str
    campaign_id: str
    content_type: Optional[str] = None
    status: ContentStatus
    published_date: Optional[datetime] = None
    platform_post_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ContentFeedback(BaseModel):
    feedback: str = Field(..., min_length=10, max_length=500)

# Analytics Schemas
class ContentAnalyticsResponse(BaseModel):
    content_item_id: str
    views: int
    likes: int
    comments: int
    shares: int
    clicks: int
    engagement_rate: float
    fetched_at: datetime
    
    class Config:
        from_attributes = True

class CampaignAnalyticsResponse(BaseModel):
    campaign_id: str
    total_reach: int
    total_engagement: int
    total_clicks: int
    platform_metrics: Dict[str, Dict[str, Any]]
    estimated_value: float
    cost: float
    roi: float
    calculated_at: datetime
    
    class Config:
        from_attributes = True

# Calendar/Schedule Schemas
class CalendarEventResponse(BaseModel):
    id: str
    title: str
    content: str
    platform: Platform
    scheduled_date: datetime
    status: ContentStatus
    campaign_id: str
    campaign_name: str
    client_name: str

class BulkScheduleUpdate(BaseModel):
    content_ids: List[str]
    new_dates: Dict[str, datetime]  # content_id -> new_date

# Document Upload
class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    content_extracted: bool
    embedding_created: bool
    uploaded_at: datetime

# Update forward references
CampaignDetail.model_rebuild() 