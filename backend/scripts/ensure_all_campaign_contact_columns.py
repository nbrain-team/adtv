#!/usr/bin/env python3
"""
Ensure all required columns exist in the campaign_contacts table
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL environment variable not set")
    sys.exit(1)

def ensure_all_columns():
    """Ensure all required columns exist in campaign_contacts table"""
    engine = create_engine(DATABASE_URL)
    
    # Define all expected columns with their types
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
        'geocoded_address': 'VARCHAR',
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
        'excluded': 'BOOLEAN DEFAULT FALSE',
        'manually_edited': 'BOOLEAN DEFAULT FALSE',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
    
    with engine.connect() as conn:
        # Get existing columns
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('campaign_contacts')]
        
        print("=== Checking Campaign Contacts Columns ===")
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        missing_columns = []
        for col_name, col_type in expected_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
                
        if missing_columns:
            print(f"\nMissing columns found: {[col[0] for col in missing_columns]}")
            
            for col_name, col_type in missing_columns:
                try:
                    print(f"Adding column: {col_name} {col_type}")
                    conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✓ Added column: {col_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"Column {col_name} already exists")
                    else:
                        print(f"Error adding column {col_name}: {e}")
        else:
            print("\n✓ All columns exist!")
            
        # Verify final state
        inspector = inspect(engine)
        final_columns = [col['name'] for col in inspector.get_columns('campaign_contacts')]
        print(f"\nFinal columns ({len(final_columns)}): {sorted(final_columns)}")

if __name__ == "__main__":
    ensure_all_columns() 