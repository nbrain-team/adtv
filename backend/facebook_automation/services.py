"""
Business logic services for Facebook automation
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import json

from . import models, schemas
from .facebook_service import facebook_service, FacebookAPIError
from core.database import User
from core.llm_handler import generate_text

logger = logging.getLogger(__name__)


class FacebookAutomationService:
    """Service for Facebook automation business logic"""
    
    async def connect_facebook_account(
        self,
        db: Session,
        user_id: str,
        auth_code: str,
        *,
        page_id_override: Optional[str] = None,
        ad_account_id_override: Optional[str] = None
    ) -> models.FacebookClient:
        """Connect a Facebook account using OAuth code"""
        try:
            # Check if Facebook API is configured
            use_mock_data = not facebook_service.app_id or not facebook_service.app_secret
            # If a marketing API token is configured, force real mode (no mocks)
            if facebook_service.marketing_api_token:
                use_mock_data = False
            
            if use_mock_data:
                # Use mock data for testing
                from .mock_data import mock_clients
                logger.info("Using mock data - Facebook API not configured")
                
                # Find or create mock client
                client = db.query(models.FacebookClient).filter_by(
                    user_id=user_id,
                    facebook_page_id="mock_page_1"
                ).first()
                
                if not client:
                    mock_client_data = mock_clients[0]
                    client = models.FacebookClient(
                        user_id=user_id,
                        facebook_user_id=mock_client_data["facebook_user_id"],
                        facebook_page_id=mock_client_data["facebook_page_id"],
                        page_name=mock_client_data["page_name"],
                        page_access_token="mock_token",
                        is_active=mock_client_data["is_active"],
                        auto_convert_posts=mock_client_data["auto_convert_posts"],
                        default_daily_budget=mock_client_data["default_daily_budget"],
                        default_campaign_duration=mock_client_data["default_campaign_duration"],
                        automation_rules=mock_client_data["automation_rules"],
                        token_expires_at=datetime.utcnow() + timedelta(days=60)
                    )
                    db.add(client)
                    db.commit()
                    db.refresh(client)
                
                return client
            
            # Original implementation for real Facebook API
            # If we have a marketing API token, use it; otherwise exchange code
            if facebook_service.marketing_api_token:
                access_token = facebook_service.marketing_api_token
                expires_in = 5184000
            else:
                token_data = await facebook_service.exchange_token(auth_code)
                access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 5184000)  # 60 days default
            
            # Get user pages (or fetch a specific page if override provided)
            pages = []
            if page_id_override:
                info = await facebook_service.get_page_basic_info(page_id_override, access_token)
                if info:
                    pages = [{"id": info.get("id"), "name": info.get("name"), "access_token": info.get("access_token")}]
            if not pages:
                pages = await facebook_service.get_user_pages(access_token)
            if not pages:
                raise ValueError("No Facebook pages found for this account")
            
            # Get ad accounts
            ad_accounts = await facebook_service.get_ad_accounts(access_token)
            
            # Choose page/ad account (allow overrides)
            page = None
            if page_id_override:
                page = next((p for p in pages if p.get("id") == page_id_override), None)
            page = page or (pages[0])

            ad_account = None
            if ad_account_id_override:
                # Facebook API expects account id in the form act_<id> in some endpoints; accept both
                wanted_ids = {ad_account_id_override, f"act_{ad_account_id_override}"}
                ad_account = next((a for a in ad_accounts if a.get("id") in wanted_ids), None)
            ad_account = ad_account or (ad_accounts[0] if ad_accounts else None)
            
            # Create or update Facebook client
            client = db.query(models.FacebookClient).filter_by(
                facebook_page_id=page["id"]
            ).first()
            
            # Ensure we have a page name; fetch if missing
            page_name = page.get("name")
            if not page_name:
                try:
                    info2 = await facebook_service.get_page_basic_info(page["id"], access_token)
                    page_name = info2.get("name") or f"Page {page['id']}"
                except Exception:
                    page_name = f"Page {page['id']}"

            # Ensure we have a page access token available for both creation and webhook subscription
            page_access_token = page.get("access_token")
            if not page_access_token and facebook_service.marketing_api_token:
                try:
                    page_access_token = await facebook_service.get_page_access_token(page["id"], access_token)
                except Exception:
                    page_access_token = None

            if not client:
                client = models.FacebookClient(
                    user_id=user_id,
                    facebook_user_id=page["id"],  # Using page ID as user ID for now
                    facebook_page_id=page["id"],
                    page_name=page_name,
                    page_access_token=page_access_token or page.get("access_token"),
                    ad_account_id=ad_account["id"] if ad_account else None,
                    token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
                )
                db.add(client)
            else:
                client.page_access_token = page_access_token or page.get("access_token") or client.page_access_token
                client.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                client.is_active = True
                if ad_account:
                    client.ad_account_id = ad_account.get("id")
            
            db.commit()
            db.refresh(client)
            
            # Subscribe to webhooks
            # Final fallback: use client's stored token
            token_for_webhook = page_access_token or page.get("access_token") or client.page_access_token
            if token_for_webhook:
                await facebook_service.subscribe_page_to_webhook(
                    page["id"], 
                    token_for_webhook
                )
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect Facebook account: {e}")
            db.rollback()
            raise

    async def create_manual_campaign(
        self,
        db: Session,
        client_id: str,
        user_id: str,
        campaign_data: schemas.CampaignCreate
    ) -> models.FacebookAdCampaign:
        """Create an ad campaign without a source post (manual)."""
        client = db.query(models.FacebookClient).filter_by(id=client_id).first()
        if not client:
            raise ValueError("Client not found")

        try:
            campaign = models.FacebookAdCampaign(
                client_id=client.id,
                source_post_id=None,
                created_by=user_id,
                name=campaign_data.name,
                objective=campaign_data.objective,
                primary_text=campaign_data.creative.primary_text,
                headline=campaign_data.creative.headline,
                description=campaign_data.creative.description,
                call_to_action=campaign_data.creative.call_to_action,
                link_url=campaign_data.creative.link_url,
                creative_urls=[],
                daily_budget=campaign_data.daily_budget or client.default_daily_budget,
                start_date=campaign_data.start_date or datetime.utcnow(),
                end_date=campaign_data.end_date or (
                    datetime.utcnow() + timedelta(days=client.default_campaign_duration)
                ),
                targeting=campaign_data.targeting.dict() if campaign_data.targeting else {
                    "geo_locations": {"countries": ["US"]},
                    "age_min": 18,
                    "age_max": 65
                }
            )

            # Create on Facebook if not draft
            if (campaign_data.status or "draft").lower() != "draft":
                fb_campaign = await self._create_facebook_campaign(campaign, client)
                campaign.facebook_campaign_id = fb_campaign["campaign_id"]
                campaign.facebook_adset_id = fb_campaign["adset_id"]
                campaign.facebook_ad_id = fb_campaign["ad_id"]
                campaign.status = models.AdStatus.ACTIVE
                campaign.launched_at = datetime.utcnow()
            else:
                campaign.status = models.AdStatus.DRAFT

            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            return campaign
        except Exception as e:
            logger.error(f"Failed to create manual campaign: {e}")
            db.rollback()
            raise
    
    async def sync_posts(
        self,
        db: Session,
        client_id: str,
        since: Optional[datetime] = None
    ) -> List[models.FacebookPost]:
        """Sync posts from Facebook page"""
        client = db.query(models.FacebookClient).filter_by(id=client_id).first()
        if not client:
            raise ValueError("Client not found")
        
        # Default to last sync or 7 days ago
        if not since:
            since = client.last_sync or datetime.utcnow() - timedelta(days=7)
        
        # Check if using mock data
        use_mock_data = not facebook_service.app_id or not facebook_service.app_secret
        # If a marketing API token is configured, force real mode
        if facebook_service.marketing_api_token:
            use_mock_data = False
        
        if use_mock_data:
            # In strict mode for this deployment we do not generate or return mock posts
            logger.info("Facebook API not configured; returning empty posts without mocks")
            return db.query(models.FacebookPost).filter_by(client_id=client_id).all()
        
        try:
            # Original implementation for real Facebook API
            # Get posts from Facebook
            fb_posts = await facebook_service.get_page_posts(
                client.facebook_page_id,
                client.page_access_token,
                since
            )
            
            synced_posts = []
            
            for fb_post in fb_posts:
                # Skip if already imported
                existing = db.query(models.FacebookPost).filter_by(
                    facebook_post_id=fb_post["id"]
                ).first()
                
                if existing:
                    continue
                
                # Extract media URLs
                media_urls = []
                if fb_post.get("full_picture"):
                    media_urls.append(fb_post["full_picture"])
                
                # Get post insights if available
                insights = await facebook_service.get_post_insights(
                    fb_post["id"],
                    client.page_access_token
                )
                
                # Create post record
                post = models.FacebookPost(
                    client_id=client_id,
                    facebook_post_id=fb_post["id"],
                    post_url=fb_post.get("permalink_url"),
                    message=fb_post.get("message", ""),
                    created_time=datetime.fromisoformat(
                        fb_post["created_time"].replace("Z", "+00:00")
                    ),
                    post_type=fb_post.get("type", "status"),
                    media_urls=media_urls,
                    thumbnail_url=media_urls[0] if media_urls else None,
                    likes_count=fb_post.get("reactions", {}).get("summary", {}).get("total_count", 0),
                    comments_count=fb_post.get("comments", {}).get("summary", {}).get("total_count", 0),
                    shares_count=fb_post.get("shares", {}).get("count", 0),
                    reach=insights.get("post_impressions", 0)
                )
                
                # AI quality analysis
                if post.message:
                    post.ai_quality_score = await self._analyze_post_quality(post)
                    post.ai_suggestions = await self._generate_ad_suggestions(post)
                
                db.add(post)
                synced_posts.append(post)
            
            # Update last sync time
            client.last_sync = datetime.utcnow()
            db.commit()
            
            # Auto-convert if enabled
            if client.auto_convert_posts:
                for post in synced_posts:
                    if await self._should_auto_convert(post, client.automation_rules):
                        await self.create_campaign_from_post(
                            db, 
                            post.id, 
                            user_id=client.user_id
                        )
            
            return synced_posts
            
        except Exception as e:
            logger.error(f"Failed to sync posts: {e}")
            db.rollback()
            raise
    
    async def create_campaign_from_post(
        self,
        db: Session,
        post_id: str,
        user_id: str,
        campaign_data: Optional[schemas.CampaignCreate] = None
    ) -> models.FacebookAdCampaign:
        """Create an ad campaign from a post"""
        post = db.query(models.FacebookPost).filter_by(id=post_id).first()
        if not post:
            raise ValueError("Post not found")
        
        client = post.client
        
        try:
            # Generate campaign data if not provided
            if not campaign_data:
                campaign_data = await self._generate_campaign_from_post(post, client)
            
            # Create campaign in database
            campaign = models.FacebookAdCampaign(
                client_id=client.id,
                source_post_id=post_id,
                created_by=user_id,
                name=campaign_data.name,
                objective=campaign_data.objective,
                primary_text=campaign_data.creative.primary_text,
                headline=campaign_data.creative.headline,
                description=campaign_data.creative.description,
                call_to_action=campaign_data.creative.call_to_action,
                link_url=campaign_data.creative.link_url,
                creative_urls=post.media_urls,
                daily_budget=campaign_data.daily_budget or client.default_daily_budget,
                start_date=campaign_data.start_date or datetime.utcnow(),
                end_date=campaign_data.end_date or (
                    datetime.utcnow() + timedelta(days=client.default_campaign_duration)
                ),
                targeting=campaign_data.targeting.dict() if campaign_data.targeting else {
                    "geo_locations": {"countries": ["US"]},
                    "age_min": 18,
                    "age_max": 65
                }
            )
            
            # Create on Facebook if not draft
            if campaign_data.status != "draft":
                fb_campaign = await self._create_facebook_campaign(campaign, client)
                campaign.facebook_campaign_id = fb_campaign["campaign_id"]
                campaign.facebook_adset_id = fb_campaign["adset_id"]
                campaign.facebook_ad_id = fb_campaign["ad_id"]
                campaign.status = models.AdStatus.ACTIVE
                campaign.launched_at = datetime.utcnow()
            
            db.add(campaign)
            
            # Update post status
            post.status = models.PostStatus.CONVERTED
            post.converted_at = datetime.utcnow()
            
            db.commit()
            db.refresh(campaign)
            
            return campaign
            
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            db.rollback()
            raise
    
    async def update_campaign_metrics(
        self,
        db: Session,
        campaign_id: str
    ) -> models.FacebookAdCampaign:
        """Update campaign metrics from Facebook"""
        campaign = db.query(models.FacebookAdCampaign).filter_by(id=campaign_id).first()
        if not campaign or not campaign.facebook_campaign_id:
            raise ValueError("Campaign not found or not launched")
        
        client = campaign.client
        
        try:
            # Get insights from Facebook
            insights = await facebook_service.get_campaign_insights(
                campaign.facebook_campaign_id,
                client.page_access_token
            )
            
            # Update campaign metrics
            campaign.impressions = insights.get("impressions", 0)
            campaign.reach = insights.get("reach", 0)
            campaign.clicks = insights.get("clicks", 0)
            campaign.ctr = float(insights.get("ctr", 0))
            campaign.cpc = float(insights.get("cpc", 0))
            campaign.cpm = float(insights.get("cpm", 0))
            campaign.spend = float(insights.get("spend", 0))
            
            # Get conversions if available
            actions = insights.get("actions", [])
            for action in actions:
                if action["action_type"] == "purchase":
                    campaign.conversions = int(action["value"])
                    break
            
            # Calculate derived metrics
            if campaign.clicks > 0:
                campaign.conversion_rate = (campaign.conversions / campaign.clicks) * 100
            
            if campaign.spend > 0:
                conversion_values = sum(
                    float(av["value"]) 
                    for av in insights.get("action_values", [])
                    if av["action_type"] == "purchase"
                )
                campaign.roas = conversion_values / campaign.spend
            
            campaign.last_updated = datetime.utcnow()
            
            # Store historical snapshot
            analytics = models.FacebookAnalytics(
                campaign_id=campaign_id,
                impressions=campaign.impressions,
                reach=campaign.reach,
                clicks=campaign.clicks,
                ctr=campaign.ctr,
                cpc=campaign.cpc,
                cpm=campaign.cpm,
                spend=campaign.spend,
                conversions=campaign.conversions
            )
            db.add(analytics)
            
            db.commit()
            db.refresh(campaign)
            
            return campaign
            
        except Exception as e:
            logger.error(f"Failed to update campaign metrics: {e}")
            db.rollback()
            raise
    
    async def get_analytics_summary(
        self,
        db: Session,
        user_id: str,
        request: schemas.AnalyticsRequest
    ) -> schemas.AnalyticsResponse:
        """Get analytics summary for campaigns"""
        # Check if using mock data
        use_mock_data = not facebook_service.app_id or not facebook_service.app_secret
        
        if use_mock_data:
            from .mock_data import mock_analytics
            logger.info("Using mock analytics data - Facebook API not configured")
            
            # Get client IDs for the user
            client_ids = request.client_ids
            if not client_ids:
                clients = db.query(models.FacebookClient).filter_by(user_id=user_id).all()
                client_ids = [c.id for c in clients]
            
            # Return mock analytics
            return schemas.AnalyticsResponse(**mock_analytics(client_ids))
        
        # Original implementation
        query = db.query(models.FacebookAdCampaign).join(
            models.FacebookClient
        ).filter(
            models.FacebookClient.user_id == user_id
        )
        
        # Apply filters
        if request.campaign_ids:
            query = query.filter(models.FacebookAdCampaign.id.in_(request.campaign_ids))
        
        if request.client_ids:
            query = query.filter(models.FacebookAdCampaign.client_id.in_(request.client_ids))
        
        # Date filters
        if request.timeframe != schemas.AnalyticsTimeframe.CUSTOM:
            date_start, date_end = self._get_date_range(request.timeframe)
        else:
            date_start = request.date_start
            date_end = request.date_end
        
        if date_start:
            query = query.filter(models.FacebookAdCampaign.created_at >= date_start)
        if date_end:
            query = query.filter(models.FacebookAdCampaign.created_at <= date_end)
        
        campaigns = query.all()
        
        # Calculate aggregates
        total_spend = sum(c.spend for c in campaigns)
        total_impressions = sum(c.impressions for c in campaigns)
        total_reach = sum(c.reach for c in campaigns)
        total_clicks = sum(c.clicks for c in campaigns)
        total_conversions = sum(c.conversions for c in campaigns)
        
        # Calculate averages
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        avg_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        avg_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        # Get top performers
        top_campaigns = sorted(campaigns, key=lambda c: c.roas, reverse=True)[:5]
        
        return schemas.AnalyticsResponse(
            total_spend=total_spend,
            total_impressions=total_impressions,
            total_reach=total_reach,
            total_clicks=total_clicks,
            avg_ctr=avg_ctr,
            avg_cpc=avg_cpc,
            avg_cpm=avg_cpm,
            total_conversions=total_conversions,
            avg_conversion_rate=avg_conversion_rate,
            avg_roas=sum(c.roas for c in campaigns) / len(campaigns) if campaigns else 0,
            top_performing_campaigns=[
                {
                    "id": c.id,
                    "name": c.name,
                    "roas": c.roas,
                    "spend": c.spend,
                    "conversions": c.conversions
                }
                for c in top_campaigns
            ],
            demographics_breakdown={},  # TODO: Implement
            device_breakdown={},  # TODO: Implement
            time_series=[]  # TODO: Implement
        )
    
    async def _analyze_post_quality(self, post: models.FacebookPost) -> float:
        """Analyze post quality using AI"""
        prompt = f"""
        Analyze this Facebook post for advertising potential. Score from 0-100.
        Consider: engagement potential, clarity, call-to-action, visual appeal indication.
        
        Post: {post.message[:500]}
        Post type: {post.post_type}
        Has image: {bool(post.media_urls)}
        Current engagement: {post.likes_count} likes, {post.comments_count} comments
        
        Return only a number between 0-100.
        """
        
        try:
            response = await generate_text(prompt)
            score = float(response.strip())
            return min(max(score, 0), 100)  # Ensure 0-100 range
        except:
            return 50.0  # Default middle score
    
    async def _generate_ad_suggestions(self, post: models.FacebookPost) -> Dict[str, Any]:
        """Generate ad improvement suggestions"""
        prompt = f"""
        Suggest improvements to turn this Facebook post into a high-performing ad.
        
        Post: {post.message[:500]}
        
        Provide suggestions in JSON format:
        {{
            "improved_headline": "...",
            "improved_text": "...", 
            "call_to_action": "LEARN_MORE/SHOP_NOW/etc",
            "target_audience": ["interest1", "interest2"],
            "recommended_budget": 50
        }}
        """
        
        try:
            response = await generate_text(prompt)
            return json.loads(response)
        except:
            return {
                "improved_headline": "Check this out!",
                "improved_text": post.message,
                "call_to_action": "LEARN_MORE",
                "target_audience": ["general"],
                "recommended_budget": 50
            }
    
    async def _should_auto_convert(
        self, 
        post: models.FacebookPost,
        rules: Dict[str, Any]
    ) -> bool:
        """Check if post should be auto-converted based on rules"""
        # Check text length
        if len(post.message or "") < rules.get("min_text_length", 50):
            return False
        
        # Check for required image
        if rules.get("require_image", True) and not post.media_urls:
            return False
        
        # Check AI quality score
        if (post.ai_quality_score or 0) < 70:
            return False
        
        # Check excluded keywords
        excluded = rules.get("exclude_keywords", [])
        if any(keyword.lower() in (post.message or "").lower() for keyword in excluded):
            return False
        
        # Check approval keywords
        approval_required = rules.get("require_approval_keywords", [])
        if approval_required and not any(
            keyword.lower() in (post.message or "").lower() 
            for keyword in approval_required
        ):
            return False
        
        return True
    
    async def _generate_campaign_from_post(
        self,
        post: models.FacebookPost,
        client: models.FacebookClient
    ) -> schemas.CampaignCreate:
        """Generate campaign data from post using AI suggestions"""
        suggestions = post.ai_suggestions or {}
        
        return schemas.CampaignCreate(
            source_post_id=post.id,
            name=f"Ad - {post.message[:30]}..." if post.message else f"Ad - Post {post.id[:8]}",
            objective=client.automation_rules.get("optimization_goal", "REACH"),
            creative=schemas.AdCreativeContent(
                primary_text=suggestions.get("improved_text", post.message or ""),
                headline=suggestions.get("improved_headline", "Special Offer"),
                call_to_action=suggestions.get("call_to_action", "LEARN_MORE")
            ),
            daily_budget=suggestions.get("recommended_budget", client.default_daily_budget),
            targeting=schemas.AdTargeting(
                interests=suggestions.get("target_audience", [])
            )
        )
    
    async def _create_facebook_campaign(
        self,
        campaign: models.FacebookAdCampaign,
        client: models.FacebookClient
    ) -> Dict[str, Any]:
        """Create campaign on Facebook"""
        # Create campaign
        fb_campaign = await facebook_service.create_campaign(
            client.ad_account_id,
            client.page_access_token,
            campaign.name,
            campaign.objective
        )
        
        # Create ad set
        fb_adset = await facebook_service.create_ad_set(
            client.ad_account_id,
            client.page_access_token,
            fb_campaign["id"],
            f"{campaign.name} - Ad Set",
            campaign.daily_budget,
            campaign.targeting,
            campaign.start_date,
            campaign.end_date
        )
        
        # Create creative
        creative_data = {
            "primary_text": campaign.primary_text,
            "headline": campaign.headline,
            "description": campaign.description,
            "call_to_action": campaign.call_to_action,
            "link_url": campaign.link_url,
            "image_url": campaign.creative_urls[0] if campaign.creative_urls else None
        }
        
        fb_creative = await facebook_service.create_ad_creative(
            client.ad_account_id,
            client.page_access_token,
            client.facebook_page_id,
            creative_data
        )
        
        # Create ad
        fb_ad = await facebook_service.create_ad(
            client.ad_account_id,
            client.page_access_token,
            f"{campaign.name} - Ad",
            fb_adset["id"],
            fb_creative["id"]
        )
        
        # Activate campaign
        await facebook_service.update_campaign_status(
            fb_campaign["id"],
            client.page_access_token,
            "ACTIVE"
        )
        
        return {
            "campaign_id": fb_campaign["id"],
            "adset_id": fb_adset["id"],
            "ad_id": fb_ad["id"]
        }
    
    def _get_date_range(self, timeframe: schemas.AnalyticsTimeframe):
        """Get date range for analytics timeframe"""
        now = datetime.utcnow()
        
        if timeframe == schemas.AnalyticsTimeframe.TODAY:
            return now.replace(hour=0, minute=0, second=0), now
        elif timeframe == schemas.AnalyticsTimeframe.YESTERDAY:
            yesterday = now - timedelta(days=1)
            return (
                yesterday.replace(hour=0, minute=0, second=0),
                yesterday.replace(hour=23, minute=59, second=59)
            )
        elif timeframe == schemas.AnalyticsTimeframe.LAST_7_DAYS:
            return now - timedelta(days=7), now
        elif timeframe == schemas.AnalyticsTimeframe.LAST_30_DAYS:
            return now - timedelta(days=30), now
        elif timeframe == schemas.AnalyticsTimeframe.THIS_MONTH:
            return now.replace(day=1, hour=0, minute=0, second=0), now
        elif timeframe == schemas.AnalyticsTimeframe.LAST_MONTH:
            first_day_this_month = now.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return first_day_last_month, last_day_last_month
        
        return None, None


# Singleton instance
facebook_automation_service = FacebookAutomationService() 