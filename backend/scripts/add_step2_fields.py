#!/usr/bin/env python3
"""
Script to add Step 2 fields to realtor_contacts table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def add_step2_fields():
    """Add Step 2 fields to realtor_contacts table if they don't exist"""
    print("Adding Step 2 fields to realtor_contacts table...")
    
    fields_to_add = [
        ('phone2', 'VARCHAR'),
        ('personal_email', 'VARCHAR'),
        ('facebook_profile', 'VARCHAR')
    ]
    
    with engine.connect() as conn:
        for field_name, field_type in fields_to_add:
            # Check if column already exists
            result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='realtor_contacts' 
                AND column_name='{field_name}'
            """))
            
            if result.fetchone():
                print(f"Column {field_name} already exists, skipping...")
            else:
                # Add the column
                conn.execute(text(f"""
                    ALTER TABLE realtor_contacts 
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"Added column {field_name}")
        
        conn.commit()
        
    print("Successfully added Step 2 fields!")

if __name__ == "__main__":
    add_step2_fields() 