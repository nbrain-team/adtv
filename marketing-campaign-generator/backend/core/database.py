"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/marketing_campaigns"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for serverless
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from ..models.database import Base
    Base.metadata.create_all(bind=engine) 