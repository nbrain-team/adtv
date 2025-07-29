#!/usr/bin/env python3
"""
Add event_times and target_cities fields to campaigns table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database import engine

def add_campaign_fields():
    """Add event_times and target_cities fields to campaigns table"""
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if campaigns table exists
            if 'campaigns' not in inspector.get_table_names():
                print("❌ campaigns table does not exist")
                return
            
            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('campaigns')]
            
            # Add event_times column if it doesn't exist
            if 'event_times' not in existing_columns:
                print("Adding event_times column...")
                conn.execute(text("""
                    ALTER TABLE campaigns 
                    ADD COLUMN event_times JSON DEFAULT '[]'::json
                """))
                conn.commit()
                print("✅ Added event_times column")
            else:
                print("ℹ️  event_times column already exists")
            
            # Add target_cities column if it doesn't exist
            if 'target_cities' not in existing_columns:
                print("Adding target_cities column...")
                conn.execute(text("""
                    ALTER TABLE campaigns 
                    ADD COLUMN target_cities TEXT
                """))
                conn.commit()
                print("✅ Added target_cities column")
            else:
                print("ℹ️  target_cities column already exists")
                
    except Exception as e:
        print(f"❌ Error adding campaign fields: {e}")
        raise

if __name__ == "__main__":
    add_campaign_fields() 