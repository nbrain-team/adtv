#!/usr/bin/env python3
"""
Diagnostic script to check Facebook automation setup and identify issues
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from core.database import Base, User
from facebook_automation.models import FacebookClient, FacebookPost, FacebookAdCampaign, FacebookAnalytics

# Get database URL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: No DATABASE_URL found in environment")
    sys.exit(1)

print(f"✅ Using database: {DATABASE_URL[:50]}...")

# Create engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("\n=== CHECKING DATABASE CONNECTION ===")
try:
    # Test connection
    result = session.execute(text("SELECT 1")).scalar()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

print("\n=== CHECKING TABLES ===")
inspector = inspect(engine)
tables = inspector.get_table_names()
required_tables = ['users', 'facebook_clients', 'facebook_posts', 'facebook_ad_campaigns', 'facebook_analytics']

for table in required_tables:
    if table in tables:
        print(f"✅ Table '{table}' exists")
    else:
        print(f"❌ Table '{table}' MISSING")

print("\n=== CHECKING ADMIN USER ===")
try:
    admin_user = session.query(User).filter(User.email == "danny@nbrain.ai").first()
    if admin_user:
        print(f"✅ Admin user found: {admin_user.email}")
        print(f"   - Role: {admin_user.role}")
        print(f"   - Permissions: {admin_user.permissions}")
        
        # Check if user has facebook-automation permission
        if admin_user.permissions and admin_user.permissions.get('facebook-automation'):
            print("   ✅ Has facebook-automation permission")
        else:
            print("   ❌ Missing facebook-automation permission")
    else:
        print("❌ Admin user danny@nbrain.ai not found")
except Exception as e:
    print(f"❌ Error checking admin user: {e}")

print("\n=== CHECKING FACEBOOK DATA ===")
try:
    # Count clients
    client_count = session.query(FacebookClient).count()
    print(f"Facebook Clients: {client_count}")
    
    if client_count > 0:
        # List clients
        clients = session.query(FacebookClient).all()
        for client in clients[:3]:  # Show first 3
            print(f"  - {client.page_name} (ID: {client.id})")
    
    # Count posts
    post_count = session.query(FacebookPost).count()
    print(f"Facebook Posts: {post_count}")
    
    if post_count > 0:
        # Check post statuses
        posts = session.query(FacebookPost).limit(5).all()
        print("  Sample post statuses:")
        for post in posts:
            print(f"    - Post {post.id}: status='{post.status}'")
    
    # Count campaigns
    campaign_count = session.query(FacebookAdCampaign).count()
    print(f"Facebook Campaigns: {campaign_count}")
    
    # Count analytics
    analytics_count = session.query(FacebookAnalytics).count()
    print(f"Facebook Analytics: {analytics_count}")
    
except Exception as e:
    print(f"❌ Error checking Facebook data: {e}")
    import traceback
    traceback.print_exc()

print("\n=== CHECKING ENUM VALUES ===")
try:
    # Check PostStatus enum
    result = session.execute(text("""
        SELECT enumlabel 
        FROM pg_enum 
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
        WHERE pg_type.typname = 'poststatus'
        ORDER BY enumsortorder
    """))
    post_statuses = [row[0] for row in result]
    print(f"PostStatus enum values: {post_statuses}")
    
    # Check AdStatus enum
    result = session.execute(text("""
        SELECT enumlabel 
        FROM pg_enum 
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
        WHERE pg_type.typname = 'adstatus'
        ORDER BY enumsortorder
    """))
    ad_statuses = [row[0] for row in result]
    print(f"AdStatus enum values: {ad_statuses}")
    
except Exception as e:
    print(f"ℹ️  Could not check enum values (might be SQLite): {e}")

print("\n=== TESTING QUERY ===")
try:
    # Try to run the same query that the API would run
    if admin_user and client_count > 0:
        client = clients[0]
        posts = session.query(FacebookPost).filter(
            FacebookPost.client_id == client.id
        ).limit(10).all()
        print(f"✅ Successfully queried {len(posts)} posts for client {client.page_name}")
    else:
        print("⚠️  Cannot test query - no clients found")
except Exception as e:
    print(f"❌ Error testing query: {e}")
    import traceback
    traceback.print_exc()

print("\n=== RECOMMENDATIONS ===")
if post_count == 0 or client_count == 0:
    print("🔧 No Facebook data found. Run the seeding script:")
    print("   python scripts/seed_facebook_correct_enums.py danny@nbrain.ai")
elif 'facebook-automation' not in (admin_user.permissions or {}):
    print("🔧 Admin user missing permission. Run:")
    print("   python scripts/add_facebook_automation_permission.py")
else:
    print("✅ Setup looks good. Check the application logs for the 500 error details.")

session.close() 