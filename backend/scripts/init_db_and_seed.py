"""
Initialize database and seed with test data
"""

import os
import sys

# Set up a local SQLite database if DATABASE_URL is not set
if not os.getenv("DATABASE_URL"):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "local_test.db"))
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    print(f"Using local SQLite database: {db_path}")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import uuid
from core.database import SessionLocal, User, engine, Base
from passlib.context import CryptContext

# Import Facebook models to ensure relationships are loaded
import facebook_automation.models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """Initialize database and create test user"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    db = SessionLocal()
    
    try:
        # Check if test user exists
        user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
        
        if not user:
            # Create test user
            user = User(
                id=str(uuid.uuid4()),
                email="danny@nbrain.ai",
                hashed_password=pwd_context.hash("password123"),
                is_active=True,
                role="admin",  # Using role field instead of is_admin
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
                first_name="Danny",
                last_name="Test",
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            print(f"Created test user: {user.email}")
        else:
            print(f"Test user already exists: {user.email}")
            
        return user.id
        
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    user_id = init_database()
    print(f"\nDatabase initialized. User ID: {user_id}")
    print("\nNow running Facebook automation seeding script...")
    
    # Import and run the seeding script
    from seed_facebook_mock_data import main
    main() 