#!/usr/bin/env python3
"""
Add email and phone capture rate fields to campaign_analytics table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_analytics_fields():
    """Add new fields to campaign_analytics table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add new columns
            logger.info("Adding new columns to campaign_analytics table...")
            
            # Add contact count fields
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS contacts_with_email INTEGER DEFAULT 0
            """))
            conn.commit()
            
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS contacts_with_phone INTEGER DEFAULT 0
            """))
            conn.commit()
            
            # Add capture rate fields
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS email_capture_rate FLOAT DEFAULT 0.0
            """))
            conn.commit()
            
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS phone_capture_rate FLOAT DEFAULT 0.0
            """))
            conn.commit()
            
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS email_generation_rate FLOAT DEFAULT 0.0
            """))
            conn.commit()
            
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS email_send_rate FLOAT DEFAULT 0.0
            """))
            conn.commit()
            
            # Add missing timestamp fields if they don't exist
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS send_start_time TIMESTAMP
            """))
            conn.commit()
            
            conn.execute(text("""
                ALTER TABLE campaign_analytics 
                ADD COLUMN IF NOT EXISTS send_end_time TIMESTAMP
            """))
            conn.commit()
            
            logger.info("Successfully added new columns to campaign_analytics table")
            
        except Exception as e:
            logger.error(f"Error adding columns: {e}")
            raise

if __name__ == "__main__":
    add_analytics_fields()
    print("✅ Migration completed successfully!") 