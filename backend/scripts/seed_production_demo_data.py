"""
Seed production database with demo Facebook automation data
Safe to run multiple times - checks for existing data
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import uuid
from sqlalchemy.orm import Session
from core.database import SessionLocal, User, engine, Base
from facebook_automation import models
from facebook_automation.mock_data import (
    MOCK_CLIENTS, 
    mock_posts,
    mock_campaigns
)

def check_existing_data(db: Session, user_id: str):
    """Check if user already has Facebook data"""
    existing_clients = db.query(models.FacebookClient).filter_by(user_id=user_id).count()
    return existing_clients > 0

def seed_demo_data(user_email: str = None):
    """Seed demo data for a specific user"""
    db = SessionLocal()
    
    try:
        # Get the user
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        else:
            # Default to first admin user
            user = db.query(User).filter(User.role == "admin").first()
        
        if not user:
            print(f"❌ User not found: {user_email or 'No admin user'}")
            return
        
        print(f"🎯 Seeding demo data for user: {user.email}")
        
        # Check if user already has data
        if check_existing_data(db, user.id):
            print("⚠️  User already has Facebook data. Skipping to prevent duplicates.")
            print("   To add more data, delete existing clients first.")
            return
        
        # Create clients
        print("\n📋 Creating Facebook clients...")
        clients_created = []
        
        for i, mock_data in enumerate(MOCK_CLIENTS[:3]):
            client = models.FacebookClient(
                id=str(uuid.uuid4()),
                user_id=user.id,
                facebook_user_id=mock_data["facebook_user_id"],
                facebook_page_id=f"{mock_data['facebook_page_id']}_{user.id[:8]}",  # Make unique
                page_name=mock_data["page_name"],
                page_access_token="mock_token_" + str(i),
                is_active=mock_data["is_active"],
                auto_convert_posts=mock_data["auto_convert_posts"],
                default_daily_budget=mock_data["default_daily_budget"],
                default_campaign_duration=mock_data["default_campaign_duration"],
                automation_rules=mock_data["automation_rules"],
                created_at=mock_data["created_at"],
                last_sync=mock_data["last_sync"],
                token_expires_at=datetime.utcnow() + timedelta(days=60)
            )
            db.add(client)
            clients_created.append(client)
            print(f"  ✅ Created: {client.page_name}")
        
        db.commit()
        
        # Create posts
        print("\n📝 Creating Facebook posts...")
        posts_created = 0
        
        for client in clients_created:
            mock_posts_data = mock_posts(client.id, count=15)
            
            for post_data in mock_posts_data:
                # Handle status - production DB expects lowercase enum values
                if "status" in post_data and isinstance(post_data["status"], str):
                    # Ensure status is lowercase
                    post_data["status"] = post_data["status"].lower()
                    # Only use status values that exist in production
                    valid_statuses = ["reviewed", "converted", "skipped"]
                    if post_data["status"] not in valid_statuses:
                        post_data["status"] = "reviewed"  # Safe default
                
                post = models.FacebookPost(**post_data)
                db.add(post)
                posts_created += 1
            
            print(f"  ✅ Created 15 posts for {client.page_name}")
        
        db.commit()
        
        # Create campaigns
        print("\n🚀 Creating ad campaigns...")
        campaigns_created = 0
        
        for client in clients_created:
            mock_campaigns_data = mock_campaigns(client.id, count=8)
            
            for campaign_data in enumerate(mock_campaigns_data):
                campaign_data = campaign_data[1]  # Get the actual data
                
                # Convert status
                if isinstance(campaign_data.get("status"), str):
                    # Ensure status is lowercase for production
                    campaign_data["status"] = campaign_data["status"].lower()
                    status_map = {
                        "active": "active",
                        "paused": "paused", 
                        "completed": "completed",
                        "draft": "draft"
                    }
                    campaign_data["status"] = status_map.get(campaign_data["status"], "draft")
                
                # Add required fields
                campaign = models.FacebookAdCampaign(
                    **campaign_data,
                    source_post_id=None,
                    created_by=user.id,
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
                campaigns_created += 1
                
                # Add analytics for active campaigns
                if campaign.status == models.AdStatus.ACTIVE:
                    for j in range(7):  # Last 7 days
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
            
            print(f"  ✅ Created 8 campaigns for {client.page_name}")
        
        db.commit()
        
        # Summary
        print("\n✨ Demo data successfully seeded!")
        print(f"  • {len(clients_created)} realtor clients")
        print(f"  • {posts_created} Facebook posts")
        print(f"  • {campaigns_created} ad campaigns")
        print(f"  • {campaigns_created * 7} analytics records")
        print("\n🎯 Ready to use! Login and check out the Facebook Automation module.")
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Check for user email argument
    user_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🚀 Facebook Automation Demo Data Seeder")
    print("=====================================")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Seed the data
    seed_demo_data(user_email) 