from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Import the enum from the database model to reuse it
from core.database import ScrapingJobStatus

# ====================
# Realtor Contact Data
# ====================

class RealtorContactBase(BaseModel):
    dma: Optional[str] = None
    source: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    profile_url: str
    cell_phone: Optional[str] = None
    email: Optional[str] = None
    years_exp: Optional[int] = None
    fb_or_website: Optional[str] = None
    seller_deals_total_deals: Optional[int] = None
    seller_deals_total_value: Optional[int] = None
    seller_deals_avg_price: Optional[int] = None
    buyer_deals_total_deals: Optional[int] = None
    buyer_deals_total_value: Optional[int] = None
    buyer_deals_avg_price: Optional[int] = None

class RealtorContact(RealtorContactBase):
    id: str
    job_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ====================
#   Scraping Job
# ====================

class ScrapeRequest(BaseModel):
    url: str

class RealtorContactResponse(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    cell_phone: Optional[str] = None
    email: Optional[str] = None
    profile_url: Optional[str] = None

class ScrapingJobResponse(BaseModel):
    id: int
    start_url: str
    status: str
    created_at: datetime
    contact_count: int = 0

class ScrapingJobDetail(BaseModel):
    id: int
    start_url: str
    status: str
    created_at: datetime
    error_message: Optional[str] = None
    realtor_contacts: List[RealtorContactResponse] = []

class ScrapingJobBase(BaseModel):
    id: str
    status: ScrapingJobStatus
    start_url: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class ScrapingJob(ScrapingJobBase):
    realtor_contacts: List[RealtorContact] = []

    class Config:
        from_attributes = True

class ScrapingJobSummary(ScrapingJobBase):
    contact_count: int
    
    class Config:
        from_attributes = True 