#!/usr/bin/env python3
"""Force fix ad-traffic permission using direct SQL"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine
from sqlalchemy import text
import json

def force_fix():
    """Use direct SQL to fix the permission"""
    db = SessionLocal()
    
    try:
        # First, let's see what's actually in the database
        result = db.execute(text("SELECT id, email, permissions FROM users WHERE email = 'danny@nbrain.ai'"))
        user = result.fetchone()
        
        if user:
            print(f"Found user: {user.email}")
            print(f"User ID: {user.id}")
            print(f"Raw permissions from DB: {user.permissions}")
            
            # Parse existing permissions
            permissions = user.permissions if isinstance(user.permissions, dict) else {}
            
            # Add ad-traffic
            permissions['ad-traffic'] = True
            
            # Update using raw SQL to ensure it works
            db.execute(
                text("UPDATE users SET permissions = :permissions WHERE id = :user_id"),
                {"permissions": json.dumps(permissions), "user_id": user.id}
            )
            db.commit()
            
            # Verify the update
            result = db.execute(text("SELECT permissions FROM users WHERE id = :user_id"), {"user_id": user.id})
            updated = result.fetchone()
            print(f"✅ Updated permissions: {updated.permissions}")
            
            # Double-check ad-traffic specifically
            final_perms = json.loads(updated.permissions) if isinstance(updated.permissions, str) else updated.permissions
            print(f"ad-traffic permission is now: {final_perms.get('ad-traffic', 'NOT FOUND')}")
        else:
            print("❌ User danny@nbrain.ai not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_fix() 