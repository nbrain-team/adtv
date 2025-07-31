#!/usr/bin/env python3
"""
Check and ensure all campaign_contacts columns exist
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database import engine

def check_campaign_columns():
    """Check existing columns and add missing ones"""
    
    # Expected columns based on the model
    expected_columns = {
        'id': 'VARCHAR',
        'campaign_id': 'VARCHAR',
        'first_name': 'VARCHAR',
        'last_name': 'VARCHAR',
        'email': 'VARCHAR',
        'company': 'VARCHAR',
        'title': 'VARCHAR',
        'phone': 'VARCHAR',
        'neighborhood': 'VARCHAR',
        'state': 'VARCHAR',
        'enriched_company': 'VARCHAR',
        'enriched_title': 'VARCHAR',
        'enriched_phone': 'VARCHAR',
        'enriched_linkedin': 'VARCHAR',
        'enriched_website': 'VARCHAR',
        'enriched_industry': 'VARCHAR',
        'enriched_company_size': 'VARCHAR',
        'enriched_location': 'VARCHAR',
        'personalized_email': 'TEXT',
        'personalized_subject': 'VARCHAR',
        'enrichment_status': 'VARCHAR',
        'enrichment_error': 'TEXT',
        'email_status': 'VARCHAR',
        'email_sent_at': 'TIMESTAMP',
        'excluded': 'BOOLEAN',
        'manually_edited': 'BOOLEAN',
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP'
    }
    
    with engine.connect() as conn:
        # Get existing columns
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='campaign_contacts'
            ORDER BY ordinal_position
        """))
        
        existing_columns = {row[0]: row[1] for row in result}
        
        print("=== Current Campaign Contacts Columns ===")
        for col, dtype in existing_columns.items():
            print(f"  {col}: {dtype}")
        
        print("\n=== Missing Columns ===")
        missing_columns = []
        for col, dtype in expected_columns.items():
            if col not in existing_columns:
                missing_columns.append((col, dtype))
                print(f"  {col}: {dtype}")
        
        if not missing_columns:
            print("  None - all columns exist!")
            return
        
        print("\n=== Adding Missing Columns ===")
        for col, dtype in missing_columns:
            try:
                # Map Python types to PostgreSQL types
                pg_type = dtype
                if dtype == 'VARCHAR':
                    pg_type = 'VARCHAR'
                elif dtype == 'TEXT':
                    pg_type = 'TEXT'
                elif dtype == 'BOOLEAN':
                    pg_type = 'BOOLEAN DEFAULT FALSE'
                elif dtype == 'TIMESTAMP':
                    pg_type = 'TIMESTAMP'
                
                sql = f"ALTER TABLE campaign_contacts ADD COLUMN {col} {pg_type}"
                print(f"  Adding {col}...")
                conn.execute(text(sql))
                conn.commit()
                print(f"  ✓ Added {col}")
            except Exception as e:
                print(f"  ✗ Error adding {col}: {e}")
        
        print("\n=== Final Column Check ===")
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name='campaign_contacts'
        """))
        count = result.scalar()
        print(f"  Total columns: {count}")

if __name__ == "__main__":
    check_campaign_columns() 