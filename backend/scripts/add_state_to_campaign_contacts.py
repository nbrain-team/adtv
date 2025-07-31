#!/usr/bin/env python3
"""
Add state column to campaign_contacts table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def add_state_column():
    """Add state column to campaign_contacts table"""
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='campaign_contacts' AND column_name='state'
        """))
        
        if result.rowcount > 0:
            print("State column already exists in campaign_contacts table")
            return
        
        # Add the column
        conn.execute(text("""
            ALTER TABLE campaign_contacts 
            ADD COLUMN state VARCHAR
        """))
        conn.commit()
        
        print("Successfully added state column to campaign_contacts table")

if __name__ == "__main__":
    add_state_column() 