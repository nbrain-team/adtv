from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import os
import shutil

from core.database import get_db, User
from core.auth import get_current_active_user
from . import models, schemas, services

router = APIRouter(tags=["ad-traffic"])


# Client endpoints
@router.get("/clients", response_model=List[schemas.Client])
async def get_clients(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all clients for the current user"""
    return services.get_user_clients(db, current_user.id)


@router.post("/clients", response_model=schemas.Client)
async def create_client(
    client: schemas.ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new client"""
    return services.create_client(db, client, current_user.id)


@router.get("/clients/{client_id}", response_model=schemas.Client)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific client"""
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/clients/{client_id}", response_model=schemas.Client)
async def update_client(
    client_id: str,
    client_update: schemas.ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a client"""
    client = services.update_client(db, client_id, client_update, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a client"""
    if not services.delete_client(db, client_id, current_user.id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}


# Post endpoints
@router.get("/clients/{client_id}/calendar", response_model=List[schemas.SocialPost])
async def get_client_posts(
    client_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all posts for a client within date range"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    posts = services.get_client_posts(db, client_id, start_date, end_date)
    
    # Add campaign names to posts
    for post in posts:
        if post.campaign_id:
            campaign = db.query(models.Campaign).filter_by(id=post.campaign_id).first()
            if campaign:
                post.campaign_name = campaign.name
    
    return posts


@router.post("/clients/{client_id}/posts", response_model=schemas.SocialPost)
async def create_post(
    client_id: str,
    post: schemas.PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new post for a client"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return services.create_post(db, post, client_id)


@router.put("/posts/{post_id}", response_model=schemas.SocialPost)
async def update_post(
    post_id: str,
    post_update: schemas.PostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a post"""
    post = services.update_post(db, post_id, post_update, current_user.id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a post"""
    if not services.delete_post(db, post_id, current_user.id):
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}


# Campaign endpoints
@router.get("/clients/{client_id}/campaigns", response_model=List[schemas.Campaign])
async def get_client_campaigns(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns for a client"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    campaigns = services.get_client_campaigns(db, client_id)
    return campaigns

@router.post("/clients/{client_id}/campaigns")
async def create_campaign(
    client_id: str,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    duration_weeks: int = Form(...),
    platforms: List[str] = Form(...),
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new video campaign"""
    # Verify client ownership
    client = services.get_client(db, client_id, current_user.id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Validate video file
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid video file")
    
    # Save video file
    upload_dir = f"uploads/campaigns/{client_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(video.filename)[1]
    video_filename = f"{uuid.uuid4()}{file_extension}"
    video_path = os.path.join(upload_dir, video_filename)
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    # Create campaign
    campaign_data = schemas.CampaignCreate(
        name=name,
        duration_weeks=duration_weeks,
        platforms=[schemas.Platform(p) for p in platforms]
    )
    
    campaign = services.create_campaign(db, campaign_data, client_id, video_path)
    
    # Start background processing
    background_tasks.add_task(
        services.process_campaign_video,
        db,
        campaign.id,
        video_path,
        client
    )
    
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=schemas.CampaignWithClips)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get campaign with its video clips"""
    campaign = services.get_campaign_with_clips(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.get("/campaigns/{campaign_id}/posts", response_model=List[schemas.SocialPost])
def get_campaign_posts(
    campaign_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all posts associated with a campaign"""
    posts = services.get_campaign_posts(db, campaign_id, current_user.id)
    return posts 