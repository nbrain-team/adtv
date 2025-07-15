#!/usr/bin/env python3
"""
Script to update a specific user's campaigns permission
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import engine, User
import json

def update_user_campaigns_permission(email):
    """Update campaigns permission for a specific user"""
    db = Session(bind=engine)
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"User with email '{email}' not found")
            return
        
        # Parse existing permissions
        permissions = user.permissions or {}
        
        # Add campaigns permission
        permissions['campaigns'] = True
        
        # Update user permissions
        user.permissions = permissions
        
        # If user is admin, ensure they have admin role
        if user.role != 'admin':
            print(f"Note: User {email} has role '{user.role}'. Do you want to make them admin? (y/n): ", end='')
            if input().lower() == 'y':
                user.role = 'admin'
        
        # Commit changes
        db.commit()
        print(f"Successfully updated {user.email}:")
        print(f"  - Role: {user.role}")
        print(f"  - Campaigns permission: {permissions['campaigns']}")
        print(f"  - All permissions: {permissions}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_user_campaigns_permission.py <user_email>")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"Updating campaigns permission for user: {email}")
    update_user_campaigns_permission(email) 