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
    
    added_count = 0
    exists_count = 0
    error_count = 0
    
    for col_name, col_type in columns_to_add:
        # Use a new connection for each column to avoid transaction issues
        with engine.connect() as conn:
            try:
                print(f"Adding column: {col_name} {col_type}")
                conn.execute(text(f"ALTER TABLE campaign_analytics ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"✓ Added column: {col_name}")
                added_count += 1
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"Column {col_name} already exists")
                    exists_count += 1
                else:
                    print(f"Error adding column {col_name}: {e}")
                    error_count += 1
    
    print(f"\n=== Summary ===")
    print(f"✓ Added: {added_count} columns")
    print(f"✓ Already existed: {exists_count} columns")
    if error_count > 0:
        print(f"✗ Errors: {error_count} columns")
    print(f"\n✓ Campaign analytics table update complete!")

if __name__ == "__main__":
    fix_campaign_analytics() 