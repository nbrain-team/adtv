"""
API routes for Facebook Automation module
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from core.database import get_db, User
from core.auth import get_current_active_user
from . import models, schemas
from .services import facebook_automation_service
from .facebook_service import facebook_service

router = APIRouter(tags=["facebook-automation"])
logger = logging.getLogger(__name__)


# OAuth endpoints
@router.get("/facebook/auth")
async def facebook_auth(
    redirect_uri: str,
    current_user: User = Depends(get_current_active_user)
):
    """Initiate Facebook OAuth flow"""
    # Permission check disabled for demo
    # if not current_user.permissions.get("facebook-automation", False):
    #     raise HTTPException(status_code=403, detail="Facebook automation not enabled for user")
    
    app_id = facebook_service.app_id
    # If a Marketing API token is configured, we can skip OAuth for service accounts
    if facebook_service.marketing_api_token:
        return {
            "auth_url": None,
            "mock_mode": False,
            "service_token_mode": True
        }
    if not app_id:
        # Return mock auth URL for testing
        logger.info("Facebook app not configured - using mock mode")
        mock_auth_url = f"{redirect_uri}?code=mock_auth_code&state={current_user.id}"
        return {"auth_url": mock_auth_url, "mock_mode": True}
    
    # Required permissions
    scopes = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts",
        "ads_management",
        "business_management",
        "instagram_basic",
        "instagram_content_publish"
    ]
    
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": ",".join(scopes),
        "response_type": "code",
        "state": current_user.id  # Pass user ID for security
    }
    
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.post("/facebook/callback")
async def facebook_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Handle Facebook OAuth callback"""
    # Verify state matches user ID
    if state != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        client = await facebook_automation_service.connect_facebook_account(
            db, current_user.id, code
        )
        return schemas.FacebookClient.from_orm(client)
    except Exception as e:
        logger.error(f"Facebook OAuth failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/facebook/connect-with-token", response_model=schemas.FacebookClient)
async def connect_with_service_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Connect using a configured Marketing API token without OAuth."""
    if not facebook_service.marketing_api_token:
        raise HTTPException(status_code=400, detail="FACEBOOK_MARKETING_API_TOKEN not configured")
    try:
        # Reuse the same flow with a dummy code; service will switch to token mode
        client = await facebook_automation_service.connect_facebook_account(
            db, current_user.id, auth_code="service_token"
        )
        return schemas.FacebookClient.from_orm(client)
    except Exception as e:
        logger.error(f"Facebook token connect failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/facebook/manual-connect", response_model=schemas.FacebookClient)
async def manual_connect(
    body: schemas.ManualConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Connect a Facebook page/account using a pre-authorized Marketing API token.
    Requires FACEBOOK_MARKETING_API_TOKEN to be set.
    """
    if not facebook_service.marketing_api_token:
        raise HTTPException(status_code=400, detail={
            "error": "FACEBOOK_MARKETING_API_TOKEN not configured",
            "hint": "Set this env on the backend service and redeploy"
        })
    try:
        client = await facebook_automation_service.connect_facebook_account(
            db,
            current_user.id,
            auth_code="service_token",
            page_id_override=body.page_id,
            ad_account_id_override=body.ad_account_id or None
        )
        # If page_name provided, persist/update it
        if body.page_name and getattr(client, "page_name", None) != body.page_name:
            client.page_name = body.page_name
            db.commit()
            db.refresh(client)
        return schemas.FacebookClient.from_orm(client)
    except Exception as e:
        logger.error(f"Facebook manual connect failed: {e}")
        raise HTTPException(status_code=400, detail={
            "error": "manual_connect_failed",
            "message": str(e)
        })

