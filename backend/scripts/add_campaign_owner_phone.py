#!/usr/bin/env python3
"""
Add owner_phone field to campaigns table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_owner_phone_field():
    """Add owner_phone field to campaigns table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add owner_phone column
            logger.info("Adding owner_phone column to campaigns table...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN IF NOT EXISTS owner_phone VARCHAR
            """))
            conn.commit()
            
            logger.info("Successfully added owner_phone column to campaigns table")
            
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            raise

if __name__ == "__main__":
    add_owner_phone_field()
    print("✅ Migration completed successfully!") 