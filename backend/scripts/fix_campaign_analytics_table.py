#!/usr/bin/env python3
"""
Fix campaign_analytics table to ensure all columns exist
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database import engine

def fix_campaign_analytics_table():
    """Ensure campaign_analytics table has all required columns"""
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if campaign_analytics table exists
            if 'campaign_analytics' not in inspector.get_table_names():
                print("Creating campaign_analytics table...")
                conn.execute(text("""
                    CREATE TABLE campaign_analytics (
                        id VARCHAR PRIMARY KEY,
                        campaign_id VARCHAR REFERENCES campaigns(id),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        contacts_uploaded INTEGER DEFAULT 0,
                        contacts_enriched INTEGER DEFAULT 0,
                        enrichment_success_rate FLOAT DEFAULT 0.0,
                        emails_generated INTEGER DEFAULT 0,
                        emails_sent INTEGER DEFAULT 0,
                        enrichment_start_time TIMESTAMP,
                        enrichment_end_time TIMESTAMP,
                        email_generation_start_time TIMESTAMP,
                        email_generation_end_time TIMESTAMP,
                        sending_start_time TIMESTAMP,
                        sending_end_time TIMESTAMP
                    )
                """))
                conn.commit()
                print("✅ Created campaign_analytics table")
            else:
                # Get existing columns
                existing_columns = [col['name'] for col in inspector.get_columns('campaign_analytics')]
                
                # Add missing columns
                columns_to_add = {
                    'timestamp': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'contacts_uploaded': 'INTEGER DEFAULT 0',
                    'contacts_enriched': 'INTEGER DEFAULT 0',
                    'enrichment_success_rate': 'FLOAT DEFAULT 0.0',
                    'emails_generated': 'INTEGER DEFAULT 0',
                    'emails_sent': 'INTEGER DEFAULT 0',
                    'enrichment_start_time': 'TIMESTAMP',
                    'enrichment_end_time': 'TIMESTAMP',
                    'email_generation_start_time': 'TIMESTAMP',
                    'email_generation_end_time': 'TIMESTAMP',
                    'sending_start_time': 'TIMESTAMP',
                    'sending_end_time': 'TIMESTAMP'
                }
                
                for col_name, col_type in columns_to_add.items():
                    if col_name not in existing_columns:
                        print(f"Adding {col_name} column...")
                        conn.execute(text(f"""
                            ALTER TABLE campaign_analytics
                            ADD COLUMN {col_name} {col_type}
                        """))
                        conn.commit()
                        print(f"✅ Added {col_name} column")
                    else:
                        print(f"ℹ️  {col_name} column already exists")
                        
    except Exception as e:
        print(f"❌ Error fixing campaign_analytics table: {e}")
        raise

if __name__ == "__main__":
    fix_campaign_analytics_table() 