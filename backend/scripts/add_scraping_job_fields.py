#!/usr/bin/env python3
"""
Migration script to add updated_at and error_message fields to scraping_jobs table
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_scraping_job_fields():
    """Add updated_at and error_message columns to scraping_jobs table"""
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if updated_at column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='scraping_jobs' AND column_name='updated_at'
            """))
            
            if not result.fetchone():
                logger.info("Adding updated_at column to scraping_jobs table...")
                conn.execute(text("""
                    ALTER TABLE scraping_jobs 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                """))
                logger.info("✓ Added updated_at column")
            else:
                logger.info("updated_at column already exists")
            
            # Check if error_message column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='scraping_jobs' AND column_name='error_message'
            """))
            
            if not result.fetchone():
                logger.info("Adding error_message column to scraping_jobs table...")
                conn.execute(text("""
                    ALTER TABLE scraping_jobs 
                    ADD COLUMN error_message TEXT
                """))
                logger.info("✓ Added error_message column")
            else:
                logger.info("error_message column already exists")
            
            # Update existing rows to set updated_at = created_at where it's null
            conn.execute(text("""
                UPDATE scraping_jobs 
                SET updated_at = created_at 
                WHERE updated_at IS NULL
            """))
            
            trans.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    add_scraping_job_fields() 