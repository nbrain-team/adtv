#!/usr/bin/env python3
"""Add social_accounts column to ad_traffic_clients table"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def add_social_accounts_column():
    """Add social_accounts JSON column to ad_traffic_clients table"""
    
    with engine.begin() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='ad_traffic_clients' 
            AND column_name='social_accounts'
        """))
        
        if result.rowcount > 0:
            print("✓ Column 'social_accounts' already exists")
            return
        
        # Add the column
        print("Adding social_accounts column...")
        conn.execute(text("""
            ALTER TABLE ad_traffic_clients 
            ADD COLUMN social_accounts JSON DEFAULT '{}'::json
        """))
        
        print("✅ Successfully added social_accounts column to ad_traffic_clients table")

if __name__ == "__main__":
    try:
        add_social_accounts_column()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1) 