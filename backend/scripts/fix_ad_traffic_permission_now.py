#!/usr/bin/env python3
"""Force fix ad-traffic permission for danny@nbrain.ai"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, User

def fix_permission():
    """Force ad-traffic permission to True"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        if user:
            print(f"Current permissions: {user.permissions}")
            
            # Force update
            permissions = user.permissions.copy() if user.permissions else {}
            permissions['ad-traffic'] = True
            
            # Directly update in database to ensure it sticks
            user.permissions = permissions
            db.commit()
            db.refresh(user)
            
            print(f"✅ Updated permissions: {user.permissions}")
            print(f"ad-traffic is now: {user.permissions.get('ad-traffic', False)}")
        else:
            print("❌ User danny@nbrain.ai not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_permission() 