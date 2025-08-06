#!/usr/bin/env python3
"""
Add mail merge fields to campaigns table
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_campaign_mail_merge_fields():
    """Add new mail merge fields to campaigns table"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Local development
        DATABASE_URL = "postgresql://adtv_user:SecureP@ss2024!@localhost/adtv_db"
    
    engine = create_engine(DATABASE_URL)
    
    # Fields to add
    fields_to_add = [
        ("owner_phone", "VARCHAR(50)"),
        ("video_link", "VARCHAR(500)"),
        ("event_link", "VARCHAR(500)"),
    ]
    
    with engine.connect() as conn:
        # Check which columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'campaigns' AND table_schema = 'public'
        """))
        existing_columns = {row[0] for row in result}
        
        # Add missing columns
        for field_name, field_type in fields_to_add:
            if field_name not in existing_columns:
                try:
                    logger.info(f"Adding column {field_name} to campaigns table...")
                    conn.execute(text(f"ALTER TABLE campaigns ADD COLUMN {field_name} {field_type}"))
                    conn.commit()
                    logger.info(f"Successfully added {field_name} column")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.error(f"Error adding {field_name}: {e}")
                        raise
                    else:
                        logger.info(f"Column {field_name} already exists")
            else:
                logger.info(f"Column {field_name} already exists, skipping")
        
        logger.info("All mail merge fields have been added successfully")

if __name__ == "__main__":
    add_campaign_mail_merge_fields()
    logger.info("Migration completed successfully") 