@router.post("/campaigns/manual", response_model=schemas.FacebookAdCampaign)
async def create_campaign_manual(
    client_id: str,
    campaign_data: schemas.CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create an ad campaign without selecting a post."""
    try:
        campaign = await facebook_automation_service.create_manual_campaign(
            db, client_id, current_user.id, campaign_data
        )
        return schemas.FacebookAdCampaign.from_orm(campaign)
    except Exception as e:
        logger.error(f"Failed to create manual campaign: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Client management
@router.get("/clients", response_model=List[schemas.FacebookClient])
async def get_clients(
    is_active: Optional[bool] = None,
    page_id: Optional[str] = None,
    ad_account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get connected Facebook clients"""
    # Show only current user's clients by default
    query = db.query(models.FacebookClient).filter_by(user_id=current_user.id)
    
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    if page_id:
        query = query.filter(models.FacebookClient.facebook_page_id == page_id)
    if ad_account_id:
        # Accept both raw id and act_<id> forms
        variants = [ad_account_id, f"act_{ad_account_id}"]
        query = query.filter(models.FacebookClient.ad_account_id.in_(variants))
    
    clients = query.order_by(models.FacebookClient.created_at.desc()).all()
    
    # Don't auto-create mock data - return actual DB data
    return clients


@router.get("/clients/{client_id}", response_model=schemas.FacebookClient)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific Facebook client"""
    # Allow syncing if the client exists; re-scope ownership issues are handled in service layer
    client = db.query(models.FacebookClient).filter_by(id=client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client


@router.put("/clients/{client_id}", response_model=schemas.FacebookClient)
async def update_client(
    client_id: str,
    update_data: schemas.FacebookClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update Facebook client settings"""
    client = db.query(models.FacebookClient).filter_by(
        id=client_id, user_id=current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    return client


@router.delete("/clients/{client_id}")
async def disconnect_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect Facebook client"""
    client = db.query(models.FacebookClient).filter_by(
        id=client_id, user_id=current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    
    return {"message": "Client disconnected successfully"}


# Post management
@router.post("/clients/{client_id}/sync-posts")
async def sync_posts(
    client_id: str,
    background_tasks: BackgroundTasks,
    since: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync posts from Facebook page"""
    client = db.query(models.FacebookClient).filter_by(
        id=client_id, user_id=current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Run sync in background
    background_tasks.add_task(
        facebook_automation_service.sync_posts,
        db, client_id, since
    )
    
    return {"message": "Post sync started"}


@router.get("/posts", response_model=List[schemas.FacebookPost])
async def get_posts(
    client_id: Optional[str] = None,
    status: Optional[schemas.PostStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get imported Facebook posts"""
    query = db.query(models.FacebookPost).join(models.FacebookClient)
    
    if client_id:
        query = query.filter(models.FacebookPost.client_id == client_id)
    
    if status:
        query = query.filter(models.FacebookPost.status == status)
    
    query = query.order_by(models.FacebookPost.created_time.desc())

    posts = query.offset(skip).limit(limit).all()
    # Normalize any legacy uppercase statuses to enum-compatible values to avoid 500s
    def normalize_post_status(value: str) -> models.PostStatus:
        mapping = {
            "IMPORTED": models.PostStatus.IMPORTED,
            "REVIEWED": models.PostStatus.REVIEWED,
            "CONVERTED": models.PostStatus.CONVERTED,
            "SKIPPED": models.PostStatus.SKIPPED,
            "PUBLISHED": models.PostStatus.REVIEWED,
            "APPROVED": models.PostStatus.REVIEWED,
            "DRAFT": models.PostStatus.IMPORTED,
        }
        if isinstance(value, str):
            return mapping.get(value.upper(), models.PostStatus.IMPORTED)
        return value or models.PostStatus.IMPORTED

    for p in posts:
        if isinstance(p.status, str):
            try:
                p.status = normalize_post_status(p.status)
            except Exception:
                p.status = models.PostStatus.IMPORTED
    return posts


@router.get("/posts/{post_id}", response_model=schemas.FacebookPost)
async def get_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific Facebook post"""
    post = db.query(models.FacebookPost).join(
        models.FacebookClient
    ).filter(
        models.FacebookPost.id == post_id,
        models.FacebookClient.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return post


@router.put("/posts/{post_id}/review")
async def review_post(
    post_id: str,
    review_data: schemas.PostReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Review and update post status"""
    post = db.query(models.FacebookPost).join(
        models.FacebookClient
    ).filter(
        models.FacebookPost.id == post_id,
        models.FacebookClient.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = review_data.status
    post.review_notes = review_data.review_notes
    post.reviewed_by = current_user.id
    post.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Post reviewed successfully"}


# Campaign management
@router.post("/campaigns", response_model=schemas.FacebookAdCampaign)
async def create_campaign(
    campaign_data: schemas.CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create ad campaign (from post or manual)"""
    try:
        campaign = await facebook_automation_service.create_campaign_from_post(
            db,
            campaign_data.source_post_id,
            current_user.id,
            campaign_data
        )
        return schemas.FacebookAdCampaign.from_orm(campaign)
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns", response_model=List[schemas.FacebookAdCampaign])
async def get_campaigns(
    client_id: Optional[str] = None,
    status: Optional[schemas.AdStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ad campaigns"""
    query = db.query(models.FacebookAdCampaign).join(models.FacebookClient)
    
    if client_id:
        query = query.filter(models.FacebookAdCampaign.client_id == client_id)
    
    if status:
        query = query.filter(models.FacebookAdCampaign.status == status)
    
    query = query.order_by(models.FacebookAdCampaign.created_at.desc())
    
    campaigns = query.offset(skip).limit(limit).all()
    # Normalize any legacy uppercase statuses
    def normalize_ad_status(value: str) -> models.AdStatus:
        mapping = {
            "ACTIVE": models.AdStatus.ACTIVE,
            "PAUSED": models.AdStatus.PAUSED,
            "COMPLETED": models.AdStatus.COMPLETED,
            "DRAFT": models.AdStatus.DRAFT,
        }
        if isinstance(value, str):
            return mapping.get(value.upper(), models.AdStatus.DRAFT)
        return value or models.AdStatus.DRAFT

    for c in campaigns:
        if isinstance(c.status, str):
            try:
                c.status = normalize_ad_status(c.status)
            except Exception:
                c.status = models.AdStatus.DRAFT

    # Don't auto-create mock data - return actual DB data
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=schemas.FacebookAdCampaign)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific campaign"""
    campaign = db.query(models.FacebookAdCampaign).join(
        models.FacebookClient
    ).filter(
        models.FacebookAdCampaign.id == campaign_id,
        models.FacebookClient.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=schemas.FacebookAdCampaign)
async def update_campaign(
    campaign_id: str,
    update_data: schemas.CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update campaign settings"""
    campaign = db.query(models.FacebookAdCampaign).join(
        models.FacebookClient
    ).filter(
        models.FacebookAdCampaign.id == campaign_id,
        models.FacebookClient.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    # Update on Facebook if needed
    if update_data.status and campaign.facebook_campaign_id:
        try:
            await facebook_service.update_campaign_status(
                campaign.facebook_campaign_id,
                campaign.client.page_access_token,
                update_data.status
            )
        except Exception as e:
            logger.error(f"Failed to update campaign on Facebook: {e}")
    
    db.commit()
    db.refresh(campaign)
    
    return campaign


@router.post("/campaigns/{campaign_id}/sync-metrics")
async def sync_campaign_metrics(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync campaign metrics from Facebook"""
    campaign = db.query(models.FacebookAdCampaign).join(
        models.FacebookClient
    ).filter(
        models.FacebookAdCampaign.id == campaign_id,
        models.FacebookClient.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        campaign = await facebook_automation_service.update_campaign_metrics(
            db, campaign_id
        )
        return {"message": "Metrics updated successfully"}
    except Exception as e:
        logger.error(f"Failed to sync metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Analytics
@router.post("/analytics", response_model=schemas.AnalyticsResponse)
async def get_analytics(
    request: schemas.AnalyticsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics summary"""
    try:
        return await facebook_automation_service.get_analytics_summary(
            db, current_user.id, request
        )
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Bulk operations
@router.post("/bulk/campaigns")
async def bulk_campaign_operation(
    operation: schemas.BulkOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk operations on campaigns"""
    campaigns = db.query(models.FacebookAdCampaign).join(
        models.FacebookClient
    ).filter(
        models.FacebookAdCampaign.id.in_(operation.item_ids),
        models.FacebookClient.user_id == current_user.id
    ).all()
    
    if not campaigns:
        raise HTTPException(status_code=404, detail="No campaigns found")
    
    success_count = 0
    errors = []
    
    for campaign in campaigns:
        try:
            if operation.operation == "pause":
                campaign.status = models.AdStatus.PAUSED
                if campaign.facebook_campaign_id:
                    await facebook_service.update_campaign_status(
                        campaign.facebook_campaign_id,
                        campaign.client.page_access_token,
                        "PAUSED"
                    )
            elif operation.operation == "resume":
                campaign.status = models.AdStatus.ACTIVE
                if campaign.facebook_campaign_id:
                    await facebook_service.update_campaign_status(
                        campaign.facebook_campaign_id,
                        campaign.client.page_access_token,
                        "ACTIVE"
                    )
            elif operation.operation == "delete":
                db.delete(campaign)
            
            success_count += 1
        except Exception as e:
            errors.append({"campaign_id": campaign.id, "error": str(e)})
    
    db.commit()
    
    return {
        "success_count": success_count,
        "errors": errors
    }


# Templates
@router.get("/templates", response_model=List[schemas.AdTemplate])
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ad templates"""
    templates = db.query(models.AdTemplate).filter_by(
        user_id=current_user.id
    ).order_by(models.AdTemplate.times_used.desc()).all()
    
    return templates


@router.post("/templates", response_model=schemas.AdTemplate)
async def create_template(
    template_data: schemas.AdTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create ad template"""
    template = models.AdTemplate(
        user_id=current_user.id,
        **template_data.dict()
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


# Webhook endpoint
@router.get("/webhook")
async def webhook_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Facebook webhook verification"""
    challenge = facebook_service.verify_webhook(hub_mode, hub_token, hub_challenge)
    if challenge:
        return int(challenge)
    
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def webhook_callback(
    data: dict,
    background_tasks: BackgroundTasks
):
    """Handle Facebook webhook events"""
    background_tasks.add_task(
        facebook_service.process_webhook_event,
        data
    )
    
    return {"status": "ok"} 