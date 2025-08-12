"""
Initialize production database - creates admin user only
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import uuid
from core.database import SessionLocal, User, engine, Base
from passlib.context import CryptContext
import facebook_automation.models  # Ensure all models are loaded

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_production_database():
    """Initialize production database with admin user only"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_email = os.getenv("ADMIN_EMAIL", "danny@nbrain.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")
        
        user = db.query(User).filter(User.email == admin_email).first()
        
        if not user:
            # Create admin user
            user = User(
                id=str(uuid.uuid4()),
                email=admin_email,
                hashed_password=pwd_context.hash(admin_password),
                is_active=True,
                role="admin",
                permissions={
                    "facebook-automation": True,
                    "ad-traffic": True,
                    "data-lake": True,
                    "contact-enricher": True,
                    "realtor-importer": True,
                    "user-roles-admin": True,
                    "chat": True,
                    "campaigns": True
                },
                first_name="Admin",
                last_name="User",
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            print(f"Created admin user: {user.email}")
            print("⚠️  IMPORTANT: Change the default password immediately!")
        else:
            print(f"Admin user already exists: {user.email}")
            
        return user.id
        
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing production database...")
    user_id = init_production_database()
    print(f"\n✅ Production database initialized. Admin user ID: {user_id}")
    print("\nNOTE: No mock data was added. The platform will start empty.")
    print("Users can connect their real Facebook accounts to begin using the platform.") 