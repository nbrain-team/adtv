import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, func, Enum as SAEnum, BigInteger, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import enum

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment. Please set it.")

# Increase pool size to support concurrent enrichment operations
# pool_size: number of permanent connections (increased from default 5 to 20)
# max_overflow: additional connections that can be created (increased from default 10 to 30)
# This allows up to 50 total connections for high concurrency operations
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,  # Verify connections are alive before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # User profile fields
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    
    # Role and permissions
    role = Column(String, default="user")  # "user" or "admin"
    permissions = Column(JSON, default=lambda: {"chat": True, "campaigns": False, "ad-traffic": False})  # Module access permissions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # User relationships
    conversations = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    template_agents = relationship("TemplateAgent", back_populates="user", cascade="all, delete-orphan")
    email_templates = relationship("EmailTemplate", back_populates="creator", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    campaign_templates = relationship("CampaignTemplate", back_populates="user", cascade="all, delete-orphan")
    facebook_clients = relationship("FacebookClient", back_populates="user", cascade="all, delete-orphan")
    # Note: ad_traffic_clients relationship is defined on the AdTrafficClient model to avoid circular imports


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    messages = Column(JSON, nullable=False)
    
    user_id = Column(String, ForeignKey('users.id'))
    user = relationship("User", back_populates="conversations")


# --- Realtor Importer Models ---

class ScrapingJobStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)  # User-defined name for the job
    start_url = Column(String, nullable=False)
    status = Column(SAEnum(ScrapingJobStatus), default=ScrapingJobStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)  # Store error messages

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    realtor_contacts = relationship("RealtorContact", back_populates="job", cascade="all, delete-orphan")

class RealtorContact(Base):
    __tablename__ = "realtor_contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    job_id = Column(String, ForeignKey("scraping_jobs.id"), nullable=False)
    job = relationship("ScrapingJob", back_populates="realtor_contacts")

    # Scraped data from the user's spec
    dma = Column(String, nullable=True)
    source = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    profile_url = Column(String, nullable=False, index=True)
    cell_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    agent_website = Column(String, nullable=True)
    
    # Step 2 fields - extracted from agent's website
    phone2 = Column(String, nullable=True)  # Phone from agent website
    personal_email = Column(String, nullable=True)  # Personal email from agent website
    facebook_profile = Column(String, nullable=True)  # Facebook profile link
    
    years_exp = Column(Integer, nullable=True)
    fb_or_website = Column(String, nullable=True)
    
    seller_deals_total_deals = Column(Integer, nullable=True)
    seller_deals_total_value = Column(BigInteger, nullable=True)
    seller_deals_avg_price = Column(BigInteger, nullable=True)
    
    buyer_deals_total_deals = Column(Integer, nullable=True)
    buyer_deals_total_value = Column(BigInteger, nullable=True)
    buyer_deals_avg_price = Column(BigInteger, nullable=True)
    
    # Sales stats from the new scraper
    closed_sales = Column(String, nullable=True)
    total_value = Column(String, nullable=True)
    price_range = Column(String, nullable=True)
    average_price = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TemplateAgent(Base):
    __tablename__ = "template_agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = Column(String, ForeignKey("users.id"))  # Changed from user_id to created_by
    name = Column(String, nullable=False)
    description = Column(Text)
    prompt_template = Column(Text, nullable=False)
    example_input = Column(Text)
    example_output = Column(Text)
    is_active = Column(Boolean, default=True)  # Added is_active field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="template_agents")

# Campaign Models
class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)  # Associate Producer name
    owner_email = Column(String, nullable=False)
    owner_phone = Column(String, nullable=True)  # Phone number for the owner
    video_link = Column(String, nullable=True)  # Video link for email template
    event_link = Column(String, nullable=True)  # Event information link
    city = Column(String, nullable=True)  # City for [[City]] merge field
    state = Column(String, nullable=True)  # State for [[State]] merge field
    launch_date = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=False)  # 'virtual' or 'in_person'
    event_date = Column(DateTime, nullable=False)  # Keep for backward compatibility
    event_times = Column(JSON, default=[])  # Keep for backward compatibility
    event_slots = Column(JSON, default=[])  # New: Array of {date, time, calendly_link} objects
    target_cities = Column(Text)  # Multi-line text for locations to scrape
    hotel_name = Column(String)
    hotel_address = Column(String)
    calendly_link = Column(String)  # Main calendly link for in-person events
    status = Column(String, default='draft')  # draft, enriching, ready_for_personalization, emails_generated, ready_to_send, sending, sent
    
    # Analytics
    total_contacts = Column(Integer, default=0)
    enriched_contacts = Column(Integer, default=0)
    failed_enrichments = Column(Integer, default=0)
    emails_generated = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    
    # Email template
    email_template = Column(Text)
    email_subject = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    contacts = relationship("CampaignContact", back_populates="campaign", cascade="all, delete-orphan")
    analytics = relationship("CampaignAnalytics", back_populates="campaign", uselist=False)
    email_templates = relationship("CampaignEmailTemplate", back_populates="campaign", cascade="all, delete-orphan")

