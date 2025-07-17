from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from core.database import Base
import uuid
from datetime import datetime

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
    
    # Social Media Accounts
    facebook_page_id = Column(String)
    facebook_page_name = Column(String)
    facebook_access_token = Column(Text)  # Encrypted in production
    instagram_account_id = Column(String)
    instagram_username = Column(String)
    
    # Additional Info
    industry = Column(String)
    description = Column(Text)
    brand_voice = Column(Text)
    target_audience = Column(Text)
    brand_colors = Column(JSON)  # Store as array of hex colors
    logo_url = Column(String)
    
    # Settings
    auto_post_enabled = Column(Boolean, default=False)
    default_post_times = Column(JSON)  # Store preferred posting times
    hashtag_sets = Column(JSON)  # Store commonly used hashtag groups
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    video_clips = relationship("VideoClip", back_populates="client")
    campaigns = relationship("Campaign", back_populates="client")
    scheduled_posts = relationship("ScheduledPost", back_populates="client")


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)
    
    # Post Content
    content = Column(Text, nullable=False)
    media_urls = Column(JSON)  # Array of URLs to images/videos
    video_clip_ids = Column(JSON)  # Array of video clip IDs
    
    # Platform Details
    platforms = Column(JSON, nullable=False)  # ["facebook", "instagram"]
    platform_specific_content = Column(JSON)  # Platform-specific modifications
    
    # Scheduling
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")  # scheduled, publishing, published, failed
    published_at = Column(DateTime)
    
    # Publishing Results
    facebook_post_id = Column(String)
    instagram_post_id = Column(String)
    error_message = Column(Text)
    engagement_metrics = Column(JSON)  # Store likes, comments, shares
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("AdTrafficClient", back_populates="scheduled_posts") 