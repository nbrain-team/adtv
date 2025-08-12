"""
Pydantic schemas for Facebook Automation module
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FacebookPermissions(BaseModel):
    """Facebook permissions granted by the user"""
    manage_pages: bool = True
    ads_management: bool = True
    pages_show_list: bool = True
    business_management: bool = True


class AutomationRules(BaseModel):
    """Rules for automated post-to-ad conversion"""
    min_text_length: int = Field(50, ge=10)
    require_image: bool = True
    auto_approve: bool = False
    target_audience: str = "interests"  # interests, lookalike, custom
    optimization_goal: str = "REACH"
    exclude_keywords: List[str] = []
    require_approval_keywords: List[str] = []


class FacebookClientCreate(BaseModel):
    """Create a new Facebook client connection"""
    facebook_user_id: str
    facebook_page_id: str
    page_name: str
    page_access_token: str
    ad_account_id: Optional[str] = None
    business_id: Optional[str] = None
    default_daily_budget: float = Field(50.0, ge=1.0)
    default_campaign_duration: int = Field(7, ge=1, le=90)
    auto_convert_posts: bool = False
    automation_rules: Optional[AutomationRules] = None


class FacebookClientUpdate(BaseModel):
    """Update Facebook client settings"""
    is_active: Optional[bool] = None
    auto_convert_posts: Optional[bool] = None
    default_daily_budget: Optional[float] = Field(None, ge=1.0)
    default_campaign_duration: Optional[int] = Field(None, ge=1, le=90)
    automation_rules: Optional[AutomationRules] = None


class FacebookClient(BaseModel):
    """Facebook client response"""
    id: str
    user_id: str
    facebook_user_id: str
    facebook_page_id: str
    page_name: Optional[str]
    ad_account_id: Optional[str]
    is_active: bool
    auto_convert_posts: bool
    default_daily_budget: float
    default_campaign_duration: int
    automation_rules: Dict[str, Any]
    created_at: datetime
    last_sync: Optional[datetime]
    token_expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PostStatus(str, Enum):
    """Post processing status"""
    IMPORTED = "imported"
    REVIEWED = "reviewed"
    CONVERTED = "converted"
    SKIPPED = "skipped"


class FacebookPost(BaseModel):
    """Facebook post response"""
    id: str
    client_id: str
    facebook_post_id: str
    post_url: Optional[str]
    message: Optional[str]
    created_time: Optional[datetime]
    post_type: Optional[str]
    media_urls: List[str]
    thumbnail_url: Optional[str]
    likes_count: int
    comments_count: int
    shares_count: int
    reach: int
    status: PostStatus
    review_notes: Optional[str]
    ai_quality_score: Optional[float]
    ai_suggestions: Optional[Dict[str, Any]]
    imported_at: datetime
    converted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PostReview(BaseModel):
    """Review a post for conversion"""
    status: PostStatus
    review_notes: Optional[str] = None


class AdTargeting(BaseModel):
    """Ad targeting configuration"""
    geo_locations: Dict[str, List[str]] = {"countries": ["US"]}
    age_min: int = Field(18, ge=13, le=65)
    age_max: int = Field(65, ge=18, le=65)
    genders: List[int] = [1, 2]  # 1=male, 2=female
    interests: List[str] = []
    behaviors: List[str] = []
    custom_audiences: List[str] = []
    
    @validator('age_max')
    def age_max_greater_than_min(cls, v, values):
        if 'age_min' in values and v < values['age_min']:
            raise ValueError('age_max must be greater than age_min')
        return v


class AdCreativeContent(BaseModel):
    """Ad creative content"""
    primary_text: str = Field(..., min_length=1, max_length=2000)
    headline: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    call_to_action: str = "LEARN_MORE"
    link_url: Optional[str] = None
    display_link: Optional[str] = None


class CampaignCreate(BaseModel):
    """Create a new ad campaign"""
    source_post_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    objective: str = "REACH"
    creative: AdCreativeContent
    daily_budget: float = Field(50.0, ge=1.0)
    lifetime_budget: Optional[float] = Field(None, ge=1.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    targeting: Optional[AdTargeting] = None
    is_ab_test: bool = False
    ab_test_variants: Optional[List[Dict[str, Any]]] = None


class CampaignUpdate(BaseModel):
    """Update campaign settings"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None
    daily_budget: Optional[float] = Field(None, ge=1.0)
    end_date: Optional[datetime] = None
    targeting: Optional[AdTargeting] = None


class AdStatus(str, Enum):
    """Ad campaign status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class FacebookAdCampaign(BaseModel):
    """Ad campaign response"""
    id: str
    client_id: str
    source_post_id: Optional[str]
    name: str
    objective: str
    status: AdStatus
    primary_text: Optional[str]
    headline: Optional[str]
    description: Optional[str]
    creative_urls: List[str]
    daily_budget: float
    lifetime_budget: Optional[float]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    targeting: Dict[str, Any]
    impressions: int
    reach: int
    clicks: int
    ctr: float
    cpc: float
    cpm: float
    spend: float
    conversions: int
    conversion_rate: float
    roas: float
    created_at: datetime
    launched_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AnalyticsTimeframe(str, Enum):
    """Analytics timeframe options"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    CUSTOM = "custom"


class AnalyticsRequest(BaseModel):
    """Request analytics data"""
    campaign_ids: Optional[List[str]] = None
    client_ids: Optional[List[str]] = None
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.LAST_7_DAYS
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    group_by: Optional[str] = None  # day, week, month, campaign, client


class AnalyticsResponse(BaseModel):
    """Analytics data response"""
    total_spend: float
    total_impressions: int
    total_reach: int
    total_clicks: int
    avg_ctr: float
    avg_cpc: float
    avg_cpm: float
    total_conversions: int
    avg_conversion_rate: float
    avg_roas: float
    top_performing_campaigns: List[Dict[str, Any]]
    demographics_breakdown: Dict[str, Any]
    device_breakdown: Dict[str, Any]
    time_series: List[Dict[str, Any]]


class BulkOperation(BaseModel):
    """Bulk operation on multiple items"""
    item_ids: List[str]
    operation: str  # pause, resume, delete, approve
    
    
class AdTemplate(BaseModel):
    """Ad template for reuse"""
    id: str
    name: str
    description: Optional[str]
    template_type: str
    primary_text_template: Optional[str]
    headline_template: Optional[str]
    description_template: Optional[str]
    call_to_action: str
    rules: Dict[str, Any]
    avg_ctr: Optional[float]
    avg_conversion_rate: Optional[float]
    times_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdTemplateCreate(BaseModel):
    """Create a new ad template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: str = "standard"
    primary_text_template: str
    headline_template: str
    description_template: Optional[str] = None
    call_to_action: str = "LEARN_MORE"
    rules: Optional[Dict[str, Any]] = None 