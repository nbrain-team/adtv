#!/usr/bin/env python3
"""
Script to add agent_website column to realtor_contacts table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def add_agent_website_column():
    """Add agent_website column to realtor_contacts table if it doesn't exist"""
    print("Adding agent_website column to realtor_contacts table...")
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='realtor_contacts' 
            AND column_name='agent_website'
        """))
        
        if result.fetchone():
            print("Column agent_website already exists, skipping...")
            return
        
        # Add the column
        conn.execute(text("""
            ALTER TABLE realtor_contacts 
            ADD COLUMN agent_website VARCHAR
        """))
        conn.commit()
        
    print("Successfully added agent_website column!")

if __name__ == "__main__":
    add_agent_website_column() 