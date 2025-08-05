#!/usr/bin/env python3
"""
Add RSVP tracking fields to campaign_contacts and create campaign_email_templates table
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add RSVP fields to campaign_contacts
            logger.info("Adding RSVP fields to campaign_contacts table...")
            
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'campaign_contacts' 
                AND column_name IN ('is_rsvp', 'rsvp_status', 'rsvp_date')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'is_rsvp' not in existing_columns:
                conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN is_rsvp BOOLEAN DEFAULT FALSE"))
                logger.info("Added is_rsvp column")
            
            if 'rsvp_status' not in existing_columns:
                conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN rsvp_status VARCHAR"))
                logger.info("Added rsvp_status column")
            
            if 'rsvp_date' not in existing_columns:
                conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN rsvp_date TIMESTAMP"))
                logger.info("Added rsvp_date column")
            
            # Create campaign_email_templates table
            logger.info("Creating campaign_email_templates table...")
            
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'campaign_email_templates'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                conn.execute(text("""
                    CREATE TABLE campaign_email_templates (
                        id VARCHAR PRIMARY KEY,
                        campaign_id VARCHAR REFERENCES campaigns(id) ON DELETE CASCADE,
                        name VARCHAR NOT NULL,
                        subject VARCHAR NOT NULL,
                        body TEXT NOT NULL,
                        template_type VARCHAR DEFAULT 'general',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                logger.info("Created campaign_email_templates table")
                
                # Create index on campaign_id
                conn.execute(text("""
                    CREATE INDEX idx_campaign_email_templates_campaign_id 
                    ON campaign_email_templates(campaign_id)
                """))
                logger.info("Created index on campaign_id")
            
            conn.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration() 