from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class ProcessedJob(Base):
    """Represents a merged/processed job from multiple scraping jobs"""
    __tablename__ = "processed_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    source_job_ids = Column(JSON, nullable=False)  # List of source scraping job IDs
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    
    # Processing stats
    total_contacts = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    emails_validated = Column(Integer, default=0)
    websites_crawled = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    merged_contacts = relationship("MergedContact", back_populates="processed_job", cascade="all, delete-orphan")


class MergedContact(Base):
    """Represents a merged contact from multiple sources with enriched data"""
    __tablename__ = "merged_contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    processed_job_id = Column(String, ForeignKey("processed_jobs.id"), nullable=False)
    
    # Basic info (merged from best available data)
    first_name = Column(String)
    last_name = Column(String)
    company = Column(String)
    city = Column(String)
    state = Column(String)
    dma = Column(String)
    
    # Contact info
    cell_phone = Column(String)
    phone2 = Column(String)
    email = Column(String)
    personal_email = Column(String)
    
    # Online presence
    agent_website = Column(String)
    facebook_profile = Column(String)
    fb_or_website = Column(String)
    profile_url = Column(String)
    
    # Sales data (best/most complete from sources)
    years_exp = Column(Integer)
    closed_sales = Column(String)
    total_value = Column(String)
    price_range = Column(String)
    average_price = Column(String)
    
    # Enriched data
    website_content = Column(Text)  # Crawled website content
    email_valid = Column(Boolean)  # ZeroBounce validation result
    email_score = Column(Float)  # ZeroBounce score
    email_status = Column(String)  # ZeroBounce status (valid, invalid, spam, etc.)
    
    # Metadata
    source_count = Column(Integer, default=1)  # How many sources this contact came from
    merge_confidence = Column(Float, default=1.0)  # Confidence in the merge (0-1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    processed_job = relationship("ProcessedJob", back_populates="merged_contacts") 