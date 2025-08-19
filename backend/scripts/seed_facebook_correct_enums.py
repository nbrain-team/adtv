"""
Seed Facebook automation demo data with correct enum values for production
Uses: imported/reviewed/converted/skipped for posts and active/paused/completed/draft for campaigns
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import uuid
from core.database import SessionLocal, User, Base, engine
from facebook_automation import models
from facebook_automation.mock_data import MOCK_CLIENTS, MOCK_POSTS_TEMPLATES

def seed_facebook_demo(user_email: str = None):
    """Seed demo data with correct enum values"""
    db = SessionLocal()
    
    try:
        # Get user
        if user_email:
            user = db.query(User).filter(User.email == user_email).first()
        else:
            user = db.query(User).filter(User.role == "admin").first()
        
        if not user:
            print(f"❌ User not found: {user_email or 'No admin user'}")
            return
        
        print(f"🎯 Seeding demo data for: {user.email}")
        
        # Check existing data
        if db.query(models.FacebookClient).filter_by(user_id=user.id).count() > 0:
            print("⚠️  User already has Facebook data. Clean first with:")
            print(f"   python scripts/clean_facebook_data.py {user.email}")
            return
        
        # Create 3 realtor clients
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
        
        # Create posts with CORRECT statuses
        print("\n📝 Creating Facebook posts...")
        posts_created = 0
        
        # Use only valid PostStatus values from models.PostStatus
        valid_post_statuses = [
            models.PostStatus.IMPORTED.value,
            models.PostStatus.REVIEWED.value,
            models.PostStatus.CONVERTED.value,
            models.PostStatus.SKIPPED.value,
        ]
        
        for client in clients_created:
            for i in range(15):
                template = random.choice(MOCK_POSTS_TEMPLATES)
                created_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                
                # Bias toward reviewed/converted
                status_weights = [0.2, 0.4, 0.35, 0.05]  # imported, reviewed, converted, skipped
                status = random.choices(valid_post_statuses, weights=status_weights)[0]
                
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
                    reach=random.randint(500, 3000),
                    status=status,
                    ai_quality_score=random.randint(*template["ai_score"]),
                    ai_suggestions={
                        "improved_headline": "Don't Miss This Opportunity!",
                        "improved_text": template["message"] + "\n\n🔥 Limited Time Offer!",
                        "call_to_action": random.choice(["LEARN_MORE", "CONTACT_US", "GET_OFFER"]),
                        "target_audience": ["Real Estate", "Home Buyers", "Property Investment"],
                        "recommended_budget": random.choice([50, 75, 100, 125])
                    },
                    imported_at=created_time + timedelta(hours=random.randint(1, 24))
                )
                db.add(post)
                posts_created += 1
            
            print(f"  ✅ Created 15 posts for {client.page_name}")
        
        db.commit()
        
        # Create campaigns with CORRECT statuses
        print("\n🚀 Creating ad campaigns...")
        campaigns_created = 0
        
        # Use only valid AdStatus values from models.AdStatus
        valid_campaign_statuses = [
            models.AdStatus.ACTIVE.value,
            models.AdStatus.PAUSED.value,
            models.AdStatus.COMPLETED.value,
            models.AdStatus.DRAFT.value,
        ]
        
        for client in clients_created:
            for i in range(8):
                # Pick status - mix of active, paused, completed
                status_weights = [0.4, 0.2, 0.3, 0.1]  # ACTIVE, PAUSED, COMPLETED, DRAFT
                status = random.choices(valid_campaign_statuses, weights=status_weights)[0]
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, 20))
                
                # Generate realistic metrics
                impressions = random.randint(5000, 50000)
                reach = int(impressions * random.uniform(0.6, 0.8))
                clicks = int(impressions * random.uniform(0.01, 0.03))
                spend = random.uniform(50, 500)
                
                campaign = models.FacebookAdCampaign(
                    id=str(uuid.uuid4()),
                    client_id=client.id,
                    name=f"Realtor Campaign #{i+1} - {client.page_name.split(' - ')[0]}",
                    objective="REACH",
                    status=status,
                    daily_budget=random.choice([50, 75, 100, 125]),
                    primary_text="Looking for your dream home? We make it happen! 🏡",
                    headline="Find Your Perfect Home Today",
                    description="Expert real estate services in your area",
                    call_to_action="LEARN_MORE",
                    link_url="https://example.com/listings",
                    creative_urls=["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
                    targeting={
                        "geo_locations": {"countries": ["US"], "cities": ["New York", "Los Angeles"]},
                        "age_min": 25,
                        "age_max": 65,
                        "interests": ["Real Estate", "Home Buyers", "Property Investment"]
                    },
                    impressions=impressions,
                    reach=reach,
                    clicks=clicks,
                    ctr=round((clicks / impressions) * 100, 2) if impressions > 0 else 0,
                    cpc=round(spend / clicks, 2) if clicks > 0 else 0,
                    cpm=round((spend / impressions) * 1000, 2) if impressions > 0 else 0,
                    spend=spend,
                    conversions=int(clicks * random.uniform(0.05, 0.15)),
                    conversion_rate=random.uniform(2.0, 5.0),
                    roas=random.uniform(1.5, 4.0),
                    created_at=created_at,
                    created_by=user.id,
                    facebook_campaign_id=f"camp_{random.randint(1000000, 9999999)}",
                    facebook_adset_id=f"adset_{random.randint(1000000, 9999999)}",
                    facebook_ad_id=f"ad_{random.randint(1000000, 9999999)}"
                )
                
                # Set launched_at for active/completed campaigns
                if status in ["ACTIVE", "COMPLETED"]:
                    campaign.launched_at = created_at + timedelta(hours=2)
                
                db.add(campaign)
                campaigns_created += 1
                
                # Add analytics for active campaigns
                if status == "ACTIVE" and i < 3:  # Add analytics for first 3 active campaigns
                    for day in range(7):
                        analytics = models.FacebookAnalytics(
                            campaign_id=campaign.id,
                            recorded_at=datetime.utcnow() - timedelta(days=day),
                            date_start=datetime.utcnow() - timedelta(days=day+1),
                            date_stop=datetime.utcnow() - timedelta(days=day),
                            impressions=impressions // 7,
                            reach=reach // 7,
                            clicks=clicks // 7,
                            ctr=campaign.ctr,
                            cpc=campaign.cpc,
                            cpm=campaign.cpm,
                            spend=spend / 7,
                            conversions=random.randint(1, 5),
                            demographics={
                                "age": {"25-34": 35, "35-44": 40, "45-54": 20, "55+": 5},
                                "gender": {"male": 45, "female": 55}
                            },
                            device_breakdown={
                                "mobile": 65,
                                "desktop": 30,
                                "tablet": 5
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
        print(f"  • Analytics data for active campaigns")
        print("\n🎯 Ready! Login and check out the Facebook Automation module.")
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    user_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🚀 Facebook Automation Demo Data Seeder (Correct Enums)")
    print("======================================================")
    
    Base.metadata.create_all(bind=engine)
    seed_facebook_demo(user_email) 