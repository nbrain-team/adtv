from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid
import shutil

from core import auth
from core.database import get_db, User
from . import schemas
from . import models
from . import video_processor

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = "uploads/ad_traffic"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Client endpoints
@router.get("/clients", response_model=List[schemas.ClientResponse])
async def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get all clients for the current user"""
    clients = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.user_id == current_user.id
    ).order_by(models.AdTrafficClient.created_at.desc()).all()
    
    return clients

@router.post("/clients", response_model=schemas.ClientResponse)
async def create_client(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Create a new client"""
    client = models.AdTrafficClient(
        **client_data.dict(),
        user_id=current_user.id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.put("/clients/{client_id}", response_model=schemas.ClientResponse)
async def update_client(
    client_id: str,
    client_data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Update a client"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    return client

@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Delete a client"""
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}

# Calendar/Posts endpoints
@router.get("/clients/{client_id}/calendar", response_model=List[schemas.CalendarPostResponse])
async def get_client_calendar(
    client_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get calendar posts for a client"""
    # Verify client ownership
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Build query
    query = db.query(models.SocialMediaPost).options(
        joinedload(models.SocialMediaPost.video_clip),
        joinedload(models.SocialMediaPost.campaign)
    ).filter(models.SocialMediaPost.client_id == client_id)
    
    if start_date:
        query = query.filter(models.SocialMediaPost.scheduled_time >= start_date)
    if end_date:
        query = query.filter(models.SocialMediaPost.scheduled_time <= end_date)
    
    posts = query.order_by(models.SocialMediaPost.scheduled_time).all()
    
    # Format response
    calendar_posts = []
    for post in posts:
        calendar_post = schemas.CalendarPostResponse(
            id=post.id,
            content=post.content,
            platforms=post.platforms,
            scheduled_time=post.scheduled_time,
            status=post.status.value,
            media_urls=post.media_urls or [],
            video_clip=post.video_clip,
            campaign_name=post.campaign.name if post.campaign else None
        )
        calendar_posts.append(calendar_post)
    
    return calendar_posts

@router.post("/clients/{client_id}/posts", response_model=schemas.PostResponse)
async def create_post(
    client_id: str,
    post_data: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Create a single social media post"""
    # Verify client ownership
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    post = models.SocialMediaPost(
        **post_data.dict(),
        client_id=client_id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.put("/posts/{post_id}", response_model=schemas.PostResponse)
async def update_post(
    post_id: str,
    post_data: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Update a social media post"""
    # Get post and verify ownership through client
    post = db.query(models.SocialMediaPost).join(
        models.AdTrafficClient
    ).filter(
        models.SocialMediaPost.id == post_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    update_data = post_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return post

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Delete a social media post"""
    # Get post and verify ownership through client
    post = db.query(models.SocialMediaPost).join(
        models.AdTrafficClient
    ).filter(
        models.SocialMediaPost.id == post_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

# Campaign endpoints
@router.post("/clients/{client_id}/campaigns", response_model=schemas.CampaignResponse)
async def create_campaign(
    client_id: str,
    background_tasks: BackgroundTasks,
    campaign_data: schemas.CampaignCreate = Depends(),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Create a video clip campaign"""
    # Verify client ownership
    client = db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Validate video file
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video file.")
    
    # Save video file
    campaign_id = str(uuid.uuid4())
    file_extension = os.path.splitext(video.filename)[1]
    video_path = os.path.join(UPLOAD_DIR, f"campaign_{campaign_id}{file_extension}")
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    # Create campaign
    campaign = models.VideoClipCampaign(
        id=campaign_id,
        client_id=client_id,
        name=campaign_data.name,
        original_video_url=video_path,
        duration_weeks=campaign_data.duration_weeks,
        platforms=[p.value for p in campaign_data.platforms]
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Start background processing
    background_tasks.add_task(
        video_processor.process_campaign,
        campaign_id=campaign_id,
        video_path=video_path,
        platforms=campaign_data.platforms,
        duration_weeks=campaign_data.duration_weeks
    )
    
    return campaign

@router.get("/campaigns/{campaign_id}", response_model=schemas.CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get campaign details"""
    campaign = db.query(models.VideoClipCampaign).join(
        models.AdTrafficClient
    ).filter(
        models.VideoClipCampaign.id == campaign_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.get("/campaigns/{campaign_id}/clips", response_model=List[schemas.VideoClipResponse])
async def get_campaign_clips(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get all clips from a campaign"""
    # Verify ownership
    campaign = db.query(models.VideoClipCampaign).join(
        models.AdTrafficClient
    ).filter(
        models.VideoClipCampaign.id == campaign_id,
        models.AdTrafficClient.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    clips = db.query(models.VideoClip).filter(
        models.VideoClip.campaign_id == campaign_id
    ).all()
    
    return clips 