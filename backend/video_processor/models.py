from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer, Text
from sqlalchemy.orm import relationship
from core.database import Base
import uuid
from datetime import datetime

class VideoProcessingJob(Base):
    __tablename__ = "video_processing_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=True)  # Link to client
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, analyzing, extracting, complete, failed
    progress = Column(Integer, default=0)
    platforms = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clips = relationship("VideoClip", back_populates="job", cascade="all, delete-orphan")

class VideoClip(Base):
    __tablename__ = "video_clips"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("video_processing_jobs.id"), nullable=False)
    client_id = Column(String, ForeignKey("ad_traffic_clients.id"), nullable=True)  # Link to client
    title = Column(String, nullable=False)
    description = Column(Text)
    duration = Column(Float, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    platform = Column(String, nullable=False)  # instagram, youtube, facebook
    file_path = Column(String)
    thumbnail_path = Column(String)
    clip_metadata = Column(JSON)  # Store platform-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("VideoProcessingJob", back_populates="clips")
    client = relationship("AdTrafficClient", back_populates="video_clips") 