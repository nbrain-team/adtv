"""
Facebook Graph API service layer
"""

import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class FacebookAPIError(Exception):
    """Facebook API error"""
    pass


class FacebookService:
    """Service for interacting with Facebook Graph API"""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self):
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.webhook_token = os.getenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN")
        # Optional long-lived Marketing API token (user/system token)
        self.marketing_api_token = os.getenv("FACEBOOK_MARKETING_API_TOKEN")
        
    async def exchange_token(self, short_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token"""
        async with httpx.AsyncClient() as client:
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": short_token
            }
            
            response = await client.get(
                f"{self.BASE_URL}/oauth/access_token",
                params=params
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Token exchange failed: {response.text}")
                
            return response.json()
    
    async def get_user_pages(self, access_token: str) -> List[Dict[str, Any]]:
        """Get pages managed by the user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/me/accounts",
                params={
                    "access_token": access_token or self.marketing_api_token,
                    "fields": "id,name,access_token,category,tasks"
                }
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to get pages: {response.text}")
                
            data = response.json()
            return data.get("data", [])
    
    async def get_ad_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get ad accounts accessible by the user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/me/adaccounts",
                params={
                    "access_token": access_token or self.marketing_api_token,
                    "fields": "id,name,account_status,currency,business"
                }
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to get ad accounts: {response.text}")
                
            data = response.json()
            return data.get("data", [])
    
    async def get_page_posts(
        self, 
        page_id: str, 
        access_token: str,
        since: Optional[datetime] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Get posts from a Facebook page"""
        params = {
            "access_token": access_token or self.marketing_api_token,
            # Request only supported, non-deprecated fields. Engagement metrics will be fetched via insights.
            "fields": "id,message,created_time,full_picture,permalink_url",
            "limit": limit
        }
        
        if since:
            params["since"] = int(since.timestamp())
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{page_id}/posts",
                params=params
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to get posts: {response.text}")
                
            data = response.json()
            return data.get("data", [])

    async def get_page_access_token(self, page_id: str, user_access_token: Optional[str] = None) -> Optional[str]:
        """Fetch a page access token using a user/system access token"""
        token = user_access_token or self.marketing_api_token
        if not token:
            return None
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{page_id}",
                params={
                    "access_token": token,
                    "fields": "access_token"
                }
            )
            if response.status_code != 200:
                logger.warning(f"Failed to get page access token: {response.text}")
                return None
            data = response.json()
            return data.get("access_token")

    async def get_page_basic_info(self, page_id: str, access_token: Optional[str]) -> Dict[str, Any]:
        """Fetch basic page info like name and access token"""
        token = access_token or self.marketing_api_token
        if not token:
            return {}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{page_id}",
                params={
                    "access_token": token,
                    "fields": "id,name,access_token"
                }
            )
            if response.status_code != 200:
                logger.warning(f"Failed to get page basic info: {response.text}")
                return {}
            return response.json()
    
    async def get_post_insights(
        self, 
        post_id: str, 
        access_token: str
    ) -> Dict[str, Any]:
        """Get insights for a specific post"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{post_id}/insights",
                params={
                    "access_token": access_token,
                    "metric": "post_impressions,post_engaged_users,post_clicks,post_reactions_by_type_total"
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get post insights: {response.text}")
                return {}
                
            data = response.json()
            
            # Parse insights into a flat dictionary
            insights = {}
            for item in data.get("data", []):
                metric = item["name"]
                value = item["values"][0]["value"] if item["values"] else 0
                insights[metric] = value
                
            return insights
    
    async def create_campaign(
        self,
        ad_account_id: str,
        access_token: str,
        name: str,
        objective: str = "REACH",
        status: str = "PAUSED"
    ) -> Dict[str, Any]:
        """Create a Facebook ad campaign"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{ad_account_id}/campaigns",
                data={
                    "access_token": access_token,
                    "name": name,
                    "objective": objective,
                    "status": status,
                    "special_ad_categories": "[]"
                }
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to create campaign: {response.text}")
                
            return response.json()
    
    async def create_ad_set(
        self,
        ad_account_id: str,
        access_token: str,
        campaign_id: str,
        name: str,
        daily_budget: float,
        targeting: Dict[str, Any],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a Facebook ad set"""
        data = {
            "access_token": access_token,
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": int(daily_budget * 100),  # Convert to cents
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "REACH",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "targeting": targeting,
            "status": "PAUSED"
        }
        
        if start_time:
            data["start_time"] = start_time.isoformat()
        if end_time:
            data["end_time"] = end_time.isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{ad_account_id}/adsets",
                json=data
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to create ad set: {response.text}")
                
            return response.json()
    
    async def create_ad_creative(
        self,
        ad_account_id: str,
        access_token: str,
        page_id: str,
        creative_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create ad creative"""
        data = {
            "access_token": access_token,
            "name": creative_data.get("name", "Ad Creative"),
            "object_story_spec": {
                "page_id": page_id,
                "link_data": {
                    "message": creative_data["primary_text"],
                    "link": creative_data.get("link_url", f"https://facebook.com/{page_id}"),
                    "name": creative_data["headline"],
                    "description": creative_data.get("description", ""),
                    "call_to_action": {
                        "type": creative_data.get("call_to_action", "LEARN_MORE")
                    }
                }
            }
        }
        
        # Add image if provided
        if creative_data.get("image_url"):
            data["object_story_spec"]["link_data"]["picture"] = creative_data["image_url"]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{ad_account_id}/adcreatives",
                json=data
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to create ad creative: {response.text}")
                
            return response.json()
    
    async def create_ad(
        self,
        ad_account_id: str,
        access_token: str,
        name: str,
        adset_id: str,
        creative_id: str
    ) -> Dict[str, Any]:
        """Create the actual ad"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{ad_account_id}/ads",
                data={
                    "access_token": access_token,
                    "name": name,
                    "adset_id": adset_id,
                    "creative": {"creative_id": creative_id},
                    "status": "PAUSED"
                }
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to create ad: {response.text}")
                
            return response.json()
    
    async def update_campaign_status(
        self,
        campaign_id: str,
        access_token: str,
        status: str
    ) -> Dict[str, Any]:
        """Update campaign status (ACTIVE, PAUSED, etc)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{campaign_id}",
                data={
                    "access_token": access_token,
                    "status": status
                }
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to update campaign: {response.text}")
                
            return response.json()
    
    async def get_campaign_insights(
        self,
        campaign_id: str,
        access_token: str,
        date_preset: str = "last_7d",
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get campaign performance insights"""
        if fields is None:
            fields = [
                "impressions", "reach", "clicks", "ctr", "cpc", "cpm", "spend",
                "actions", "action_values", "cost_per_action_type",
                "frequency", "unique_clicks", "unique_ctr"
            ]
        
        params = {
            "access_token": access_token,
            "fields": ",".join(fields),
            "date_preset": date_preset,
            "level": "campaign"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{campaign_id}/insights",
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get campaign insights: {response.text}")
                return {}
                
            data = response.json()
            return data.get("data", [{}])[0] if data.get("data") else {}
    
    async def get_ad_insights_with_demographics(
        self,
        ad_id: str,
        access_token: str,
        date_preset: str = "last_7d"
    ) -> Dict[str, Any]:
        """Get ad insights with demographic breakdown"""
        params = {
            "access_token": access_token,
            "fields": "impressions,reach,clicks,spend,ctr,cpc,cpm",
            "date_preset": date_preset,
            "breakdowns": "age,gender",
            "level": "ad"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{ad_id}/insights",
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get ad insights: {response.text}")
                return {}
                
            return response.json()
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook subscription"""
        if mode == "subscribe" and token == self.webhook_token:
            return challenge
        return None
    
    async def process_webhook_event(self, data: Dict[str, Any]) -> None:
        """Process incoming webhook events"""
        # This will be called when Facebook sends updates
        # Process different event types (page posts, ad updates, etc)
        for entry in data.get("entry", []):
            page_id = entry.get("id")
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value")
                
                if field == "feed":
                    # New post created
                    logger.info(f"New post on page {page_id}: {value}")
                elif field == "ads_insights":
                    # Ad performance update
                    logger.info(f"Ad insights update: {value}")
                    
    async def subscribe_page_to_webhook(
        self, 
        page_id: str, 
        page_access_token: str
    ) -> Dict[str, Any]:
        """Subscribe a page to webhook events"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{page_id}/subscribed_apps",
                data={
                    "access_token": page_access_token,
                    # 'ads_insights' is not a valid page webhook field; subscribe to 'feed' only
                    "subscribed_fields": "feed"
                }
            )
            
            if response.status_code != 200:
                raise FacebookAPIError(f"Failed to subscribe page: {response.text}")
                
            return response.json()


# Singleton instance
facebook_service = FacebookService() 