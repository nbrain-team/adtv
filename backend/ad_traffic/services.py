from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import uuid

from . import models, schemas
from core.database import User


# Client services
def get_user_clients(db: Session, user_id: str) -> List[models.AdTrafficClient]:
    """Get all clients for a user"""
    return db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.user_id == user_id
    ).order_by(models.AdTrafficClient.created_at.desc()).all()


def get_client(db: Session, client_id: str, user_id: str) -> Optional[models.AdTrafficClient]:
    """Get a specific client by ID and user"""
    return db.query(models.AdTrafficClient).filter(
        models.AdTrafficClient.id == client_id,
        models.AdTrafficClient.user_id == user_id
    ).first()


def create_client(db: Session, client_data: schemas.ClientCreate, user_id: str) -> models.AdTrafficClient:
    """Create a new client"""
    client = models.AdTrafficClient(
        **client_data.dict(),
        user_id=user_id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(
    db: Session, 
    client_id: str, 
    client_data: schemas.ClientUpdate, 
    user_id: str
) -> Optional[models.AdTrafficClient]:
    """Update a client"""
    client = get_client(db, client_id, user_id)
    if not client:
        return None
    
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: str, user_id: str) -> bool:
    """Delete a client"""
    client = get_client(db, client_id, user_id)
    if not client:
        return False
    
    db.delete(client)
    db.commit()
    return True


# Post services
def get_client_posts(
    db: Session, 
    client_id: str, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[models.SocialPost]:
    """Get posts for a client within date range"""
    query = db.query(models.SocialPost).options(
        joinedload(models.SocialPost.video_clip),
        joinedload(models.SocialPost.campaign)
    ).filter(models.SocialPost.client_id == client_id)
    
    if start_date:
        query = query.filter(models.SocialPost.scheduled_time >= start_date)
    if end_date:
        query = query.filter(models.SocialPost.scheduled_time <= end_date)
    
    return query.order_by(models.SocialPost.scheduled_time).all()


def create_post(db: Session, post_data: schemas.PostCreate, client_id: str) -> models.SocialPost:
    """Create a new post"""
    post = models.SocialPost(
        **post_data.dict(),
        client_id=client_id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Load relationships
    if post.video_clip_id:
        post.video_clip = db.query(models.VideoClip).filter_by(id=post.video_clip_id).first()
    
    return post


def update_post(
    db: Session, 
    post_id: str, 
    post_data: schemas.PostUpdate,
    user_id: str
) -> Optional[models.SocialPost]:
    """Update a post"""
    post = db.query(models.SocialPost).join(
        models.AdTrafficClient
    ).filter(
        models.SocialPost.id == post_id,
        models.AdTrafficClient.user_id == user_id
    ).first()
    
    if not post:
        return None
    
    update_data = post_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: str, user_id: str) -> bool:
    """Delete a post"""
    post = db.query(models.SocialPost).join(
        models.AdTrafficClient
    ).filter(
        models.SocialPost.id == post_id,
        models.AdTrafficClient.user_id == user_id
    ).first()
    
    if not post:
        return False
    
    db.delete(post)
    db.commit()
    return True


# Campaign services
def create_campaign(
    db: Session, 
    campaign_data: schemas.CampaignCreate,
    client_id: str,
    video_path: str
) -> models.Campaign:
    """Create a new campaign"""
    campaign = models.Campaign(
        **campaign_data.dict(),
        client_id=client_id,
        original_video_url=video_path
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def get_campaign_with_clips(
    db: Session, 
    campaign_id: str, 
    user_id: str
) -> Optional[models.Campaign]:
    """Get campaign with video clips"""
    campaign = db.query(models.Campaign).join(
        models.AdTrafficClient
    ).options(
        joinedload(models.Campaign.video_clips)
    ).filter(
        models.Campaign.id == campaign_id,
        models.AdTrafficClient.user_id == user_id
    ).first()
    
    return campaign


def get_campaign_posts(db: Session, campaign_id: str, user_id: str) -> List[models.SocialPost]:
    """Get all posts associated with a campaign"""
    # First verify the campaign belongs to the user
    campaign = db.query(models.Campaign).join(
        models.AdTrafficClient
    ).filter(
        models.Campaign.id == campaign_id,
        models.AdTrafficClient.user_id == user_id
    ).first()
    
    if not campaign:
        return []
    
    # Get all posts for the campaign
    posts = db.query(models.SocialPost).filter(
        models.SocialPost.campaign_id == campaign_id
    ).order_by(models.SocialPost.scheduled_time).all()
    
    return posts


# Background processing
async def process_campaign_video(
    db: Session,
    campaign_id: str,
    video_path: str,
    client: models.AdTrafficClient
):
    """Process campaign video (placeholder for video processing logic)"""
    # This is where you would integrate with the video processing backend
    # For now, we'll just update the campaign status
    
    try:
        # Update progress
        campaign = db.query(models.Campaign).filter_by(id=campaign_id).first()
        if not campaign:
            return
        
        campaign.status = models.CampaignStatus.PROCESSING
        campaign.progress = 10
        db.commit()
        
        # TODO: Integrate with video processing backend
        # - Extract clips using AI
        # - Generate captions and hashtags
        # - Create platform-optimized versions
        # - Schedule posts
        
        # For now, mark as ready
        campaign.status = models.CampaignStatus.READY
        campaign.progress = 100
        db.commit()
        
    except Exception as e:
        campaign = db.query(models.Campaign).filter_by(id=campaign_id).first()
        if campaign:
            campaign.status = models.CampaignStatus.FAILED
            campaign.error_message = str(e)
            db.commit() 