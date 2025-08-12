"""
Database models for Facebook Automation module
"""

from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, JSON, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from core.database import Base


class AdStatus(str, enum.Enum):
    """Status of ad campaigns"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PostStatus(str, enum.Enum):
    """Status of imported posts"""
    IMPORTED = "imported"
    REVIEWED = "reviewed"
    CONVERTED = "converted"
    SKIPPED = "skipped"


class FacebookClient(Base):
    """Facebook client accounts connected via OAuth"""
    __tablename__ = "facebook_clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Facebook OAuth data
    facebook_user_id = Column(String, nullable=False, unique=True)
    facebook_page_id = Column(String, nullable=False)
    page_name = Column(String)
    page_access_token = Column(Text)  # Encrypted in production
    
    # Permissions and settings
    permissions = Column(JSON, default=lambda: {
        "manage_pages": True,
        "ads_management": True,
        "pages_show_list": True,
        "business_management": True
    })
    
    # Ad account info
    ad_account_id = Column(String)
    business_id = Column(String)
    
    # Client settings
    is_active = Column(Boolean, default=True)
    auto_convert_posts = Column(Boolean, default=False)
    default_daily_budget = Column(Float, default=50.0)
    default_campaign_duration = Column(Integer, default=7)  # days
    
    # Automation rules
    automation_rules = Column(JSON, default=lambda: {
        "min_text_length": 50,
        "require_image": True,
        "auto_approve": False,
        "target_audience": "interests",
        "optimization_goal": "REACH"
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_sync = Column(DateTime(timezone=True))
    token_expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="facebook_clients")
    posts = relationship("FacebookPost", back_populates="client", cascade="all, delete-orphan")
    campaigns = relationship("FacebookAdCampaign", back_populates="client", cascade="all, delete-orphan")
    

class FacebookPost(Base):
    """Organic Facebook posts imported from client pages"""
    __tablename__ = "facebook_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("facebook_clients.id"), nullable=False)
    
    # Facebook post data
    facebook_post_id = Column(String, nullable=False, unique=True)
    post_url = Column(String)
    message = Column(Text)
    created_time = Column(DateTime(timezone=True))
    post_type = Column(String)  # photo, video, link, status
    
    # Media
    media_urls = Column(JSON, default=list)  # List of image/video URLs
    thumbnail_url = Column(String)
    
    # Engagement metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    
    # Processing status
    status = Column(SQLEnum(PostStatus), default=PostStatus.IMPORTED)
    review_notes = Column(Text)
    reviewed_by = Column(String, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    
    # AI analysis
    ai_quality_score = Column(Float)  # 0-100
    ai_suggestions = Column(JSON)
    detected_topics = Column(JSON, default=list)
    
    # Timestamps
    imported_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    converted_at = Column(DateTime(timezone=True))
    
    # Relationships
    client = relationship("FacebookClient", back_populates="posts")
    campaign = relationship("FacebookAdCampaign", back_populates="source_post", uselist=False)
    

class FacebookAdCampaign(Base):
    """Ad campaigns created from posts"""
    __tablename__ = "facebook_ad_campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("facebook_clients.id"), nullable=False)
    source_post_id = Column(String, ForeignKey("facebook_posts.id"))
    created_by = Column(String, ForeignKey("users.id"))
    
    # Facebook campaign data
    facebook_campaign_id = Column(String)
    facebook_adset_id = Column(String)
    facebook_ad_id = Column(String)
    
    # Campaign details
    name = Column(String, nullable=False)
    objective = Column(String, default="REACH")  # REACH, ENGAGEMENT, TRAFFIC, etc.
    status = Column(SQLEnum(AdStatus), default=AdStatus.DRAFT)
    
    # Ad content
    primary_text = Column(Text)
    headline = Column(String)
    description = Column(String)
    call_to_action = Column(String, default="LEARN_MORE")
    link_url = Column(String)
    display_link = Column(String)
    
    # Media
    creative_urls = Column(JSON, default=list)
    
    # Budget and schedule
    daily_budget = Column(Float, default=50.0)
    lifetime_budget = Column(Float)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    # Targeting
    targeting = Column(JSON, default=lambda: {
        "geo_locations": {"countries": ["US"]},
        "age_min": 18,
        "age_max": 65,
        "genders": [1, 2],  # 1=male, 2=female
        "interests": [],
        "behaviors": [],
        "custom_audiences": []
    })
    
    # A/B testing
    is_ab_test = Column(Boolean, default=False)
    ab_test_variants = Column(JSON, default=list)
    winning_variant = Column(String)
    
    # Performance metrics (updated via webhook/cron)
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)  # Click-through rate
    cpc = Column(Float, default=0.0)  # Cost per click
    cpm = Column(Float, default=0.0)  # Cost per 1000 impressions
    spend = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)  # Return on ad spend
    
    # Quality metrics
    relevance_score = Column(Float)
    quality_ranking = Column(String)
    engagement_rate_ranking = Column(String)
    conversion_rate_ranking = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    launched_at = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True))
    
    # Relationships
    client = relationship("FacebookClient", back_populates="campaigns")
    source_post = relationship("FacebookPost", back_populates="campaign")
    analytics_history = relationship("FacebookAnalytics", back_populates="campaign", cascade="all, delete-orphan")
    

class FacebookAnalytics(Base):
    """Historical analytics data for campaigns"""
    __tablename__ = "facebook_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("facebook_ad_campaigns.id"), nullable=False)
    
    # Snapshot timestamp
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    date_start = Column(DateTime(timezone=True))
    date_stop = Column(DateTime(timezone=True))
    
    # Metrics snapshot
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpm = Column(Float, default=0.0)
    spend = Column(Float, default=0.0)
    
    # Engagement metrics
    post_engagements = Column(Integer, default=0)
    page_engagements = Column(Integer, default=0)
    post_reactions = Column(Integer, default=0)
    post_comments = Column(Integer, default=0)
    post_shares = Column(Integer, default=0)
    post_saves = Column(Integer, default=0)
    
    # Video metrics (if applicable)
    video_views = Column(Integer, default=0)
    video_thruplay_watched = Column(Integer, default=0)
    video_avg_time_watched = Column(Float, default=0.0)
    
    # Conversion metrics
    conversions = Column(Integer, default=0)
    conversion_values = Column(Float, default=0.0)
    cost_per_conversion = Column(Float, default=0.0)
    
    # Demographic breakdown
    demographics = Column(JSON, default=dict)  # Age, gender, location breakdown
    
    # Device breakdown
    device_breakdown = Column(JSON, default=dict)
    
    # Relationship
    campaign = relationship("FacebookAdCampaign", back_populates="analytics_history")


class AdTemplate(Base):
    """Reusable templates for ad creation"""
    __tablename__ = "facebook_ad_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Template content
    template_type = Column(String, default="standard")  # standard, carousel, video
    primary_text_template = Column(Text)
    headline_template = Column(String)
    description_template = Column(String)
    call_to_action = Column(String)
    
    # Best practices rules
    rules = Column(JSON, default=lambda: {
        "add_emojis": True,
        "include_hashtags": True,
        "personalize_location": True,
        "urgency_phrases": ["Limited time", "Today only"],
        "social_proof": ["Join thousands", "Trusted by"]
    })
    
    # Performance benchmarks
    avg_ctr = Column(Float)
    avg_conversion_rate = Column(Float)
    times_used = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    
# Add relationship to User model
# This should be added to your existing User model in core/database.py:
# facebook_clients = relationship("FacebookClient", back_populates="user", cascade="all, delete-orphan") 