#!/usr/bin/env python3
"""
Add agreement fields to campaign_contacts table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_agreement_fields():
    """Add agreement tracking fields to campaign_contacts table"""
    
    queries = [
        """
        ALTER TABLE campaign_contacts 
        ADD COLUMN IF NOT EXISTS agreement_status VARCHAR(50);
        """,
        """
        ALTER TABLE campaign_contacts 
        ADD COLUMN IF NOT EXISTS agreement_sent_at TIMESTAMP;
        """,
        """
        ALTER TABLE campaign_contacts 
        ADD COLUMN IF NOT EXISTS agreement_signed_at TIMESTAMP;
        """,
        """
        ALTER TABLE campaign_contacts 
        ADD COLUMN IF NOT EXISTS agreement_data TEXT;
        """
    ]
    
    with engine.begin() as conn:
        for query in queries:
            try:
                conn.execute(text(query))
                logger.info(f"Successfully executed: {query[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"Column already exists, skipping...")
                else:
                    logger.error(f"Error executing query: {e}")
                    raise
    
    logger.info("Successfully added agreement fields to campaign_contacts table")

if __name__ == "__main__":
    add_agreement_fields() 