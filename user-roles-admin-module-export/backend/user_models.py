"""
User and Authentication Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

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
    permissions = Column(JSON, default=lambda: {"chat": True})  # Module access permissions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True) 