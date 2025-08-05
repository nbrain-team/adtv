#!/usr/bin/env python3
"""
Update the poststatus enum to include new values: PENDING_APPROVAL and APPROVED
"""
import os
import sys
from sqlalchemy import create_engine, text
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_poststatus_enum():
    """Update the poststatus enum to include new values"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return
    
    engine = create_engine(database_url)
    
    with engine.begin() as conn:
        try:
            # First, check current enum values
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'poststatus')
                ORDER BY enumsortorder;
            """))
            
            current_values = [row[0] for row in result]
            logger.info(f"Current poststatus enum values: {current_values}")
            
            # Check if we need to add new values
            values_to_add = []
            if 'pending_approval' not in current_values:
                values_to_add.append('pending_approval')
            if 'approved' not in current_values:
                values_to_add.append('approved')
                
            if not values_to_add:
                logger.info("All required values already exist in poststatus enum")
                return
                
            # Add new values to the enum
            for value in values_to_add:
                logger.info(f"Adding '{value}' to poststatus enum...")
                conn.execute(text(f"ALTER TYPE poststatus ADD VALUE '{value}'"))
                logger.info(f"Successfully added '{value}'")
            
            # Verify the update
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'poststatus')
                ORDER BY enumsortorder;
            """))
            
            updated_values = [row[0] for row in result]
            logger.info(f"Updated poststatus enum values: {updated_values}")
            
        except Exception as e:
            logger.error(f"Error updating poststatus enum: {e}")
            raise

if __name__ == "__main__":
    update_poststatus_enum() 