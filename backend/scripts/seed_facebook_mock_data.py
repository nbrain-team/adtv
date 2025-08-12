"""
Seed the database with mock Facebook automation data for realtors
"""

import os
import sys

# Set up a local SQLite database if DATABASE_URL is not set
if not os.getenv("DATABASE_URL"):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "local_test.db"))
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    print(f"Using local SQLite database: {db_path}")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import uuid
from sqlalchemy.orm import Session
from core.database import SessionLocal, User, engine, Base
from facebook_automation import models
from facebook_automation.mock_data import (
    MOCK_CLIENTS, 
    MOCK_POSTS_TEMPLATES,
    mock_posts,
    mock_campaigns
)

def clear_facebook_data(db: Session):
    """Clear existing Facebook automation data"""
    try:
        db.query(models.FacebookAnalytics).delete()
        db.query(models.FacebookAdCampaign).delete()
        db.query(models.FacebookPost).delete()
        db.query(models.FacebookClient).delete()
        db.query(models.AdTemplate).delete()
        db.commit()
        print("Cleared existing Facebook automation data")
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()

def seed_facebook_clients(db: Session, user_id: str):
    """Seed Facebook clients for a user"""
    clients_created = []
    
    for mock_data in MOCK_CLIENTS[:3]:
        client = models.FacebookClient(
            id=str(uuid.uuid4()),
            user_id=user_id,
            facebook_user_id=mock_data["facebook_user_id"],
            facebook_page_id=mock_data["facebook_page_id"],
            page_name=mock_data["page_name"],
            page_access_token="mock_token_" + mock_data["facebook_page_id"],
            is_active=mock_data["is_active"],
            auto_convert_posts=mock_data["auto_convert_posts"],
            default_daily_budget=mock_data["default_daily_budget"],
            default_campaign_duration=mock_data["default_campaign_duration"],
            automation_rules=mock_data["automation_rules"],
            created_at=mock_data["created_at"],
            last_sync=mock_data["last_sync"],
            token_expires_at=datetime.utcnow() + timedelta(days=60),
            ad_account_id=f"act_{random.randint(100000, 999999)}",
            business_id=f"biz_{random.randint(100000, 999999)}"
        )
        db.add(client)
        clients_created.append(client)
        print(f"Created client: {client.page_name}")
    
    db.commit()
    return clients_created

def seed_facebook_posts(db: Session, clients):
    """Seed Facebook posts for each client"""
    posts_created = []
    
    for client in clients:
        # Generate 15 posts per client
        mock_posts_data = mock_posts(client.id, count=15)
        
        for post_data in mock_posts_data:
            # Convert status string to enum
            if isinstance(post_data.get("status"), str):
                post_data["status"] = getattr(models.PostStatus, post_data["status"].upper())
            
            post = models.FacebookPost(**post_data)
            db.add(post)
            posts_created.append(post)
        
        print(f"Created 15 posts for {client.page_name}")
    
    db.commit()
    return posts_created

def seed_facebook_campaigns(db: Session, clients, user_id: str):
    """Seed Facebook campaigns for each client"""
    campaigns_created = []
    
    for client in clients:
        # Generate 8 campaigns per client
        mock_campaigns_data = mock_campaigns(client.id, count=8)
        
        for i, campaign_data in enumerate(mock_campaigns_data):
            # Convert status string to enum
            if isinstance(campaign_data.get("status"), str):
                status_map = {
                    "active": models.AdStatus.ACTIVE,
                    "paused": models.AdStatus.PAUSED,
                    "completed": models.AdStatus.COMPLETED,
                    "draft": models.AdStatus.DRAFT
                }
                campaign_data["status"] = status_map.get(campaign_data["status"], models.AdStatus.DRAFT)
            
            # Add required fields
            campaign = models.FacebookAdCampaign(
                **campaign_data,
                source_post_id=None,  # Some campaigns might not be from posts
                created_by=user_id,
                description="",
                call_to_action="LEARN_MORE",
                link_url="https://example.com/property-listing",
                creative_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                targeting={
                    "geo_locations": {"countries": ["US"], "cities": ["New York", "Los Angeles", "Chicago"]},
                    "age_min": 25,
                    "age_max": 55,
                    "interests": ["Real Estate", "Home Buyers", "Property Investment"]
                },
                facebook_campaign_id=f"camp_{random.randint(1000000, 9999999)}",
                facebook_adset_id=f"adset_{random.randint(1000000, 9999999)}",
                facebook_ad_id=f"ad_{random.randint(1000000, 9999999)}"
            )
            db.add(campaign)
            campaigns_created.append(campaign)
            
            # Add some analytics history for active campaigns
            if campaign.status == models.AdStatus.ACTIVE:
                for j in range(7):  # Last 7 days of data
                    analytics = models.FacebookAnalytics(
                        campaign_id=campaign.id,
                        recorded_at=datetime.utcnow() - timedelta(days=j),
                        date_start=datetime.utcnow() - timedelta(days=j+1),
                        date_stop=datetime.utcnow() - timedelta(days=j),
                        impressions=campaign.impressions // 7,
                        reach=campaign.reach // 7,
                        clicks=campaign.clicks // 7,
                        ctr=campaign.ctr,
                        cpc=campaign.cpc,
                        cpm=campaign.cpm,
                        spend=campaign.spend // 7,
                        conversions=campaign.conversions // 7,
                        post_engagements=random.randint(50, 200),
                        post_reactions=random.randint(20, 100),
                        post_comments=random.randint(5, 30),
                        post_shares=random.randint(2, 20),
                        demographics={
                            "age": {
                                "25-34": random.randint(25, 35),
                                "35-44": random.randint(35, 45),
                                "45-54": random.randint(15, 25),
                                "55+": random.randint(5, 15)
                            },
                            "gender": {
                                "male": random.randint(40, 50),
                                "female": random.randint(50, 60)
                            }
                        },
                        device_breakdown={
                            "mobile": random.randint(60, 70),
                            "desktop": random.randint(25, 35),
                            "tablet": random.randint(5, 10)
                        }
                    )
                    db.add(analytics)
        
        print(f"Created 8 campaigns for {client.page_name}")
    
    db.commit()
    return campaigns_created

