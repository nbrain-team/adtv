#!/usr/bin/env python3
"""
Ensure agreements table exists - run this on startup
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
import logging

logger = logging.getLogger(__name__)

def ensure_agreements_table():
    """Ensure the agreements table exists in the database"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment")
        return False
    
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Check if agreements table exists
        if 'agreements' not in inspector.get_table_names():
            logger.info("agreements table does not exist, creating it...")
            
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS agreements (
                        id VARCHAR PRIMARY KEY,
                        campaign_id VARCHAR NOT NULL,
                        contact_id VARCHAR NOT NULL,
                        contact_name VARCHAR NOT NULL,
                        contact_email VARCHAR NOT NULL,
                        company VARCHAR,
                        start_date VARCHAR NOT NULL,
                        setup_fee FLOAT NOT NULL,
                        monthly_fee FLOAT NOT NULL,
                        campaign_name VARCHAR NOT NULL,
                        status VARCHAR DEFAULT 'pending',
                        signature TEXT,
                        signature_type VARCHAR,
                        signed_date VARCHAR,
                        signed_at TIMESTAMP,
                        viewed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        pdf_data TEXT,
                        agreement_url VARCHAR
                    )
                """))
                logger.info("agreements table created successfully")
        else:
            logger.info("agreements table already exists")
        
        # Also ensure campaign_contacts has agreement fields
        if 'campaign_contacts' in inspector.get_table_names():
            columns = {col['name'] for col in inspector.get_columns('campaign_contacts')}
            agreement_fields = [
                ('agreement_status', 'VARCHAR(50)'),
                ('agreement_sent_at', 'TIMESTAMP'),
                ('agreement_signed_at', 'TIMESTAMP'),
                ('agreement_data', 'TEXT')
            ]
            
            for field_name, field_type in agreement_fields:
                if field_name not in columns:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field_name} {field_type}"))
                            logger.info(f"Added {field_name} to campaign_contacts")
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            logger.error(f"Error adding {field_name}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring agreements table: {e}")
        return False

if __name__ == "__main__":
    if ensure_agreements_table():
        print("✅ Agreements table ready")
        exit(0)
    else:
        print("❌ Failed to ensure agreements table")
        exit(1) 