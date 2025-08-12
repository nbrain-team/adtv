"""
Seed production database with demo Facebook automation data
Auto-detects correct enum values from database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import SessionLocal, User, engine, Base
from facebook_automation import models
from facebook_automation.mock_data import MOCK_CLIENTS, MOCK_POSTS_TEMPLATES

def get_enum_values(enum_type_name: str):
    """Get actual enum values from PostgreSQL"""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = '{enum_type_name}'
            )
            ORDER BY enumsortorder;
        """))
        return [row[0] for row in result]

def seed_demo_data(user_email: str = None):
    """Seed demo data for a specific user"""
    db = SessionLocal()
    
    try:
        # Get actual enum values from database
        post_statuses = get_enum_values('poststatus')
        ad_statuses = get_enum_values('adstatus')
        
        print(f"📊 Database PostStatus values: {post_statuses}")
        print(f"📊 Database AdStatus values: {ad_statuses}")
        
        # Get the user
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        else:
            user = db.query(User).filter(User.role == "admin").first()
        
        if not user:
            print(f"❌ User not found: {user_email or 'No admin user'}")
            return
        
        print(f"\n🎯 Seeding demo data for user: {user.email}")
        
        # Check existing data
        existing_clients = db.query(models.FacebookClient).filter_by(user_id=user.id).count()
        if existing_clients > 0:
            print("⚠️  User already has Facebook data. Skipping to prevent duplicates.")
            return
        
        # Create clients
        print("\n📋 Creating Facebook clients...")
        clients_created = []
        
        for i, mock_data in enumerate(MOCK_CLIENTS[:3]):
            client = models.FacebookClient(
                id=str(uuid.uuid4()),
                user_id=user.id,
                facebook_user_id=mock_data["facebook_user_id"],
                facebook_page_id=f"{mock_data['facebook_page_id']}_{user.id[:8]}",
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
        
        # Filter post statuses - only use ones that exist in DB
        safe_post_statuses = [s for s in post_statuses if s.upper() in ['REVIEWED', 'CONVERTED', 'SKIPPED']]
        if not safe_post_statuses:
            safe_post_statuses = post_statuses  # Use whatever is in DB
        
        for client in clients_created:
            for i in range(15):
                template = random.choice(MOCK_POSTS_TEMPLATES)
                created_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                
                post = models.FacebookPost(
                    id=str(uuid.uuid4()),
                    client_id=client.id,
                    facebook_post_id=f"mock_fb_post_{client.id}_{i+1}",
                    post_url=f"https://facebook.com/mock_post_{client.id}_{i+1}",
                    message=template["message"],
                    created_time=created_time,
                    post_type=template["post_type"],
                    media_urls=template["media_urls"],
                    thumbnail_url=template["media_urls"][0] if template["media_urls"] else None,
                    likes_count=random.randint(*template["engagement"]["likes"]),
                    comments_count=random.randint(*template["engagement"]["comments"]),
                    shares_count=random.randint(*template["engagement"]["shares"]),
                    reach=random.randint(200, 2000),
                    status=random.choice(safe_post_statuses),
                    ai_quality_score=random.randint(*template["ai_score"]),
                    ai_suggestions={
                        "improved_headline": "Don't Miss This Opportunity!",
                        "improved_text": template["message"] + "\n\n🔥 Limited Time Offer!",
                        "call_to_action": "LEARN_MORE",
                        "target_audience": ["Real Estate", "Home Buyers"],
                        "recommended_budget": random.choice([50, 75, 100])
                    },
                    imported_at=created_time + timedelta(hours=random.randint(1, 24))
                )
                db.add(post)
                posts_created += 1
            
            print(f"  ✅ Created 15 posts for {client.page_name}")
        
        db.commit()
        
        # Create campaigns
        print("\n🚀 Creating ad campaigns...")
        campaigns_created = 0
        
        # Filter ad statuses
        safe_ad_statuses = [s for s in ad_statuses if s.upper() in ['ACTIVE', 'PAUSED', 'COMPLETED', 'DRAFT']]
        if not safe_ad_statuses:
            safe_ad_statuses = ad_statuses
        
        # Find active status
        active_status = next((s for s in ad_statuses if s.upper() == 'ACTIVE'), ad_statuses[0] if ad_statuses else 'ACTIVE')
        
        for client in clients_created:
            for i in range(8):
                status = random.choice(safe_ad_statuses)
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, 20))
                
                campaign = models.FacebookAdCampaign(
                    id=str(uuid.uuid4()),
                    client_id=client.id,
                    name=f"Realtor Campaign #{i+1} - {client.page_name}",
                    objective="REACH",
                    status=status,
                    daily_budget=random.choice([50, 75, 100]),
                    primary_text="Looking for your dream home? We make it happen!",
                    headline="Find Your Perfect Home",
                    description="Expert real estate services in your area",
                    call_to_action="LEARN_MORE",
                    link_url="https://example.com",
                    creative_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                    targeting={
                        "geo_locations": {"countries": ["US"]},
                        "age_min": 25,
                        "age_max": 65,
                        "interests": ["Real Estate", "Home Buyers"]
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
                    created_at=created_at,
                    created_by=user.id,
                    facebook_campaign_id=f"camp_{random.randint(1000000, 9999999)}",
                    facebook_adset_id=f"adset_{random.randint(1000000, 9999999)}",
                    facebook_ad_id=f"ad_{random.randint(1000000, 9999999)}"
                )
                
                if status == active_status:
                    campaign.launched_at = created_at + timedelta(hours=2)
                
                db.add(campaign)
                campaigns_created += 1
            
            print(f"  ✅ Created 8 campaigns for {client.page_name}")
        
        db.commit()
        
        print("\n✨ Demo data successfully seeded!")
        print(f"  • {len(clients_created)} realtor clients")
        print(f"  • {posts_created} Facebook posts")
        print(f"  • {campaigns_created} ad campaigns")
        print("\n🎯 Ready! Check out the Facebook Automation module.")
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    user_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🚀 Facebook Automation Demo Data Seeder")
    print("=====================================")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Seed the data
    seed_demo_data(user_email) 