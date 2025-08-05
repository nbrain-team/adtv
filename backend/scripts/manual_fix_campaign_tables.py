#!/usr/bin/env python3
"""
Manual script to fix campaign tables - run this separately after deployment
This avoids hanging during startup
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment")
    sys.exit(1)

# Create engine with specific pool settings for migrations
engine = create_engine(
    DATABASE_URL,
    pool_size=1,
    max_overflow=0,
    pool_pre_ping=True
)
Session = sessionmaker(bind=engine)

def fix_campaign_foreign_keys():
    """Fix foreign key constraints for campaign tables"""
    session = Session()
    try:
        logger.info("Fixing campaign foreign key constraints...")
        
        # Check if campaign_contacts exists
        inspector = inspect(engine)
        if 'campaign_contacts' not in inspector.get_table_names():
            logger.warning("campaign_contacts table does not exist")
            return
        
        # Get existing foreign keys
        foreign_keys = inspector.get_foreign_keys('campaign_contacts')
        logger.info(f"Current foreign keys: {foreign_keys}")
        
        # Drop incorrect constraints
        for fk in foreign_keys:
            if fk['constrained_columns'] == ['campaign_id']:
                constraint_name = fk['name']
                logger.info(f"Dropping constraint: {constraint_name}")
                session.execute(text(f"""
                    ALTER TABLE campaign_contacts 
                    DROP CONSTRAINT IF EXISTS {constraint_name}
                """))
        
        # Add correct constraint
        logger.info("Adding correct foreign key constraint...")
        session.execute(text("""
            ALTER TABLE campaign_contacts
            ADD CONSTRAINT campaign_contacts_campaign_id_fkey 
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
        """))
        
        session.commit()
        logger.info("✅ Fixed campaign foreign key constraints")
        
    except Exception as e:
        logger.error(f"Error fixing foreign keys: {e}")
        session.rollback()
    finally:
        session.close()

def add_analytics_columns():
    """Add missing columns to campaign_analytics table"""
    session = Session()
    try:
        logger.info("Adding missing columns to campaign_analytics...")
        
        # Check if table exists
        inspector = inspect(engine)
        if 'campaign_analytics' not in inspector.get_table_names():
            logger.info("Creating campaign_analytics table...")
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS campaign_analytics (
                    id VARCHAR PRIMARY KEY,
                    campaign_id VARCHAR REFERENCES campaigns(id) ON DELETE CASCADE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    enrichment_start_time TIMESTAMP,
                    enrichment_end_time TIMESTAMP,
                    email_generation_start_time TIMESTAMP,
                    email_generation_end_time TIMESTAMP,
                    sending_start_time TIMESTAMP,
                    sending_end_time TIMESTAMP,
                    contacts_uploaded INTEGER DEFAULT 0,
                    contacts_enriched INTEGER DEFAULT 0,
                    contacts_with_email INTEGER DEFAULT 0,
                    contacts_with_phone INTEGER DEFAULT 0,
                    emails_generated INTEGER DEFAULT 0,
                    emails_sent INTEGER DEFAULT 0,
                    enrichment_success_rate FLOAT DEFAULT 0.0,
                    email_capture_rate FLOAT DEFAULT 0.0,
                    phone_capture_rate FLOAT DEFAULT 0.0,
                    email_generation_rate FLOAT DEFAULT 0.0,
                    email_send_rate FLOAT DEFAULT 0.0
                )
            """))
            session.commit()
            logger.info("✅ Created campaign_analytics table")
        else:
            # Add missing columns if they don't exist
            columns_to_add = [
                ("contacts_with_email", "INTEGER DEFAULT 0"),
                ("contacts_with_phone", "INTEGER DEFAULT 0"),
                ("enrichment_success_rate", "FLOAT DEFAULT 0.0"),
                ("email_capture_rate", "FLOAT DEFAULT 0.0"),
                ("phone_capture_rate", "FLOAT DEFAULT 0.0"),
                ("email_generation_rate", "FLOAT DEFAULT 0.0"),
                ("email_send_rate", "FLOAT DEFAULT 0.0"),
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    session.execute(text(f"""
                        ALTER TABLE campaign_analytics 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    logger.info(f"✓ Added column: {column_name}")
                except Exception as e:
                    logger.debug(f"Column {column_name} might already exist: {e}")
            
            session.commit()
            logger.info("✅ Updated campaign_analytics columns")
            
    except Exception as e:
        logger.error(f"Error updating analytics table: {e}")
        session.rollback()
    finally:
        session.close()

def add_neighborhood_field():
    """Add neighborhood and state fields to campaign_contacts table"""
    session = Session()
    try:
        logger.info("Adding neighborhood and state fields to campaign_contacts...")
        
        # Check if table exists
        inspector = inspect(engine)
        if 'campaign_contacts' not in inspector.get_table_names():
            logger.warning("campaign_contacts table does not exist")
            return
        
        # Add neighborhood field if it doesn't exist
        try:
            session.execute(text("""
                ALTER TABLE campaign_contacts 
                ADD COLUMN IF NOT EXISTS neighborhood VARCHAR
            """))
            logger.info("✓ Added neighborhood column")
        except Exception as e:
            logger.debug(f"Neighborhood column might already exist: {e}")
        
        # Add state field if it doesn't exist
        try:
            session.execute(text("""
                ALTER TABLE campaign_contacts 
                ADD COLUMN IF NOT EXISTS state VARCHAR
            """))
            logger.info("✓ Added state column")
        except Exception as e:
            logger.debug(f"State column might already exist: {e}")
        
        # Add geocoded_address field if it doesn't exist
        try:
            session.execute(text("""
                ALTER TABLE campaign_contacts 
                ADD COLUMN IF NOT EXISTS geocoded_address VARCHAR
            """))
            logger.info("✓ Added geocoded_address column")
        except Exception as e:
            logger.debug(f"Geocoded_address column might already exist: {e}")
        
        session.commit()
        logger.info("✅ Updated campaign_contacts fields")
        
    except Exception as e:
        logger.error(f"Error adding neighborhood fields: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Run all manual migrations"""
    logger.info("=" * 60)
    logger.info("Running manual campaign table fixes...")
    logger.info("=" * 60)
    
    # Fix foreign keys
    fix_campaign_foreign_keys()
    
    # Add analytics columns
    add_analytics_columns()
    
    # Add neighborhood fields
    add_neighborhood_field()
    
    logger.info("=" * 60)
    logger.info("Manual migrations completed!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 