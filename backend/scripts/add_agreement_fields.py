#!/usr/bin/env python3
"""
Add agreement fields to campaign_contacts table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_agreement_fields():
    """Add agreement tracking fields to campaign_contacts table"""
    
    try:
        # Check if table exists first
        inspector = inspect(engine)
        if 'campaign_contacts' not in inspector.get_table_names():
            logger.warning("campaign_contacts table does not exist yet, skipping agreement fields...")
            return
        
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('campaign_contacts')]
        logger.info(f"Existing columns in campaign_contacts: {existing_columns}")
        
        fields_to_add = [
            ('agreement_status', 'VARCHAR(50)'),
            ('agreement_sent_at', 'TIMESTAMP'),
            ('agreement_signed_at', 'TIMESTAMP'),
            ('agreement_data', 'TEXT')
        ]
        
        added_fields = []
        
        with engine.begin() as conn:
            for field_name, field_type in fields_to_add:
                if field_name not in existing_columns:
                    try:
                        query = f"""
                        ALTER TABLE campaign_contacts 
                        ADD COLUMN {field_name} {field_type};
                        """
                        conn.execute(text(query))
                        added_fields.append(field_name)
                        logger.info(f"Successfully added column: {field_name}")
                    except Exception as e:
                        logger.error(f"Error adding column {field_name}: {e}")
                else:
                    logger.info(f"Column {field_name} already exists, skipping...")
        
        if added_fields:
            logger.info(f"Successfully added agreement fields: {', '.join(added_fields)}")
        else:
            logger.info("All agreement fields already exist")
            
    except Exception as e:
        logger.error(f"Error in add_agreement_fields: {e}")
        # Don't raise - allow the app to continue starting up

if __name__ == "__main__":
    add_agreement_fields() 