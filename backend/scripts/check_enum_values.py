"""
Check actual enum values in PostgreSQL database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def check_enum_values():
    """Check what enum values exist in the database"""
    
    with engine.connect() as conn:
        # Check PostStatus enum values
        print("🔍 Checking PostStatus enum values in database...")
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'poststatus'
            )
            ORDER BY enumsortorder;
        """))
        
        post_statuses = [row[0] for row in result]
        print(f"PostStatus values: {post_statuses}")
        
        # Check AdStatus enum values
        print("\n🔍 Checking AdStatus enum values in database...")
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'adstatus'
            )
            ORDER BY enumsortorder;
        """))
        
        ad_statuses = [row[0] for row in result]
        print(f"AdStatus values: {ad_statuses}")

if __name__ == "__main__":
    check_enum_values() 