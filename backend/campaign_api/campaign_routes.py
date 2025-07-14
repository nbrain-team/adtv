"""
Campaign Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import logging

from core.database import get_db
from core.auth import get_current_active_user
from core.campaign_models import Campaign, CampaignStatus, Client, ContentItem, Platform, ContentStatus
from campaign_services.content_generator import ContentGeneratorService
from . import schemas

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Initialize content generator with error handling
logger = logging.getLogger(__name__)
content_generator = None

try:
    content_generator = ContentGeneratorService()
    logger.info("Content generator initialized successfully")
except Exception as e:
    logger.warning(f"Content generator initialization failed: {e}")
    logger.warning("Campaign content generation will not be available")

@router.post("/", response_model=schemas.CampaignResponse)
async def create_campaign(
    campaign_data: schemas.CampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new campaign and generate content"""
    
    # Check if content generator is available
    if not content_generator:
        raise HTTPException(
            status_code=503, 
            detail="Content generation service is not available. Please check GEMINI_API_KEY configuration."
        )
    
    # Verify client exists and user has access
    client = db.query(Client).filter(
        Client.id == campaign_data.client_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Create campaign
    campaign = Campaign(
        client_id=campaign_data.client_id,
        name=campaign_data.name,
        description=campaign_data.description,
        topics=campaign_data.topics[:5],  # Max 5 topics
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        status=CampaignStatus.DRAFT,
        created_by=current_user.id
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Generate content in background
    background_tasks.add_task(
        generate_campaign_content_task,
        campaign.id,
        campaign_data.platforms
    )
    
    return campaign

@router.get("/", response_model=List[schemas.CampaignResponse])
async def list_campaigns(
    client_id: Optional[str] = None,
    status: Optional[CampaignStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List campaigns with optional filters"""
    
    query = db.query(Campaign)
    
    if client_id:
        query = query.filter(Campaign.client_id == client_id)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

@router.get("/{campaign_id}", response_model=schemas.CampaignDetail)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get campaign details including content items"""
    
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.put("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status_update: schemas.CampaignStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update campaign status (approve, pause, etc.)"""
    
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Handle approval workflow
    if status_update.status == CampaignStatus.APPROVED:
        campaign.approved_by = current_user.id
        campaign.approved_at = datetime.utcnow()
        campaign.approval_notes = status_update.notes
    
    campaign.status = status_update.status
    db.commit()
    
    return {"status": "updated"}

@router.post("/{campaign_id}/regenerate/{content_id}")
async def regenerate_content(
    campaign_id: str,
    content_id: str,
    feedback: schemas.ContentFeedback,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Regenerate specific content with feedback"""
    
    # Check if content generator is available
    if not content_generator:
        raise HTTPException(
            status_code=503, 
            detail="Content generation service is not available. Please check GEMINI_API_KEY configuration."
        )
    
    content_item = db.query(ContentItem).filter(
        ContentItem.id == content_id,
        ContentItem.campaign_id == campaign_id
    ).first()
    
    if not content_item:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Regenerate content
    new_content = content_generator.regenerate_content(
        content_item,
        feedback.feedback
    )
    
    # Update content
    content_item.content = new_content["content"]
    content_item.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "regenerated", "content": new_content}

@router.get("/{campaign_id}/preview")
async def preview_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get campaign preview for approval"""
    
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get all content items grouped by platform
    content_by_platform = {}
    for item in campaign.content_items:
        platform = item.platform.value
        if platform not in content_by_platform:
            content_by_platform[platform] = []
        content_by_platform[platform].append({
            "id": item.id,
            "content": item.content,
            "scheduled_date": item.scheduled_date,
            "hashtags": item.hashtags,
            "media_urls": item.media_urls
        })
    
    return {
        "campaign": {
            "id": campaign.id,
            "name": campaign.name,
            "client": campaign.client.name,
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "topics": campaign.topics
        },
        "content": content_by_platform,
        "total_posts": len(campaign.content_items)
    }

# Background task for content generation
def generate_campaign_content_task(campaign_id: str, platforms: List[str]):
    """Background task to generate campaign content"""
    
    db = Session()
    
    try:
        # Check if content generator is available
        if not content_generator:
            print(f"Content generator not available for campaign {campaign_id}")
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                campaign.status = CampaignStatus.FAILED
                db.commit()
            return
            
        # Get campaign and client
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        client = campaign.client
        
        # Convert platform strings to enums
        platform_enums = [Platform(p) for p in platforms]
        
        # Generate content
        generated_content = content_generator.generate_campaign_content(
            client,
            campaign,
            platform_enums
        )
        
        # Save content items
        for platform, items in generated_content.items():
            for item_data in items:
                content_item = ContentItem(
                    campaign_id=campaign_id,
                    platform=platform,
                    content=item_data.get("content", ""),
                    title=item_data.get("title"),  # For emails
                    hashtags=item_data.get("hashtags", []),
                    scheduled_date=item_data.get("scheduled_date"),
                    status=ContentStatus.DRAFT,
                    prompt_used=f"Generated for topic: {item_data.get('topic')}",
                    model_used="gemini-pro"
                )
                db.add(content_item)
        
        # Update campaign status
        campaign.status = CampaignStatus.PENDING_APPROVAL
        db.commit()
        
    except Exception as e:
        print(f"Error generating content: {e}")
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.status = CampaignStatus.FAILED
            db.commit()
    finally:
        db.close() 