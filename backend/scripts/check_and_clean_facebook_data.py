"""
Check and optionally clean Facebook automation data for a user
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import SessionLocal, User
from facebook_automation import models

def check_user_data(db: Session, user_email: str):
    """Check what Facebook data exists for a user"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        print(f"❌ User not found: {user_email}")
        return None
    
    print(f"\n📊 Facebook data for {user_email}:")
    
    clients = db.query(models.FacebookClient).filter_by(user_id=user.id).all()
    print(f"  • Clients: {len(clients)}")
    for client in clients:
        posts_count = db.query(models.FacebookPost).filter_by(client_id=client.id).count()
        campaigns_count = db.query(models.FacebookAdCampaign).filter_by(client_id=client.id).count()
        print(f"    - {client.page_name}: {posts_count} posts, {campaigns_count} campaigns")
    
    total_posts = db.query(models.FacebookPost).join(models.FacebookClient).filter(
        models.FacebookClient.user_id == user.id
    ).count()
    
    total_campaigns = db.query(models.FacebookAdCampaign).join(models.FacebookClient).filter(
        models.FacebookClient.user_id == user.id
    ).count()
    
    print(f"  • Total posts: {total_posts}")
    print(f"  • Total campaigns: {total_campaigns}")
    
    return user

def clean_user_data(db: Session, user_id: str):
    """Clean all Facebook data for a user"""
    try:
        # Delete all clients (cascades to posts, campaigns, analytics)
        clients = db.query(models.FacebookClient).filter_by(user_id=user_id).all()
        for client in clients:
            db.delete(client)
        
        db.commit()
        print("✅ All Facebook data cleaned successfully")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error cleaning data: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_and_clean_facebook_data.py <user_email> [--clean]")
        sys.exit(1)
    
    user_email = sys.argv[1]
    should_clean = "--clean" in sys.argv
    
    db = SessionLocal()
    try:
        user = check_user_data(db, user_email)
        
        if user and should_clean:
            print(f"\n⚠️  About to delete all Facebook data for {user_email}")
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() == "yes":
                if clean_user_data(db, user.id):
                    print("\n💡 You can now run the seed script again:")
                    print(f"   python scripts/seed_production_demo_data.py {user_email}")
            else:
                print("❌ Cleanup cancelled")
    finally:
        db.close() 