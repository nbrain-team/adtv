#!/usr/bin/env python3
"""
Script to diagnose and fix login issues for danny@nbrain.ai
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from core.database import SessionLocal, User
from core.auth import verify_password, get_password_hash

def fix_danny_login():
    """Debug and fix user login for danny@nbrain.ai"""
    
    with SessionLocal() as db:
        # Check if user exists
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        
        if not user:
            print("❌ User danny@nbrain.ai does not exist in the database")
            
            # List all users
            all_users = db.query(User).all()
            print("\nAll users in database:")
            for u in all_users:
                print(f"  - {u.email} (role: {u.role}, active: {u.is_active})")
            
            # Create the user if needed
            print("\nCreating user danny@nbrain.ai...")
            try:
                new_user = User(
                    email="danny@nbrain.ai",
                    hashed_password=get_password_hash("Tm0bile#88"),
                    role="admin",
                    is_active=True,
                    permissions={
                        "chat": True,
                        "history": True,
                        "knowledge": True,
                        "agents": True,
                        "data-lake": True,
                        "ad-traffic": True,
                        "campaigns": True
                    }
                )
                db.add(new_user)
                db.commit()
                print("✓ User created successfully")
            except Exception as e:
                print(f"❌ Failed to create user: {e}")
            return
        
        print(f"✓ Found user: {user.email}")
        print(f"  - ID: {user.id}")
        print(f"  - Role: {user.role}")
        print(f"  - Active: {user.is_active}")
        print(f"  - Permissions: {user.permissions}")
        print(f"  - Created: {user.created_at}")
        print(f"  - Last login: {user.last_login}")
        
        # Test password
        test_password = "Tm0bile#88"
        
        print(f"\nTesting password verification...")
        try:
            is_valid = verify_password(test_password, user.hashed_password)
            if is_valid:
                print("✓ Password verification successful")
            else:
                print("❌ Password verification failed")
                
                # Update the password
                print("\nUpdating password...")
                new_hash = get_password_hash(test_password)
                user.hashed_password = new_hash
                db.commit()
                print("✓ Password updated successfully")
                
        except Exception as e:
            print(f"❌ Error during password verification: {e}")
            
            # Force update password
            print("\nForce updating password...")
            try:
                new_hash = get_password_hash(test_password)
                user.hashed_password = new_hash
                db.commit()
                print("✓ Password force updated successfully")
            except Exception as e2:
                print(f"❌ Failed to update password: {e2}")
        
        # Ensure admin role and permissions
        if user.role != "admin":
            print(f"\n⚠️  User role is '{user.role}', updating to 'admin'...")
            user.role = "admin"
            db.commit()
            print("✓ Role updated to admin")
        
        # Ensure all permissions
        expected_permissions = {
            "chat": True,
            "history": True,
            "knowledge": True,
            "agents": True,
            "data-lake": True,
            "ad-traffic": True,
            "campaigns": True
        }
        
        if user.permissions != expected_permissions:
            print(f"\n⚠️  Permissions need updating...")
            user.permissions = expected_permissions
            db.commit()
            print("✓ Permissions updated")
        
        # Ensure user is active
        if not user.is_active:
            print(f"\n⚠️  User is not active, activating...")
            user.is_active = True
            db.commit()
            print("✓ User activated")

if __name__ == "__main__":
    fix_danny_login() 