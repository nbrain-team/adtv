#!/usr/bin/env python3
"""
Update ad traffic enums to include new values
"""
import os
import sys
from sqlalchemy import create_engine, text
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_ad_traffic_enums():
    """Update ad traffic enums to include new values"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return
    
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        try:
            # Start a transaction
            trans = conn.begin()
            
            # Check if poststatus enum exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'poststatus'
                );
            """))
            
            if not result.scalar():
                logger.info("poststatus enum doesn't exist, skipping update")
                trans.rollback()
                return
            
            # Get current enum values
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'poststatus')
                ORDER BY enumsortorder;
            """))
            
            current_values = [row[0] for row in result]
            logger.info(f"Current poststatus enum values: {current_values}")
            
            # Values we need
            required_values = ['draft', 'scheduled', 'pending_approval', 'approved', 'published', 'failed']
            values_to_add = [v for v in required_values if v not in current_values]
            
            if not values_to_add:
                logger.info("All required values already exist in poststatus enum")
                trans.commit()
                return
            
            # Add new values one by one
            for value in values_to_add:
                try:
                    logger.info(f"Adding '{value}' to poststatus enum...")
                    # Use a separate transaction for each ALTER TYPE
                    conn.execute(text("COMMIT"))
                    conn.execute(text(f"ALTER TYPE poststatus ADD VALUE IF NOT EXISTS '{value}'"))
                    logger.info(f"Successfully added '{value}'")
                except Exception as e:
                    # This might fail if the value already exists, which is fine
                    logger.warning(f"Could not add '{value}': {e}")
            
            logger.info("Enum update completed")
            
        except Exception as e:
            logger.error(f"Error updating ad traffic enums: {e}")
            # Don't raise, just log - we don't want to break startup

if __name__ == "__main__":
    update_ad_traffic_enums() 