"""
Minimal safe seeding script - only uses enum values that definitely work
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import uuid
from core.database import SessionLocal, User, Base, engine
from facebook_automation import models

def seed_minimal_data(user_email: str = None):
    """Seed minimal demo data with only safe values"""
    db = SessionLocal()
    
    try:
        # Get user
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        else:
            user = db.query(User).filter(User.role == "admin").first()
        
        if not user:
            print(f"❌ User not found")
            return
        
        print(f"🎯 Seeding minimal demo data for: {user.email}")
        
        # Check existing
        if db.query(models.FacebookClient).filter_by(user_id=user.id).count() > 0:
            print("⚠️  User already has data. Clean first.")
            return
        
        # Create 1 client
        print("\n📋 Creating client...")
        client = models.FacebookClient(
            id=str(uuid.uuid4()),
            user_id=user.id,
            facebook_user_id="mock_user_1",
            facebook_page_id=f"mock_page_{user.id[:8]}",
            page_name="Demo Realtor - Sarah Johnson",
            page_access_token="mock_token",
            is_active=True,
            auto_convert_posts=True,
            default_daily_budget=75.0,
            default_campaign_duration=7,
            automation_rules={
                "min_text_length": 50,
                "require_image": True,
                "auto_approve": False
            },
            created_at=datetime.utcnow() - timedelta(days=30),
            last_sync=datetime.utcnow() - timedelta(hours=2),
            token_expires_at=datetime.utcnow() + timedelta(days=60)
        )
        db.add(client)
        db.commit()
        print(f"  ✅ Created: {client.page_name}")
        
        # Create 5 posts - ONLY use REVIEWED status
        print("\n📝 Creating posts...")
        for i in range(5):
            post = models.FacebookPost(
                id=str(uuid.uuid4()),
                client_id=client.id,
                facebook_post_id=f"fb_post_{client.id}_{i+1}",
                post_url=f"https://facebook.com/post_{i+1}",
                message=f"🏡 Beautiful {i+3} bedroom home in prime location! Schedule your showing today. #{i+1}",
                created_time=datetime.utcnow() - timedelta(days=i+1),
                post_type="photo",
                media_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                thumbnail_url="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800",
                likes_count=random.randint(50, 200),
                comments_count=random.randint(5, 50),
                shares_count=random.randint(2, 20),
                reach=random.randint(200, 1000),
                status="REVIEWED",  # ONLY REVIEWED
                ai_quality_score=random.uniform(70, 95),
                ai_suggestions={
                    "improved_headline": "Your Dream Home Awaits!",
                    "improved_text": "Don't miss this opportunity!",
                    "call_to_action": "LEARN_MORE",
                    "target_audience": ["Real Estate"],
                    "recommended_budget": 75
                },
                imported_at=datetime.utcnow()
            )
            db.add(post)
        
        db.commit()
        print("  ✅ Created 5 posts")
        
        # Create 2 campaigns - try ACTIVE and PAUSED
        print("\n🚀 Creating campaigns...")
        for i, status in enumerate(["ACTIVE", "PAUSED"]):
            try:
                campaign = models.FacebookAdCampaign(
                    id=str(uuid.uuid4()),
                    client_id=client.id,
                    name=f"Demo Campaign #{i+1}",
                    objective="REACH",
                    status=status,
                    daily_budget=75.0,
                    primary_text="Find your dream home today!",
                    headline="Exclusive Properties",
                    description="Professional real estate services",
                    call_to_action="LEARN_MORE",
                    link_url="https://example.com",
                    creative_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                    targeting={
                        "geo_locations": {"countries": ["US"]},
                        "age_min": 25,
                        "age_max": 65
                    },
                    impressions=random.randint(1000, 5000),
                    reach=random.randint(500, 2500),
                    clicks=random.randint(50, 200),
                    ctr=2.5,
                    cpc=1.0,
                    cpm=10.0,
                    spend=float(random.randint(50, 150)),
                    conversions=random.randint(5, 20),
                    conversion_rate=3.0,
                    roas=2.5,
                    created_at=datetime.utcnow() - timedelta(days=i+1),
                    created_by=user.id,
                    facebook_campaign_id=f"camp_{i+1}",
                    facebook_adset_id=f"adset_{i+1}",
                    facebook_ad_id=f"ad_{i+1}"
                )
                
                if status == "ACTIVE":
                    campaign.launched_at = campaign.created_at + timedelta(hours=1)
                
                db.add(campaign)
                db.commit()
                print(f"  ✅ Created campaign with status: {status}")
            except Exception as e:
                print(f"  ❌ Failed to create campaign with {status}: {e}")
                db.rollback()
        
        print("\n✨ Minimal demo data seeded successfully!")
        print("🎯 Check the Facebook Automation module now!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    user_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🚀 Minimal Facebook Demo Seeder")
    print("===============================")
    
    Base.metadata.create_all(bind=engine)
    seed_minimal_data(user_email) 