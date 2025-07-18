#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, User

def enable_ad_traffic_permission(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User {email} not found")
            return
        
        # Update permissions
        if not user.permissions:
            user.permissions = {}
        
        user.permissions['ad-traffic'] = True
        db.commit()
        
        print(f"✅ Successfully enabled ad-traffic permission for {email}")
        print(f"Current permissions: {user.permissions}")
        
    finally:
        db.close()

if __name__ == "__main__":
    enable_ad_traffic_permission("danny@nbrain.ai") 