"""
Mock data for Facebook Automation testing with realtor-specific content
"""

from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import uuid

# Mock realtor Facebook pages
MOCK_CLIENTS = [
    {
        "id": str(uuid.uuid4()),
        "facebook_user_id": "mock_fb_user_1",
        "facebook_page_id": "mock_page_1",
        "page_name": "Sarah Johnson - Premier Real Estate",
        "is_active": True,
        "auto_convert_posts": True,
        "default_daily_budget": 75.0,
        "default_campaign_duration": 7,
        "automation_rules": {
            "min_text_length": 50,
            "require_image": True,
            "auto_approve": False,
            "target_audience": "interests",
            "optimization_goal": "REACH"
        },
        "created_at": datetime.now() - timedelta(days=30),
        "last_sync": datetime.now() - timedelta(hours=2)
    },
    {
        "id": str(uuid.uuid4()),
        "facebook_user_id": "mock_fb_user_2",
        "facebook_page_id": "mock_page_2",
        "page_name": "Mike Chen - Luxury Homes Specialist",
        "is_active": True,
        "auto_convert_posts": False,
        "default_daily_budget": 100.0,
        "default_campaign_duration": 14,
        "automation_rules": {
            "min_text_length": 75,
            "require_image": True,
            "auto_approve": False,
            "target_audience": "lookalike",
            "optimization_goal": "TRAFFIC"
        },
        "created_at": datetime.now() - timedelta(days=60),
        "last_sync": datetime.now() - timedelta(days=1)
    },
    {
        "id": str(uuid.uuid4()),
        "facebook_user_id": "mock_fb_user_3",
        "facebook_page_id": "mock_page_3", 
        "page_name": "The Davis Team - Your Local Experts",
        "is_active": True,
        "auto_convert_posts": True,
        "default_daily_budget": 50.0,
        "default_campaign_duration": 5,
        "automation_rules": {
            "min_text_length": 40,
            "require_image": True,
            "auto_approve": True,
            "target_audience": "interests",
            "optimization_goal": "ENGAGEMENT"
        },
        "created_at": datetime.now() - timedelta(days=90),
        "last_sync": datetime.now() - timedelta(hours=6)
    }
]

