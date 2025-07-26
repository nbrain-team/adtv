#!/usr/bin/env python3
"""
Fix CRM opportunities table - remove lead_status references
The database has deal_status but the code is looking for lead_status
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_crm_table():
    """Check if lead_status exists and handle appropriately"""
    with engine.connect() as conn:
        try:
            # First, check current column names
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'crm_opportunities'
                AND column_name IN ('lead_status', 'deal_status')
                ORDER BY column_name;
            """))
            
            columns = [row[0] for row in result]
            logger.info(f"Found columns: {columns}")
            
            if 'lead_status' in columns and 'deal_status' not in columns:
                # Rename lead_status to deal_status
                logger.info("Renaming lead_status to deal_status...")
                conn.execute(text("""
                    ALTER TABLE crm_opportunities 
                    RENAME COLUMN lead_status TO deal_status;
                """))
                conn.commit()
                logger.info("Column renamed successfully")
                
            elif 'lead_status' in columns and 'deal_status' in columns:
                # Both exist - drop lead_status
                logger.info("Both columns exist, dropping lead_status...")
                conn.execute(text("""
                    ALTER TABLE crm_opportunities 
                    DROP COLUMN lead_status;
                """))
                conn.commit()
                logger.info("Duplicate column removed")
                
            elif 'deal_status' in columns and 'lead_status' not in columns:
                logger.info("Table already has correct schema (deal_status only)")
                
            else:
                logger.warning("Neither lead_status nor deal_status found - table might not exist")
                
        except Exception as e:
            logger.error(f"Error checking/fixing table: {str(e)}")
            raise

if __name__ == "__main__":
    logger.info("Starting CRM table fix...")
    check_and_fix_crm_table()
    logger.info("CRM table fix completed!") 