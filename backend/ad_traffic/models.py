from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean, Integer, Float, Enum as SAEnum
from sqlalchemy.orm import relationship
from core.database import Base
import uuid
from datetime import datetime
import enum

class PlatformType(enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"

class PostStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class CampaignStatus(enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class AdTrafficClient(Base):
    __tablename__ = "ad_traffic_clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Basic Information
    name = Column(String, nullable=False)
    company_name = Column(String)
    email = Column(String)
    phone = Column(String)
    website = Column(String)
    
    # Social Media Accounts (store connection details later)
    social_accounts = Column(JSON, default=dict)  # {platform: account_info}
    
    # Additional Info
    industry = Column(String)
    description = Column(Text)
    brand_voice = Column(Text)
    target_audience = Column(Text)
    brand_colors = Column(JSON)  # Array of hex colors
    logo_url = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = relationship("SocialMediaPost", back_populates="client", cascade="all, delete-orphan")
    campaigns = relationship("VideoClipCampaign", back_populates="client", cascade="all, delete-orphan")

class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("video_clip_campaigns.id"), nullable=True)
    
    # Post Content
    content = Column(Text, nullable=False)
    platforms = Column(JSON, nullable=False)  # List of platforms ["facebook", "instagram", "tiktok"]
    
    # Media
    media_urls = Column(JSON, default=list)  # List of image/video URLs
    video_clip_id = Column(String, ForeignKey("video_clips.id"), nullable=True)
    
    # Scheduling
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(SAEnum(PostStatus), default=PostStatus.DRAFT)
    published_at = Column(DateTime, nullable=True)
    
    # Platform-specific data
    platform_data = Column(JSON, default=dict)  # Store platform-specific modifications
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("AdTrafficClient", back_populates="posts")
    campaign = relationship("VideoClipCampaign", back_populates="posts")
    video_clip = relationship("VideoClip", back_populates="posts")

class VideoClipCampaign(Base):
    __tablename__ = "video_clip_campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=False)
    
    # Campaign Info
    name = Column(String, nullable=False)
    original_video_url = Column(String, nullable=False)
    duration_weeks = Column(Integer, nullable=False)  # 1-8 weeks
    platforms = Column(JSON, nullable=False)  # Selected platforms
    
    # Processing Status
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.PROCESSING)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("AdTrafficClient", back_populates="campaigns")
    clips = relationship("VideoClip", back_populates="campaign", cascade="all, delete-orphan")
    posts = relationship("SocialMediaPost", back_populates="campaign")

class VideoClip(Base):
    __tablename__ = "video_clips"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("video_clip_campaigns.id"), nullable=False)
    
    # Clip Info
    title = Column(String, nullable=False)
    description = Column(Text)
    duration = Column(Float, nullable=False)  # seconds
    start_time = Column(Float, nullable=False)  # seconds from original
    end_time = Column(Float, nullable=False)  # seconds from original
    
    # File paths
    video_url = Column(String, nullable=False)
    thumbnail_url = Column(String)
    
    # Platform optimization
    platform_versions = Column(JSON, default=dict)  # {platform: {url, aspect_ratio, etc}}
    
    # AI-generated content
    suggested_caption = Column(Text)
    suggested_hashtags = Column(JSON, default=list)
    content_type = Column(String)  # testimonial, showcase, process, etc
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("VideoClipCampaign", back_populates="clips")
    posts = relationship("SocialMediaPost", back_populates="video_clip") 