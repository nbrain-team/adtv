#!/usr/bin/env python3
"""
Script to find and fix admin user permissions
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import create_engine, Column, String, Boolean, JSON, DateTime, func

# Define User model directly to avoid import issues
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    role = Column(String, default="user")
    permissions = Column(JSON, default=lambda: {"chat": True})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

def find_and_fix_admin(db_url, email="danny@nbrain.ai"):
    """Find user and ensure they have admin role and campaigns permission"""
    print(f"\nChecking database...")
    
    try:
        engine = create_engine(db_url)
        db = Session(bind=engine)
        
        # Get all users
        users = db.query(User).all()
        print(f"Total users found: {len(users)}")
        
        for user in users:
            print(f"  - {user.email} (role: {user.role})")
        
        # Find specific user
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"\nFound user: {user.email}")
            print(f"Current role: {user.role}")
            print(f"Current permissions: {user.permissions}")
            
            # Update to admin with campaigns
            user.role = "admin"
            permissions = user.permissions or {}
            permissions["campaigns"] = True
            user.permissions = permissions
            
            db.commit()
            print(f"\nUpdated successfully!")
            print(f"New role: {user.role}")
            print(f"New permissions: {user.permissions}")
        else:
            print(f"\nUser {email} not found in this database")
        
        db.close()
        return user is not None
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Try external URL
    external_url = "postgresql://adtv_db_user:fTu3uQdUG3DLy3qAKRBGffwMioIk8IfG@dpg-d1a7efh5pdvs73ai9a9g-a.oregon-postgres.render.com/adtv_db"
    
    # Try internal URL (without .render.com)
    internal_url = "postgresql://adtv_db_user:fTu3uQdUG3DLy3qAKRBGffwMioIk8IfG@dpg-d1a7efh5pdvs73ai9a9g-a/adtv_db"
    
    print("Trying external database URL...")
    if not find_and_fix_admin(external_url):
        print("\nTrying internal database URL...")
        find_and_fix_admin(internal_url) 