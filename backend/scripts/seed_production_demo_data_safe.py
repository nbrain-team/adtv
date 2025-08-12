"""
Seed production database with demo Facebook automation data - SAFE VERSION
Explicitly handles enum case issues for production PostgreSQL
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
        
        # Import mock data here to ensure we get the latest version
        from facebook_automation.mock_data import MOCK_CLIENTS
        
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
        
        # Create posts with SAFE status values
        print("\n📝 Creating Facebook posts...")
        posts_created = 0
        
        # Safe status values for production
        safe_statuses = ["reviewed", "converted", "skipped"]
        
        for client in clients_created:
            for i in range(15):  # 15 posts per client
                post = models.FacebookPost(
                    id=str(uuid.uuid4()),
                    client_id=client.id,
                    facebook_post_id=f"mock_fb_post_{client.id}_{i+1}",
                    post_url=f"https://facebook.com/mock_post_{client.id}_{i+1}",
                    message=f"🏡 Amazing property opportunity! Contact {client.page_name} for details. #{i+1}",
                    created_time=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    post_type=random.choice(["photo", "video", "link"]),
                    media_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                    thumbnail_url="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800",
                    likes_count=random.randint(50, 500),
                    comments_count=random.randint(5, 100),
                    shares_count=random.randint(2, 50),
                    reach=random.randint(200, 2000),
                    status=random.choice(safe_statuses),  # Only safe values
                    ai_quality_score=random.uniform(70, 98),
                    ai_suggestions={
                        "improved_headline": "Don't Miss This Opportunity!",
                        "improved_text": "Contact us today for exclusive viewing!",
                        "call_to_action": "LEARN_MORE",
                        "target_audience": ["Real Estate", "Home Buyers"],
                        "recommended_budget": 75
                    },
                    imported_at=datetime.utcnow()
                )
                db.add(post)
                posts_created += 1
            
            print(f"  ✅ Created 15 posts for {client.page_name}")
        
        db.commit()
        
        # Create campaigns with SAFE status values
        print("\n🚀 Creating ad campaigns...")
        campaigns_created = 0
        
        # Safe campaign statuses
        safe_campaign_statuses = ["active", "paused", "completed", "draft"]
        
        for client in clients_created:
            for i in range(8):  # 8 campaigns per client
                campaign = models.FacebookAdCampaign(
                    id=str(uuid.uuid4()),
                    client_id=client.id,
                    name=f"Campaign #{i+1} - {client.page_name}",
                    objective="REACH",
                    status=random.choice(safe_campaign_statuses),  # Safe values
                    daily_budget=random.choice([50, 75, 100]),
                    primary_text="Looking for your dream home? We can help!",
                    headline="Find Your Perfect Home",
                    description="Expert real estate services",
                    call_to_action="LEARN_MORE",
                    link_url="https://example.com",
                    creative_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                    targeting={
                        "geo_locations": {"countries": ["US"]},
                        "age_min": 25,
                        "age_max": 65
                    },
                    impressions=random.randint(1000, 50000),
                    reach=random.randint(500, 25000),
                    clicks=random.randint(50, 1000),
                    ctr=random.uniform(1.0, 3.0),
                    cpc=random.uniform(0.5, 2.0),
                    cpm=random.uniform(5.0, 15.0),
                    spend=random.uniform(50, 500),
                    conversions=random.randint(5, 50),
                    conversion_rate=random.uniform(1.0, 5.0),
                    roas=random.uniform(1.5, 4.0),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                    created_by=user.id,
                    facebook_campaign_id=f"camp_{random.randint(1000000, 9999999)}",
                    facebook_adset_id=f"adset_{random.randint(1000000, 9999999)}",
                    facebook_ad_id=f"ad_{random.randint(1000000, 9999999)}"
                )
                
                if campaign.status == "active":
                    campaign.launched_at = campaign.created_at + timedelta(hours=2)
                
                db.add(campaign)
                campaigns_created += 1
            
            print(f"  ✅ Created 8 campaigns for {client.page_name}")
        
        db.commit()
        
        # Summary
        print("\n✨ Demo data successfully seeded!")
        print(f"  • {len(clients_created)} realtor clients")
        print(f"  • {posts_created} Facebook posts") 
        print(f"  • {campaigns_created} ad campaigns")
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
    
    print("🚀 Facebook Automation Demo Data Seeder (SAFE VERSION)")
    print("===================================================")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Seed the data
    seed_demo_data(user_email) 