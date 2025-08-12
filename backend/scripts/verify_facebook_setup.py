"""
Verify Facebook Automation setup in production
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, User, engine
from sqlalchemy import inspect
import facebook_automation.models

def verify_setup():
    """Verify Facebook automation is properly set up"""
    print("🔍 Facebook Automation Setup Verification")
    print("=" * 50)
    
    # Check tables
    print("\n📊 Checking database tables...")
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    fb_tables = [t for t in all_tables if 'facebook' in t]
    
    required_tables = ['facebook_clients', 'facebook_posts', 'facebook_ad_campaigns', 'facebook_analytics', 'ad_templates']
    
    for table in required_tables:
        if table in all_tables:
            print(f"  ✅ {table} exists")
        else:
            print(f"  ❌ {table} missing")
    
    # Check admin users
    print("\n👤 Checking admin users...")
    db = SessionLocal()
    try:
        admin_users = db.query(User).filter(User.role == "admin").all()
        
        if not admin_users:
            print("  ❌ No admin users found!")
        else:
            for user in admin_users:
                has_fb = user.permissions.get('facebook-automation', False) if user.permissions else False
                status = "✅" if has_fb else "❌"
                print(f"  {status} {user.email} - facebook-automation: {has_fb}")
        
        # Check existing Facebook data
        print("\n📈 Checking existing Facebook data...")
        client_count = db.query(facebook_automation.models.FacebookClient).count()
        post_count = db.query(facebook_automation.models.FacebookPost).count()
        campaign_count = db.query(facebook_automation.models.FacebookAdCampaign).count()
        analytics_count = db.query(facebook_automation.models.FacebookAnalytics).count()
        
        print(f"  • Clients: {client_count}")
        print(f"  • Posts: {post_count}")
        print(f"  • Campaigns: {campaign_count}")
        print(f"  • Analytics records: {analytics_count}")
        
        if client_count == 0:
            print("\n💡 No demo data found. Run this to add demo data:")
            print("   python scripts/seed_production_demo_data.py")
        
    finally:
        db.close()
    
    print("\n✨ Verification complete!")

if __name__ == "__main__":
    verify_setup() 