from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from core.database import Base, User


class Platform(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram" 
    TIKTOK = "tiktok"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class CampaignStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class AdTrafficClient(Base):
    __tablename__ = "ad_traffic_clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    company_name = Column(String)
    email = Column(String)
    phone = Column(String)
    website = Column(String)
    industry = Column(String)
    description = Column(Text)
    brand_voice = Column(Text)
    target_audience = Column(Text)
    brand_colors = Column(JSON, default=[])
    logo_url = Column(String)
    social_accounts = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    posts = relationship("SocialPost", back_populates="client", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="client", cascade="all, delete-orphan")


class Campaign(Base):
    __tablename__ = "ad_traffic_campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=False)
    name = Column(String, nullable=False)
    original_video_url = Column(String, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    platforms = Column(ARRAY(String), nullable=False)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.PROCESSING)
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("AdTrafficClient", back_populates="campaigns")
    video_clips = relationship("VideoClip", back_populates="campaign", cascade="all, delete-orphan")
    posts = relationship("SocialPost", back_populates="campaign")


class VideoClip(Base):
    __tablename__ = "video_clips"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    duration = Column(Float, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    video_url = Column(String, nullable=False)
    thumbnail_url = Column(String)
    platform_versions = Column(JSON, default={})
    suggested_caption = Column(Text)
    suggested_hashtags = Column(ARRAY(String), default=[])
    content_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="video_clips")


class SocialPost(Base):
    __tablename__ = "social_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    video_clip_id = Column(String, ForeignKey("video_clips.id"))
    content = Column(Text, nullable=False)
    platforms = Column(ARRAY(String), nullable=False)
    media_urls = Column(ARRAY(String), default=[])
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT)
    published_at = Column(DateTime(timezone=True))
    platform_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("AdTrafficClient", back_populates="posts")
    campaign = relationship("Campaign", back_populates="posts")
    video_clip = relationship("VideoClip") 