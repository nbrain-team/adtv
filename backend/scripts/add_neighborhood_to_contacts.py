#!/usr/bin/env python3
"""
Add neighborhood field to campaign_contacts table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database import engine

def add_neighborhood_field():
    """Add neighborhood field to campaign_contacts table"""
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if campaign_contacts table exists
            if 'campaign_contacts' not in inspector.get_table_names():
                print("❌ campaign_contacts table does not exist")
                return
            
            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('campaign_contacts')]
            
            # Add neighborhood column if it doesn't exist
            if 'neighborhood' not in existing_columns:
                print("Adding neighborhood column...")
                conn.execute(text("""
                    ALTER TABLE campaign_contacts
                    ADD COLUMN neighborhood VARCHAR
                """))
                conn.commit()
                print("✅ Added neighborhood column")
            else:
                print("ℹ️  neighborhood column already exists")
                
    except Exception as e:
        print(f"❌ Error adding neighborhood field: {e}")
        raise

if __name__ == "__main__":
    add_neighborhood_field() 