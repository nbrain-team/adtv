"""
Database Models for Marketing Campaign Generator
"""
from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean, ForeignKey, Integer, Float, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"

class ContentStatus(enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class Platform(enum.Enum):
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    EMAIL = "email"

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    industry = Column(String)
    website = Column(String)
    description = Column(Text)
    
    # Client preferences and data
    brand_voice = Column(Text)
    target_audience = Column(JSON)  # Demographics, interests, etc.
    keywords = Column(JSON)  # List of relevant keywords
    competitors = Column(JSON)  # List of competitor info
    
    # Social media accounts
    social_accounts = Column(JSON)  # {platform: account_info}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"))
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="client")
    documents = relationship("ClientDocument", back_populates="client")

class ClientDocument(Base):
    __tablename__ = "client_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("clients.id"))
    
    filename = Column(String, nullable=False)
    file_type = Column(String)  # pdf, docx, txt, etc.
    file_path = Column(String)  # S3 or local path
    
    # Extracted content for embeddings
    content = Column(Text)
    embedding_id = Column(String)  # Pinecone ID
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String, ForeignKey("users.id"))
    
    # Relationships
    client = relationship("Client", back_populates="documents")

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("clients.id"))
    
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Campaign configuration
    topics = Column(JSON)  # List of up to 5 topics
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Status tracking
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    
    # Approval workflow
    submitted_for_approval = Column(DateTime)
    approved_by = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"))
    
    # Relationships
    client = relationship("Client", back_populates="campaigns")
    content_items = relationship("ContentItem", back_populates="campaign")
    analytics = relationship("CampaignAnalytics", back_populates="campaign")

class ContentItem(Base):
    __tablename__ = "content_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Content details
    platform = Column(SAEnum(Platform), nullable=False)
    content_type = Column(String)  # post, story, email, etc.
    
    # Generated content
    title = Column(String)  # For emails
    content = Column(Text, nullable=False)
    media_urls = Column(JSON)  # List of image/video URLs
    hashtags = Column(JSON)  # List of hashtags
    
    # Scheduling
    scheduled_date = Column(DateTime)
    published_date = Column(DateTime)
    
    # Status
    status = Column(SAEnum(ContentStatus), default=ContentStatus.DRAFT)
    
    # Platform-specific IDs
    platform_post_id = Column(String)  # Facebook post ID, Tweet ID, etc.
    
    # AI Generation metadata
    prompt_used = Column(Text)
    model_used = Column(String)
    generation_params = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="content_items")
    analytics = relationship("ContentAnalytics", back_populates="content_item")

class ContentAnalytics(Base):
    __tablename__ = "content_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_item_id = Column(String, ForeignKey("content_items.id"))
    
    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    
    # Email-specific metrics
    opens = Column(Integer, default=0)
    click_through_rate = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    
    # Calculated metrics
    engagement_rate = Column(Float, default=0.0)
    
    # Timestamp
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="analytics")

class CampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Aggregate metrics
    total_reach = Column(Integer, default=0)
    total_engagement = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    
    # Platform breakdown
    platform_metrics = Column(JSON)  # {platform: {metric: value}}
    
    # ROI metrics
    estimated_value = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    
    # Timestamp
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    provider = Column(String)  # openai, anthropic, etc.
    model_id = Column(String)  # gpt-4, claude-3, etc.
    
    # Configuration
    default_params = Column(JSON)
    cost_per_token = Column(Float)
    
    # Usage tracking
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow) 