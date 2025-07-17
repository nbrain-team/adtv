from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime

from core import auth
from core.database import get_db, User
from . import schemas
from . import processor
from . import models

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = "uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.VideoJobResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    platforms: str = "instagram,youtube,facebook",
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Upload a video and start processing"""
    
    # Validate video file
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video file.")
    
    # Check file size (500MB limit)
    if video.size > 500 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 500MB.")
    
    # Save video file
    job_id = str(uuid.uuid4())
    file_extension = os.path.splitext(video.filename)[1]
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_extension}")
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    # Create job in database
    job = models.VideoProcessingJob(
        id=job_id,
        user_id=current_user.id,
        filename=video.filename,
        file_path=video_path,
        status="analyzing",
        platforms=platforms.split(","),
        created_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    
    # Start processing in background
    background_tasks.add_task(
        processor.process_video,
        job_id=job_id,
        video_path=video_path,
        platforms=platforms.split(",")
    )
    
    return schemas.VideoJobResponse(
        jobId=job_id,
        status="analyzing",
        progress=0
    )

@router.get("/status/{job_id}", response_model=schemas.VideoJobStatus)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get the status of a video processing job"""
    
    job = db.query(models.VideoProcessingJob).filter(
        models.VideoProcessingJob.id == job_id,
        models.VideoProcessingJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get clips for this job
    clips = db.query(models.VideoClip).filter(
        models.VideoClip.job_id == job_id
    ).all()
    
    return schemas.VideoJobStatus(
        jobId=job.id,
        status=job.status,
        progress=job.progress,
        error=job.error_message,
        clips=[
            schemas.VideoClipResponse(
                id=clip.id,
                title=clip.title,
                description=clip.description,
                duration=clip.duration,
                startTime=clip.start_time,
                endTime=clip.end_time,
                platform=clip.platform,
                thumbnail=f"/api/video-processor/thumbnail/{clip.id}",
                status="ready"
            )
            for clip in clips
        ]
    )

@router.get("/download/{clip_id}")
async def download_clip(
    clip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Download a processed video clip"""
    
    clip = db.query(models.VideoClip).join(
        models.VideoProcessingJob
    ).filter(
        models.VideoClip.id == clip_id,
        models.VideoProcessingJob.user_id == current_user.id
    ).first()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if not os.path.exists(clip.file_path):
        raise HTTPException(status_code=404, detail="Clip file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        clip.file_path,
        media_type="video/mp4",
        filename=f"{clip.title}_{clip.platform}.mp4"
    )

@router.get("/thumbnail/{clip_id}")
async def get_thumbnail(
    clip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get thumbnail for a video clip"""
    
    clip = db.query(models.VideoClip).join(
        models.VideoProcessingJob
    ).filter(
        models.VideoClip.id == clip_id,
        models.VideoProcessingJob.user_id == current_user.id
    ).first()
    
    if not clip or not clip.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        clip.thumbnail_path,
        media_type="image/jpeg"
    ) 