def seed_ad_templates(db: Session, user_id: str):
    """Seed some ad templates"""
    templates = [
        {
            "name": "New Listing Announcement",
            "description": "Template for announcing new property listings",
            "template_type": "standard",
            "primary_text_template": "🏡 NEW LISTING ALERT! {property_type} in {neighborhood}. {bedrooms}BR/{bathrooms}BA, {square_feet} sq ft. {key_features}. Schedule your private tour today!",
            "headline_template": "Your Dream Home Awaits in {neighborhood}",
            "description_template": "Don't miss this incredible opportunity",
            "call_to_action": "LEARN_MORE",
            "rules": {
                "add_emojis": True,
                "include_hashtags": True,
                "urgency_phrases": ["Just Listed", "Won't Last Long", "Hot Property"]
            },
            "avg_ctr": 2.8,
            "avg_conversion_rate": 4.2,
            "times_used": 45
        },
        {
            "name": "Open House Invitation",
            "description": "Template for open house events",
            "template_type": "standard",
            "primary_text_template": "🎈 OPEN HOUSE {day} {time}! Come tour this beautiful {property_type} at {address}. {highlights}. Refreshments provided!",
            "headline_template": "Open House This {day}!",
            "description_template": "Tour this stunning property",
            "call_to_action": "GET_DIRECTIONS",
            "rules": {
                "add_emojis": True,
                "include_hashtags": ["OpenHouse", "RealEstate", "ForSale"],
                "urgency_phrases": ["This Weekend Only", "Don't Miss Out"]
            },
            "avg_ctr": 3.2,
            "avg_conversion_rate": 5.1,
            "times_used": 67
        },
        {
            "name": "Market Update",
            "description": "Template for market statistics and updates",
            "template_type": "standard",
            "primary_text_template": "📊 {area} MARKET UPDATE: {statistic}. {insight}. Thinking of buying or selling? Let's discuss your options!",
            "headline_template": "{area} Real Estate Market {trend}",
            "description_template": "Get expert market insights",
            "call_to_action": "CONTACT_US",
            "rules": {
                "add_emojis": True,
                "include_hashtags": ["MarketUpdate", "RealEstateMarket"],
                "personalize_location": True
            },
            "avg_ctr": 2.1,
            "avg_conversion_rate": 3.5,
            "times_used": 32
        }
    ]
    
    for template_data in templates:
        template = models.AdTemplate(
            user_id=user_id,
            **template_data
        )
        db.add(template)
    
    db.commit()
    print(f"Created {len(templates)} ad templates")

def main():
    """Main seeding function"""
    db = SessionLocal()
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Clear existing data
        clear_facebook_data(db)
        
        # Get or create a test user
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        if not user:
            print("User danny@nbrain.ai not found. Please create the user first.")
            return
        
        print(f"Seeding data for user: {user.email}")
        
        # Seed clients
        clients = seed_facebook_clients(db, user.id)
        
        # Seed posts
        posts = seed_facebook_posts(db, clients)
        
        # Seed campaigns
        campaigns = seed_facebook_campaigns(db, clients, user.id)
        
        # Seed templates
        seed_ad_templates(db, user.id)
        
        print("\n✅ Successfully seeded Facebook automation data!")
        print(f"- {len(clients)} clients")
        print(f"- {len(posts)} posts")
        print(f"- {len(campaigns)} campaigns")
        print(f"- 3 ad templates")
        print(f"- {len(campaigns) * 7} analytics records")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 