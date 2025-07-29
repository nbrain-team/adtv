#!/usr/bin/env python3
"""
Fix foreign key constraint for campaign_contacts table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database import engine

def fix_campaign_foreign_key():
    """Fix the foreign key constraint for campaign_contacts table"""
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if campaign_contacts table exists
            if 'campaign_contacts' not in inspector.get_table_names():
                print("❌ campaign_contacts table does not exist")
                return
            
            # Get current foreign keys
            foreign_keys = inspector.get_foreign_keys('campaign_contacts')
            print(f"Current foreign keys: {foreign_keys}")
            
            # Drop the incorrect foreign key constraint if it exists
            for fk in foreign_keys:
                if fk['constrained_columns'] == ['campaign_id']:
                    constraint_name = fk['name']
                    print(f"Dropping incorrect foreign key constraint: {constraint_name}")
                    conn.execute(text(f"""
                        ALTER TABLE campaign_contacts 
                        DROP CONSTRAINT IF EXISTS {constraint_name}
                    """))
                    conn.commit()
            
            # Add the correct foreign key constraint
            print("Adding correct foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE campaign_contacts
                ADD CONSTRAINT campaign_contacts_campaign_id_fkey 
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            """))
            conn.commit()
            
            print("✅ Fixed foreign key constraint for campaign_contacts table")
            
    except Exception as e:
        print(f"❌ Error fixing foreign key constraint: {e}")
        raise

if __name__ == "__main__":
    fix_campaign_foreign_key() 