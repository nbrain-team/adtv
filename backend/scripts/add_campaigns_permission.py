#!/usr/bin/env python3
"""
Script to add campaigns permission to all users
Admins get it enabled by default, regular users get it disabled
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import engine, User
import json

def add_campaigns_permission():
    """Add campaigns permission to all users"""
    db = Session(bind=engine)
    
    try:
        # Get all users
        users = db.query(User).all()
        
        for user in users:
            # Parse existing permissions
            permissions = user.permissions or {}
            
            # Add campaigns permission if not present
            if 'campaigns' not in permissions:
                # Admins get campaigns enabled by default
                permissions['campaigns'] = (user.role == 'admin')
                
                # Update user permissions
                user.permissions = permissions
                print(f"Updated {user.email}: campaigns = {permissions['campaigns']} (role: {user.role})")
        
        # Commit changes
        db.commit()
        print(f"\nSuccessfully updated {len(users)} users")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding campaigns permission to all users...")
    add_campaigns_permission() 