class CampaignEmailTemplate(Base):
    __tablename__ = "campaign_email_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    template_type = Column(String, default='general')  # general, rsvp_confirmation, reminder, follow_up
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="email_templates")

class CampaignContact(Base):
    __tablename__ = "campaign_contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Original data
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    company = Column(String)
    title = Column(String)
    phone = Column(String)
    neighborhood = Column(String)  # Add neighborhood field
    state = Column(String)  # Add state field for proper storage
    geocoded_address = Column(String)  # Google Maps compatible address
    
    # Enriched data
    enriched_company = Column(String)
    enriched_title = Column(String)
    enriched_phone = Column(String)
    enriched_linkedin = Column(String)
    enriched_website = Column(String)
    enriched_industry = Column(String)
    enriched_company_size = Column(String)
    enriched_location = Column(String)
    
    # Email personalization
    personalized_email = Column(Text)
    personalized_subject = Column(String)
    
    # Status tracking
    enrichment_status = Column(String, default='pending')  # pending, processing, success, failed
    enrichment_error = Column(Text)
    email_status = Column(String, default='pending')  # pending, generated, sent, failed
    email_sent_at = Column(DateTime)
    
    # Flags
    excluded = Column(Boolean, default=False)
    manually_edited = Column(Boolean, default=False)
    
    # RSVP tracking
    is_rsvp = Column(Boolean, default=False)
    rsvp_status = Column(String, default=None)  # None, attended, no_show, signed_agreement, cancelled
    rsvp_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="contacts")

class CampaignTemplate(Base):
    __tablename__ = "campaign_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Template data
    event_type = Column(String)
    email_template = Column(Text)
    email_subject = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="campaign_templates")

class CampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Timestamps for different stages
    timestamp = Column(DateTime, default=datetime.utcnow)
    enrichment_start_time = Column(DateTime)
    enrichment_end_time = Column(DateTime)
    email_generation_start_time = Column(DateTime)
    email_generation_end_time = Column(DateTime)
    sending_start_time = Column(DateTime)  # Changed from send_start_time
    sending_end_time = Column(DateTime)    # Changed from send_end_time
    
    # Metrics
    contacts_uploaded = Column(Integer, default=0)
    contacts_enriched = Column(Integer, default=0)
    contacts_with_email = Column(Integer, default=0)
    contacts_with_phone = Column(Integer, default=0)
    emails_generated = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    
    # Success rates
    enrichment_success_rate = Column(Float, default=0.0)
    email_capture_rate = Column(Float, default=0.0)
    phone_capture_rate = Column(Float, default=0.0)
    email_generation_rate = Column(Float, default=0.0)
    email_send_rate = Column(Float, default=0.0)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    
    # Relationship
    creator = relationship("User", back_populates="email_templates")

class CustomerServiceCommunication(Base):
    __tablename__ = "customer_service_communications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # e.g., Billing, Technical, Onboarding
    status = Column(String, nullable=True)    # e.g., Open, Resolved, Archived
    channel = Column(String, nullable=True)   # e.g., Email, Chat, Phone, Podio
    tags = Column(JSON, default=list)
    podio_item_id = Column(String, nullable=True)
    source_file = Column(String, nullable=True)
    author = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional linkage to user who imported/owns the record
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("User")


def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables if they don't exist."""
    # Import models to ensure they're registered with Base
    from realtor_importer.models import ProcessedJob, MergedContact
    from core.personalizer_models import PersonalizerProject
    from contact_enricher.models import EnrichmentProject, EnrichedContact, EnrichmentAPIConfig
    Base.metadata.create_all(bind=engine) 