#!/usr/bin/env python3
"""
Ensure agreement fields exist in campaign_contacts table
Run this manually if agreement fields are missing:
    python backend/scripts/ensure_agreement_fields.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_agreement_fields():
    """Ensure agreement tracking fields exist in campaign_contacts table"""
    
    print("=" * 60)
    print("ENSURING AGREEMENT FIELDS IN DATABASE")
    print("=" * 60)
    
    try:
        # Check if table exists first
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'campaign_contacts' not in tables:
            print("❌ campaign_contacts table does not exist!")
            print("Please ensure the database is properly initialized first.")
            return False
        
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('campaign_contacts')]
        print(f"\n📋 Current columns in campaign_contacts:")
        print(f"   {', '.join(existing_columns)}")
        
        # Fields we need to add
        fields_to_add = [
            ('agreement_status', 'VARCHAR(50)'),
            ('agreement_sent_at', 'TIMESTAMP'),
            ('agreement_signed_at', 'TIMESTAMP'),
            ('agreement_data', 'TEXT')
        ]
        
        # Check which fields are missing
        missing_fields = [(name, type_) for name, type_ in fields_to_add if name not in existing_columns]
        
        if not missing_fields:
            print("\n✅ All agreement fields already exist!")
            return True
        
        print(f"\n⚠️  Missing fields: {', '.join([f[0] for f in missing_fields])}")
        print("\nAdding missing fields...")
        
        added_fields = []
        failed_fields = []
        
        with engine.begin() as conn:
            for field_name, field_type in missing_fields:
                try:
                    query = f"""
                    ALTER TABLE campaign_contacts 
                    ADD COLUMN {field_name} {field_type};
                    """
                    conn.execute(text(query))
                    added_fields.append(field_name)
                    print(f"   ✅ Added: {field_name}")
                except Exception as e:
                    failed_fields.append(field_name)
                    print(f"   ❌ Failed to add {field_name}: {e}")
        
        print("\n" + "=" * 60)
        if added_fields:
            print(f"✅ Successfully added fields: {', '.join(added_fields)}")
        if failed_fields:
            print(f"❌ Failed to add fields: {', '.join(failed_fields)}")
            return False
        
        print("=" * 60)
        return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = ensure_agreement_fields()
    sys.exit(0 if success else 1) 