from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class EnrichmentProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}


class EnrichmentProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class EnrichmentProject(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    original_filename: Optional[str]
    original_row_count: int
    status: str
    processed_rows: int
    enriched_rows: int
    emails_found: int
    phones_found: int
    facebook_data_found: int
    websites_scraped: int
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class EnrichedContactBase(BaseModel):
    name: Optional[str]
    company: Optional[str]
    city: Optional[str]
    state: Optional[str]
    agent_website: Optional[str]
    facebook_profile: Optional[str]


class EnrichedContact(EnrichedContactBase):
    id: str
    project_id: str
    original_data: Dict[str, Any]
    
    # Enriched data
    email_found: Optional[str]
    email_confidence: float
    email_source: Optional[str]
    email_valid: Optional[bool]
    
    phone_found: Optional[str]
    phone_confidence: float
    phone_source: Optional[str]
    phone_formatted: Optional[str]
    
    facebook_followers: Optional[int]
    facebook_recent_post: Optional[str]
    facebook_post_date: Optional[datetime]
    facebook_engagement: Optional[Dict[str, Any]]
    
    website_emails: List[str]
    website_phones: List[str]
    website_social_links: Dict[str, str]
    website_scraped: bool
    
    data_completeness_score: float
    confidence_score: float
    
    enriched_at: datetime
    last_updated: datetime
    errors: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    project_id: str
    row_count: int
    columns: List[str]
    preview_rows: List[Dict[str, Any]]


class EnrichmentProgress(BaseModel):
    project_id: str
    status: str
    processed_rows: int
    total_rows: int
    emails_found: int
    phones_found: int
    facebook_data_found: int
    websites_scraped: int
    current_contact: Optional[str]
    estimated_time_remaining: Optional[int]  # seconds


class ExportRequest(BaseModel):
    include_original: bool = True
    only_enriched: bool = False
    format: str = "csv"  # For future: could support json, xlsx, etc.


class APIConfigUpdate(BaseModel):
    serp_api_key: Optional[str] = None
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None


class SearchStrategy(BaseModel):
    email_search_patterns: List[str] = [
        "{name} {company} email",
        "{name} {city} contact email",
        "site:{website} contact email",
        "{name} realtor email {city}"
    ]
    phone_search_patterns: List[str] = [
        "{name} {company} phone",
        "{name} {city} phone number",
        "{name} real estate agent contact"
    ]
    confidence_thresholds: Dict[str, float] = {
        "email": 0.7,
        "phone": 0.8
    } 