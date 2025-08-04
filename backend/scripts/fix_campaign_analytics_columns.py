#!/usr/bin/env python3
"""
Fix campaign_analytics table by adding missing columns
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL environment variable not set")
    sys.exit(1)

def fix_campaign_analytics():
    """Add missing columns to campaign_analytics table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("=== Fixing Campaign Analytics Table ===")
        
        # List of columns to add with their types
        columns_to_add = [
            ('contacts_with_email', 'INTEGER DEFAULT 0'),
            ('contacts_with_phone', 'INTEGER DEFAULT 0'),
            ('enrichment_success_rate', 'FLOAT DEFAULT 0'),
            ('email_capture_rate', 'FLOAT DEFAULT 0'),
            ('phone_capture_rate', 'FLOAT DEFAULT 0'),
            ('email_generation_rate', 'FLOAT DEFAULT 0'),
            ('email_send_rate', 'FLOAT DEFAULT 0')
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                print(f"Adding column: {col_name} {col_type}")
                conn.execute(text(f"ALTER TABLE campaign_analytics ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"✓ Added column: {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"Column {col_name} already exists")
                else:
                    print(f"Error adding column {col_name}: {e}")
                    
        print("\n✓ Campaign analytics table fixed!")

if __name__ == "__main__":
    fix_campaign_analytics() 