#!/usr/bin/env python3
"""
Fix empty email fields in ad_traffic_clients table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_ad_traffic_emails():
    """Fix empty email fields that are causing validation errors"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Update empty strings to NULL
            logger.info("Fixing empty email fields in ad_traffic_clients...")
            
            result = conn.execute(text("""
                UPDATE ad_traffic_clients 
                SET email = NULL 
                WHERE email = '' OR email IS NOT NULL AND LENGTH(TRIM(email)) = 0
            """))
            conn.commit()
            
            rows_updated = result.rowcount
            logger.info(f"✅ Updated {rows_updated} empty email fields to NULL")
            
            # Show current status
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(email) as with_email,
                    COUNT(CASE WHEN email IS NULL THEN 1 END) as null_email
                FROM ad_traffic_clients
            """))
            
            row = result.fetchone()
            if row:
                logger.info(f"\nCurrent status:")
                logger.info(f"  Total clients: {row.total}")
                logger.info(f"  With valid email: {row.with_email}")
                logger.info(f"  With NULL email: {row.null_email}")
            
        except Exception as e:
            logger.error(f"Error fixing emails: {e}")
            raise

if __name__ == "__main__":
    fix_ad_traffic_emails()
    print("\n✅ Email fix completed!") 