"""
Database models and configuration for the Realtor Importer module
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Create a separate Base for realtor importer tables
Base = declarative_base()

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
engine = create_engine(DATABASE_URL)

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