# Mock realtor posts with realistic content
MOCK_POSTS_TEMPLATES = [
    {
        "message": "🏡 JUST LISTED! Stunning 4BR/3BA home in Riverside Heights. Updated kitchen, hardwood floors throughout, and a backyard oasis perfect for entertaining. This won't last long in today's market! DM me for a private showing.",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],
        "engagement": {"likes": (150, 300), "comments": (10, 30), "shares": (5, 15)},
        "ai_score": (75, 95)
    },
    {
        "message": "🔑 First-time homebuyers! Did you know you might qualify for down payment assistance programs? I've helped dozens of families achieve their dream of homeownership. Let's chat about your options - coffee's on me! ☕",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800"],
        "engagement": {"likes": (200, 400), "comments": (20, 50), "shares": (15, 40)},
        "ai_score": (80, 98)
    },
    {
        "message": "✨ SOLD in just 5 days! 🎉 Congratulations to my wonderful clients on the sale of their beautiful colonial. Proper pricing and staging made all the difference. Thinking of selling? Let's talk strategy!",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800"],
        "engagement": {"likes": (300, 500), "comments": (30, 60), "shares": (20, 35)},
        "ai_score": (85, 95)
    },
    {
        "message": "📊 Market Update: Inventory is still low but we're seeing more listings hit the market. Average days on market: 12. If you're thinking of buying this spring, let's get you pre-approved NOW! 📈",
        "post_type": "link",
        "media_urls": ["https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800"],
        "engagement": {"likes": (100, 200), "comments": (5, 15), "shares": (10, 25)},
        "ai_score": (70, 85)
    },
    {
        "message": "Open House this Saturday 1-4pm! 🏠 123 Oak Street - Charming 3BR ranch with updated everything! New roof, HVAC, and gorgeous kitchen. Priced to sell at $350k. See you there! 🎈",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800"],
        "engagement": {"likes": (80, 150), "comments": (10, 25), "shares": (5, 12)},
        "ai_score": (72, 88)
    },
    {
        "message": "Happy clients = Happy realtor! 😊 Thank you Jessica & Tom for trusting me with your home search. From offer to closing in 30 days! Here's to many happy memories in your new home! 🥂 #ClientTestimonial",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?w=800"],
        "engagement": {"likes": (250, 450), "comments": (40, 80), "shares": (10, 20)},
        "ai_score": (90, 98)
    },
    {
        "message": "🏘️ New Development Alert! Exclusive pre-construction pricing available for the first 10 buyers. Modern townhomes starting in the low $400s. Schedule your appointment today!",
        "post_type": "video",
        "media_urls": ["https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"],
        "engagement": {"likes": (180, 320), "comments": (25, 45), "shares": (30, 50)},
        "ai_score": (82, 92)
    },
    {
        "message": "Thinking of selling but worried about finding your next home? Ask me about our 'Buy Before You Sell' program! We make moving seamless and stress-free. 🏡➡️🏡",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1449844908441-8829872d2607?w=800"],
        "engagement": {"likes": (120, 220), "comments": (15, 30), "shares": (8, 18)},
        "ai_score": (78, 90)
    },
    {
        "message": "Friday Feature: This week's mortgage rates dropped to 6.5%! 📉 If you've been waiting for the right time, THIS IS IT! Let's get you pre-qualified this weekend.",
        "post_type": "link",
        "media_urls": ["https://images.unsplash.com/photo-1554224154-26032ffc0d07?w=800"],
        "engagement": {"likes": (90, 180), "comments": (8, 20), "shares": (12, 28)},
        "ai_score": (75, 85)
    },
    {
        "message": "🌟 5-STAR REVIEW! 'Sarah made our first home purchase a breeze. She was patient, knowledgeable, and fought to get us the best deal. Highly recommend!' - The Martinez Family. Thank you for your trust! ❤️",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1516156008625-3a9d6067fab5?w=800"],
        "engagement": {"likes": (350, 500), "comments": (50, 90), "shares": (15, 30)},
        "ai_score": (92, 99)
    }
]

def generate_mock_posts(client_id: str, count: int = 10) -> List[Dict[str, Any]]:
    """Generate mock Facebook posts for a client"""
    posts = []
    
    for i in range(count):
        template = random.choice(MOCK_POSTS_TEMPLATES)
        created_time = datetime.now() - timedelta(days=random.randint(1, 30))
        
        # Generate engagement metrics
        likes = random.randint(*template["engagement"]["likes"])
        comments = random.randint(*template["engagement"]["comments"])
        shares = random.randint(*template["engagement"]["shares"])
        reach = likes * random.randint(3, 5)
        
        # Generate AI suggestions
        ai_score = random.randint(*template["ai_score"])
        
        post_data = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "facebook_post_id": f"mock_fb_post_{client_id}_{i+1}",  # Make unique per client
            "post_url": f"https://facebook.com/mock_post_{client_id}_{i+1}",
            "message": template["message"],
            "created_time": created_time,
            "post_type": template["post_type"],
            "media_urls": template["media_urls"],
            "thumbnail_url": template["media_urls"][0] if template["media_urls"] else None,
            "likes_count": likes,
            "comments_count": comments,
            "shares_count": shares,
            "reach": reach,
            "status": random.choice(["reviewed", "reviewed", "converted", "skipped"]),
            "ai_quality_score": ai_score,
            "ai_suggestions": {
                "improved_headline": "Don't Miss This Opportunity!",
                "improved_text": template["message"] + "\n\n🔥 Limited Time Offer - Contact Me Today!",
                "call_to_action": random.choice(["LEARN_MORE", "CONTACT_US", "GET_OFFER", "SIGN_UP"]),
                "target_audience": ["Real Estate", "Home Buyers", "First Time Home Buyers", "Property Investment"],
                "recommended_budget": random.choice([50, 75, 100, 125])
            },
            "imported_at": created_time + timedelta(hours=random.randint(1, 24))
        }
        
        posts.append(post_data)
    
    return posts

