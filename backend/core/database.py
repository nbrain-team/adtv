import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, func, Enum as SAEnum, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import enum

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment. Please set it.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    conversations = relationship("ChatSession", back_populates="user")


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

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    start_url = Column(String, nullable=False)
    status = Column(SAEnum(ScrapingJobStatus), default=ScrapingJobStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

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
    years_exp = Column(Integer, nullable=True)
    fb_or_website = Column(String, nullable=True)
    
    seller_deals_total_deals = Column(Integer, nullable=True)
    seller_deals_total_value = Column(BigInteger, nullable=True)
    seller_deals_avg_price = Column(BigInteger, nullable=True)
    
    buyer_deals_total_deals = Column(Integer, nullable=True)
    buyer_deals_total_value = Column(BigInteger, nullable=True)
    buyer_deals_avg_price = Column(BigInteger, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(bind=engine) 