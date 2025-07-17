"""
Debug script to check user login issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from core.database import SessionLocal, User
from core.auth import verify_password, get_password_hash

def debug_user_login():
    """Debug user login for danny@nbrain.com"""
    
    with SessionLocal() as db:
        # Check if user exists
        user = db.query(User).filter(User.email == "danny@nbrain.com").first()
        
        if not user:
            print("❌ User danny@nbrain.com does not exist in the database")
            
            # List all users
            all_users = db.query(User).all()
            print("\nAll users in database:")
            for u in all_users:
                print(f"  - {u.email} (role: {u.role}, active: {u.is_active})")
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
                
                # Try to update the password
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

if __name__ == "__main__":
    debug_user_login() 