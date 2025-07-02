"""
Models for Realtor Importer leads
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class RealtorLead(Base):
    """Model for storing scraped realtor information"""
    __tablename__ = "realtor_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"))
    
    # Basic Information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    profile_url = Column(String, nullable=False)
    
    # Location
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    dma = Column(String, nullable=True)
    
    # Contact Information
    cell_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Professional Information
    years_exp = Column(Integer, nullable=True)
    fb_or_website = Column(String, nullable=True)
    source = Column(String, default="realtor.com")
    
    # Sales Data - Seller
    seller_deals_total_deals = Column(Integer, nullable=True)
    seller_deals_total_value = Column(Integer, nullable=True)
    seller_deals_avg_price = Column(Integer, nullable=True)
    
    # Sales Data - Buyer
    buyer_deals_total_deals = Column(Integer, nullable=True)
    buyer_deals_total_value = Column(Integer, nullable=True)
    buyer_deals_avg_price = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    job = relationship("ScrapeJob", back_populates="leads") 