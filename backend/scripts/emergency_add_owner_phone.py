#!/usr/bin/env python3
"""
Emergency script to add owner_phone field to campaigns table
This can be run manually if the build script hasn't executed yet
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_owner_phone_field():
    """Add owner_phone field to campaigns table"""
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False
        
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='campaigns' AND column_name='owner_phone'
            """))
            
            if result.fetchone():
                logger.info("owner_phone column already exists")
                return True
            
            # Add owner_phone column
            logger.info("Adding owner_phone column to campaigns table...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN owner_phone VARCHAR
            """))
            conn.commit()
            
            logger.info("Successfully added owner_phone column to campaigns table")
            return True
            
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            return False

if __name__ == "__main__":
    success = add_owner_phone_field()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1) 