def generate_mock_campaigns(client_id: str, count: int = 5) -> List[Dict[str, Any]]:
    """Generate mock ad campaigns"""
    campaigns = []
    objectives = ["REACH", "TRAFFIC", "ENGAGEMENT", "LEAD_GENERATION"]
    statuses = ["active", "active", "paused", "completed", "draft"]
    
    for i in range(count):
        created_at = datetime.now() - timedelta(days=random.randint(1, 20))
        daily_budget = random.choice([50, 75, 100, 125, 150])
        days_running = random.randint(1, 14)
        
        # Generate realistic metrics
        impressions = random.randint(5000, 50000) * days_running
        reach = int(impressions * random.uniform(0.6, 0.8))
        clicks = int(impressions * random.uniform(0.01, 0.03))
        ctr = (clicks / impressions) * 100 if impressions > 0 else 0
        spend = daily_budget * days_running * random.uniform(0.8, 1.0)
        cpc = spend / clicks if clicks > 0 else 0
        cpm = (spend / impressions) * 1000 if impressions > 0 else 0
        conversions = int(clicks * random.uniform(0.05, 0.15))
        conversion_rate = (conversions / clicks) * 100 if clicks > 0 else 0
        roas = random.uniform(1.5, 4.5)
        
        campaign_names = [
            "Spring Home Buyers Campaign",
            "Luxury Properties Showcase", 
            "First-Time Buyer Special",
            "Weekend Open House Promo",
            "Market Update Awareness",
            "Client Success Stories",
            "New Listing Alert Campaign"
        ]
        
        campaign = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "name": random.choice(campaign_names) + f" #{i+1}",
            "objective": random.choice(objectives),
            "status": statuses[i % len(statuses)],
            "primary_text": "Looking for your dream home? We make it happen! 🏡",
            "headline": "Find Your Perfect Home Today",
            "daily_budget": daily_budget,
            "impressions": impressions,
            "reach": reach,
            "clicks": clicks,
            "ctr": ctr,
            "cpc": cpc,
            "cpm": cpm,
            "spend": spend,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "roas": roas,
            "created_at": created_at,
            "launched_at": created_at + timedelta(hours=2) if statuses[i % len(statuses)] != "draft" else None
        }
        
        campaigns.append(campaign)
    
    return campaigns

def generate_mock_analytics(client_ids: List[str]) -> Dict[str, Any]:
    """Generate mock analytics data"""
    # Aggregate data across all clients
    total_campaigns = len(client_ids) * 5
    
    return {
        "total_spend": random.uniform(2000, 5000),
        "total_impressions": random.randint(100000, 500000),
        "total_reach": random.randint(50000, 250000),
        "total_clicks": random.randint(2000, 10000),
        "avg_ctr": random.uniform(1.5, 3.0),
        "avg_cpc": random.uniform(0.5, 2.0),
        "avg_cpm": random.uniform(5.0, 15.0),
        "total_conversions": random.randint(50, 200),
        "avg_conversion_rate": random.uniform(2.0, 5.0),
        "avg_roas": random.uniform(2.0, 4.0),
        "top_performing_campaigns": [
            {
                "id": str(uuid.uuid4()),
                "name": "Luxury Home Showcase #1",
                "roas": 4.2,
                "spend": 450.0,
                "conversions": 12
            },
            {
                "id": str(uuid.uuid4()), 
                "name": "First-Time Buyer Special #3",
                "roas": 3.8,
                "spend": 325.0,
                "conversions": 8
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Weekend Open House Promo #2",
                "roas": 3.5,
                "spend": 275.0,
                "conversions": 6
            }
        ],
        "demographics_breakdown": {
            "age": {
                "25-34": 35,
                "35-44": 40,
                "45-54": 20,
                "55+": 5
            },
            "gender": {
                "male": 45,
                "female": 55
            }
        },
        "device_breakdown": {
            "mobile": 65,
            "desktop": 30,
            "tablet": 5
        },
        "time_series": []  # TODO: Add time series data
    }

# Export mock data
mock_clients = MOCK_CLIENTS
mock_posts = generate_mock_posts
mock_campaigns = generate_mock_campaigns
mock_analytics = generate_mock_analytics 