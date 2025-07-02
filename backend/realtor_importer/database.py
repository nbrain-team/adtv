"""
Database models and configuration for the Realtor Importer module
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Import Base and engine from the main database module
from core.database import Base, engine

class ScrapeJob(Base):
    """Model for tracking scraping jobs"""
    __tablename__ = "scrape_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    start_url = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    error_message = Column(Text, nullable=True)
    leads_found = Column(Integer, default=0)
    
    # Relationship to leads
    leads = relationship("RealtorLead", back_populates="job", cascade="all, delete-orphan")

# Create tables
Base.metadata.create_all(bind=engine) 