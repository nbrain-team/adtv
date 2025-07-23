#!/usr/bin/env python3
"""
Add error_message field to enrichment_projects table
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_error_field():
    """Add error_message field to enrichment_projects table"""
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'enrichment_projects' 
                AND column_name = 'error_message'
            """))
            
            if not result.fetchone():
                logger.info("Adding error_message column to enrichment_projects table...")
                conn.execute(text("""
                    ALTER TABLE enrichment_projects 
                    ADD COLUMN error_message TEXT
                """))
                logger.info("✅ error_message column added successfully!")
            else:
                logger.info("error_message column already exists, skipping...")
            
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Error adding error_message column: {e}")
            raise


if __name__ == "__main__":
    add_error_field() 