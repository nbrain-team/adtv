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
        "message": "🏡 JUST LISTED! Stunning 4BR/3BA colonial in prime location. Hardwood floors, gourmet kitchen, and spacious backyard perfect for entertaining. Won't last long at this price! Schedule your private showing today.",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop"],
        "engagement": {"likes": [120, 250], "comments": [15, 35], "shares": [10, 25]},
        "ai_score": [85, 95]
    },
    {
        "message": "🔑 Congratulations to the Johnson family on finding their dream home! It was such a pleasure helping you navigate this journey. Here's to new beginnings and making memories in your beautiful new space! #JustSold #HappyHomeowners #RealEstateSuccess",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&h=600&fit=crop"],
        "engagement": {"likes": [200, 400], "comments": [30, 60], "shares": [20, 40]},
        "ai_score": [90, 98]
    },
    {
        "message": "📊 Market Update: Home prices in our area increased by 8% this quarter! If you're thinking about selling, now might be the perfect time. Contact me for a FREE home valuation and market analysis. Let's maximize your home's value together!",
        "post_type": "link",
        "media_urls": ["https://images.unsplash.com/photo-1460472178825-e5240623afd5?w=800&h=600&fit=crop"],
        "engagement": {"likes": [80, 150], "comments": [10, 25], "shares": [15, 30]},
        "ai_score": [75, 85]
    },
    {
        "message": "✨ Open House this Weekend! Saturday & Sunday 1-4 PM. Tour this gorgeous 3BR/2BA ranch with updated kitchen, finished basement, and beautiful landscaping. 123 Oak Street. See you there! 🏠",
        "post_type": "event",
        "media_urls": ["https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop"],
        "engagement": {"likes": [100, 200], "comments": [20, 40], "shares": [25, 50]},
        "ai_score": [80, 90]
    },
    {
        "message": "💡 First-Time Buyer Tip: Did you know you might qualify for down payment assistance programs? Many buyers don't realize these opportunities exist! Let's chat about your options and find the perfect program for you. Your dream home is closer than you think!",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1560520653-9e0e4c89eb11?w=800&h=600&fit=crop"],
        "engagement": {"likes": [150, 300], "comments": [25, 50], "shares": [30, 60]},
        "ai_score": [88, 96]
    },
    {
        "message": "🌟 Just closed on this beautiful waterfront property! My clients are thrilled to start their lake life adventure. Looking for your own piece of paradise? I have exclusive access to upcoming waterfront listings. Let's connect! #LuxuryRealEstate #WaterfrontLiving",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop"],
        "engagement": {"likes": [250, 500], "comments": [40, 80], "shares": [35, 70]},
        "ai_score": [92, 99]
    },
    {
        "message": "🏘️ Thinking of investing in rental properties? Here are my top 3 neighborhoods with the best ROI potential in 2024. Swipe to see average rental rates and appreciation trends. Ready to build your portfolio? Let's discuss your investment strategy! 📈",
        "post_type": "carousel",
        "media_urls": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1602941525421-8f8b81d3edbb?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop"
        ],
        "engagement": {"likes": [180, 350], "comments": [35, 70], "shares": [40, 80]},
        "ai_score": [87, 95]
    },
    {
        "message": "🎉 PRICE REDUCED! This charming 2BR condo in downtown is now $15K under asking! Perfect for young professionals or investors. Walking distance to restaurants, shopping, and public transit. Virtual tour available - DM me for the link!",
        "post_type": "video",
        "media_urls": ["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=600&fit=crop"],
        "engagement": {"likes": [130, 260], "comments": [22, 45], "shares": [28, 55]},
        "ai_score": [83, 92]
    },
    {
        "message": "🏡 Home Staging Tip: Did you know that staged homes sell 88% faster than non-staged homes? Here's my latest staging transformation - swipe to see the before & after! Thinking of selling? Let's discuss how to showcase your home's full potential.",
        "post_type": "carousel",
        "media_urls": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1556909114-44e3e70034e2?w=800&h=600&fit=crop"
        ],
        "engagement": {"likes": [220, 440], "comments": [45, 90], "shares": [50, 100]},
        "ai_score": [91, 98]
    },
    {
        "message": "☕ Good morning! Starting my day with property tours in Maple Grove. This neighborhood has seen 12% appreciation in the last year! If you're curious about home values in your area, drop your neighborhood in the comments and I'll share the latest stats! 📊",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1449844908441-8829872d2607?w=800&h=600&fit=crop"],
        "engagement": {"likes": [90, 180], "comments": [30, 60], "shares": [12, 25]},
        "ai_score": [78, 86]
    },
    {
        "message": "🔥 HOT NEW LISTING! This modern farmhouse features 5BR/4BA, chef's kitchen, home office, and 3-car garage on 2 acres. Plus a brand new pool! Virtual walkthrough premiering tomorrow at 7 PM - comment 'TOUR' to get the exclusive link!",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop"],
        "engagement": {"likes": [300, 600], "comments": [60, 120], "shares": [70, 140]},
        "ai_score": [94, 99]
    },
    {
        "message": "📚 Real Estate Myth Buster: You DON'T need 20% down to buy a home! There are loans available with as little as 3% down. Let's explore your financing options and find the right path to homeownership for you. Knowledge is power! 💪",
        "post_type": "graphic",
        "media_urls": ["https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&h=600&fit=crop"],
        "engagement": {"likes": [160, 320], "comments": [28, 55], "shares": [45, 90]},
        "ai_score": [86, 94]
    },
    {
        "message": "🏆 So honored to receive the Top Producer Award for Q3! This wouldn't be possible without my amazing clients who trust me with their real estate journey. Thank you for your referrals and continued support. Here's to helping even more families find their perfect homes! 🥂",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=600&fit=crop"],
        "engagement": {"likes": [280, 560], "comments": [70, 140], "shares": [25, 50]},
        "ai_score": [89, 97]
    },
    {
        "message": "🌳 Spring is the perfect time to boost your curb appeal! Here are 5 quick fixes that can add $10K+ to your home value: fresh mulch, power washing, new house numbers, updated lighting, and colorful planters. What's your favorite curb appeal tip? Share below!",
        "post_type": "carousel",
        "media_urls": [
            "https://images.unsplash.com/photo-1416331108676-a22ccb276e35?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800&h=600&fit=crop"
        ],
        "engagement": {"likes": [140, 280], "comments": [32, 65], "shares": [38, 75]},
        "ai_score": [85, 93]
    },
    {
        "message": "🎯 COMING SOON! Exclusive pre-market opportunity in Westfield Estates. 4BR/3BA with pool and guest house. Serious buyers only - contact me for early access before it hits the MLS next week. This one will go FAST! 🏃‍♂️",
        "post_type": "photo",
        "media_urls": ["https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&h=600&fit=crop"],
        "engagement": {"likes": [190, 380], "comments": [42, 85], "shares": [55, 110]},
        "ai_score": [90, 97]
    },
    {
        "message": "📅 Market Watch: Interest rates holding steady this week at 7.1%. If you're on the fence about buying, let's run the numbers together. Sometimes waiting costs more than you think! Free buyer consultations available this week - link in bio to schedule.",
        "post_type": "link",
        "media_urls": ["https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop"],
        "engagement": {"likes": [70, 140], "comments": [15, 30], "shares": [20, 40]},
        "ai_score": [76, 84]
    }
]

