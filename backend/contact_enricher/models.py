from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class EnrichmentProject(Base):
    """Represents a contact enrichment project"""
    __tablename__ = "enrichment_projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Original file info
    original_filename = Column(String)
    original_row_count = Column(Integer, default=0)
    
    # Processing stats
    status = Column(String, default="pending")  # pending, processing, completed, failed
    processed_rows = Column(Integer, default=0)
    enriched_rows = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)  # Store error messages
    
    # Results
    emails_found = Column(Integer, default=0)
    phones_found = Column(Integer, default=0)
    facebook_data_found = Column(Integer, default=0)
    websites_scraped = Column(Integer, default=0)
    
    # Configuration
    config = Column(JSON, default={})  # Search settings, API keys, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    contacts = relationship("EnrichedContact", back_populates="project", cascade="all, delete-orphan")


class EnrichedContact(Base):
    """Represents an enriched contact record"""
    __tablename__ = "enriched_contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("enrichment_projects.id"), nullable=False)
    
    # Original data
    original_data = Column(JSON)  # Store all original CSV fields
    
    # Key fields from CSV
    name = Column(String)
    company = Column(String)
    city = Column(String)
    state = Column(String)
    agent_website = Column(String)
    facebook_profile = Column(String)
    
    # Enriched email data
    email_found = Column(String)
    email_confidence = Column(Float, default=0.0)  # 0-100
    email_source = Column(String)  # google, website, etc.
    email_valid = Column(Boolean)  # From ZeroBounce validation
    email_validation_details = Column(JSON)
    
    # Enriched phone data
    phone_found = Column(String)
    phone_confidence = Column(Float, default=0.0)
    phone_source = Column(String)
    phone_formatted = Column(String)  # Standardized format
    
    # Facebook data
    facebook_followers = Column(Integer)
    facebook_recent_post = Column(Text)
    facebook_post_date = Column(DateTime)
    facebook_engagement = Column(JSON)  # likes, comments, shares
    facebook_page_info = Column(JSON)  # Additional page data
    facebook_last_checked = Column(DateTime)
    
    # Website scraping data
    website_emails = Column(JSON, default=[])  # List of emails found on website
    website_phones = Column(JSON, default=[])  # List of phones found on website
    website_social_links = Column(JSON, default={})  # Other social media links
    website_scraped = Column(Boolean, default=False)
    website_scrape_date = Column(DateTime)
    
    # Quality metrics
    data_completeness_score = Column(Float, default=0.0)  # 0-100
    confidence_score = Column(Float, default=0.0)  # Overall confidence
    
    # Processing metadata
    enriched_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    errors = Column(JSON, default=[])  # Any errors during enrichment
    
    # Relationships
    project = relationship("EnrichmentProject", back_populates="contacts")


class EnrichmentAPIConfig(Base):
    """Stores API configurations for enrichment services"""
    __tablename__ = "enrichment_api_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Google SERP API
    serp_api_key = Column(String)
    serp_api_endpoint = Column(String, default="https://serpapi.com/search")
    serp_daily_limit = Column(Integer, default=100)
    serp_used_today = Column(Integer, default=0)
    
    # Facebook API
    facebook_app_id = Column(String)
    facebook_app_secret = Column(String)
    facebook_access_token = Column(Text)
    facebook_token_expires = Column(DateTime)
    
    # Rate limiting
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 