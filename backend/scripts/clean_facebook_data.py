"""
Clean Facebook automation data for a user (non-interactive)
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, User
from facebook_automation import models

def clean_facebook_data(user_email: str):
    """Clean all Facebook data for a user"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"❌ User not found: {user_email}")
            return False
        
        # Count existing data
        clients_count = db.query(models.FacebookClient).filter_by(user_id=user.id).count()
        
        if clients_count == 0:
            print("✅ No Facebook data to clean")
            return True
        
        print(f"🧹 Cleaning {clients_count} clients and all related data...")
        
        # Delete all clients (cascades to posts, campaigns, analytics)
        db.query(models.FacebookClient).filter_by(user_id=user.id).delete()
        
        db.commit()
        print("✅ All Facebook data cleaned successfully")
        print(f"\n💡 Now run: python scripts/seed_production_demo_data.py {user_email}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error cleaning data: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_facebook_data.py <user_email>")
        sys.exit(1)
    
    user_email = sys.argv[1]
    clean_facebook_data(user_email) 