def generate_mock_posts(client_id: str, page_name: str):
    """Generate mock posts for a client with realistic realtor content"""
    posts = []
    
    # Generate posts for the last 14 days with varying times
    base_date = datetime.now()
    
    # More realistic posting schedule - 2-3 posts per day on weekdays, 1 on weekends
    posting_schedule = [
        # Week 1
        {'day_offset': -13, 'times': ['09:00', '14:30']},  # Monday
        {'day_offset': -12, 'times': ['10:15', '16:00', '19:30']},  # Tuesday  
        {'day_offset': -11, 'times': ['08:30', '13:45']},  # Wednesday
        {'day_offset': -10, 'times': ['11:00', '15:30', '18:00']},  # Thursday
        {'day_offset': -9, 'times': ['09:30', '14:00']},  # Friday
        {'day_offset': -8, 'times': ['10:00']},  # Saturday
        {'day_offset': -7, 'times': ['11:30']},  # Sunday
        # Week 2
        {'day_offset': -6, 'times': ['09:15', '15:00']},  # Monday
        {'day_offset': -5, 'times': ['08:45', '13:30', '17:45']},  # Tuesday
        {'day_offset': -4, 'times': ['10:30', '16:15']},  # Wednesday
        {'day_offset': -3, 'times': ['09:00', '14:45', '18:30']},  # Thursday
        {'day_offset': -2, 'times': ['11:15', '15:45']},  # Friday
        {'day_offset': -1, 'times': ['10:45']},  # Saturday
        {'day_offset': 0, 'times': ['09:30', '14:00']},  # Today
    ]
    
    post_index = 0
    for schedule in posting_schedule:
        for time_str in schedule['times']:
            if post_index >= len(MOCK_POSTS_TEMPLATES):
                post_index = 0
            
            template = MOCK_POSTS_TEMPLATES[post_index]
            post_date = base_date + timedelta(days=schedule['day_offset'])
            
            # Parse time and set it on the date
            hour, minute = map(int, time_str.split(':'))
            post_date = post_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Add some variety to engagement metrics
            base_likes = template['engagement']['likes'][0] # Use the lower bound for base
            base_comments = template['engagement']['comments'][0] # Use the lower bound for base
            base_shares = template['engagement']['shares'][0] # Use the lower bound for base
            
            posts.append({
                'client_id': client_id,
                'facebook_page_id': f'mock_page_{client_id}',
                'facebook_post_id': f'mock_fb_post_{client_id}_{post_date.timestamp()}',
                'post_url': f'https://facebook.com/{page_name}/posts/mock_{post_date.timestamp()}',
                'message': template['message'],
                'created_time': post_date,
                'post_type': template['post_type'],
                'media_urls': template['media_urls'],
                'thumbnail_url': template['media_urls'][0] if template['media_urls'] else None,
                'likes_count': base_likes + random.randint(-10, 20),
                'comments_count': base_comments + random.randint(-2, 5),
                'shares_count': base_shares + random.randint(-1, 3),
                'reach': (base_likes + random.randint(100, 500)) * 3,
                'status': random.choice(['REVIEWED', 'CONVERTED', 'CONVERTED', 'REVIEWED']),  # More converted posts
                'ai_quality_score': template['ai_score'][0] + random.randint(-5, 5), # Add some variation
                'ai_suggestions': {
                    'improved_text': template['message'] + ' 🏡 Contact us today!',
                    'improved_headline': 'Your Dream Home Awaits',
                    'target_audience': ['Home Buyers', 'Real Estate Investors', 'First Time Buyers'],
                    'recommended_budget': random.randint(30, 100),
                    'call_to_action': 'LEARN_MORE'
                }
            })
            
            post_index += 1
    
    return posts

def generate_mock_posts_wrapper(client_id: str, count: int = 15) -> List[Dict[str, Any]]:
    """Backward compatible wrapper for generate_mock_posts"""
    # For backward compatibility, use a default page name
    page_name = f"mock_page_{client_id}"
    
    # Generate posts using the new function
    all_posts = generate_mock_posts(client_id, page_name)
    
    # Return only the requested count
    return all_posts[:count]

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
mock_posts = generate_mock_posts_wrapper  # Use the wrapper for backward compatibility
mock_campaigns = generate_mock_campaigns
mock_analytics = generate_mock_analytics 