from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

class PersonalizerProject(Base):
    __tablename__ = "personalizer_projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Project data
    template_used = Column(Text)  # The template/content used
    generation_goal = Column(Text)  # The AI instructions
    csv_headers = Column(JSON)  # Original CSV headers
    row_count = Column(Integer)  # Number of rows processed
    
    # File references
    original_csv_url = Column(String)  # URL to original CSV
    generated_csv_url = Column(String)  # URL to generated CSV
    
    # Status
    status = Column(String, default="completed")  # completed, processing, failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="personalizer_projects") 