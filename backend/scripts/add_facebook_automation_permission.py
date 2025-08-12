"""
Script to add facebook-automation permission to existing admin users
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import SessionLocal, User
import json


def add_facebook_automation_permission():
    """Add facebook-automation permission to admin users"""
    db = SessionLocal()
    
    try:
        # Update danny@nbrain.ai and danny@nbrain.com
        admin_emails = ["danny@nbrain.ai", "danny@nbrain.com"]
        
        for email in admin_emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                permissions = user.permissions.copy() if user.permissions else {}
                permissions['facebook-automation'] = True
                user.permissions = permissions
                print(f"Updated permissions for {email}: {permissions}")
        
        # Also update any other admin users
        admin_users = db.query(User).filter(User.role == "admin").all()
        for user in admin_users:
            permissions = user.permissions.copy() if user.permissions else {}
            permissions['facebook-automation'] = True
            user.permissions = permissions
            print(f"Updated permissions for {user.email}: {permissions}")
        
        db.commit()
        print("Successfully added facebook-automation permission to all admin users")
        
    except Exception as e:
        print(f"Error updating permissions: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_facebook_automation_permission() 