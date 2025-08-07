#!/usr/bin/env python3
"""
Check if agreements table exists and show existing agreements
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database import engine
import json

def check_agreements_table():
    """Check agreements table status"""
    
    print("=" * 60)
    print("CHECKING AGREEMENTS TABLE")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Available tables: {', '.join(tables)}")
        
        if 'agreements' not in tables:
            print("\n❌ 'agreements' table does not exist!")
            print("\nTo create it, the application needs to start up properly.")
            print("The table should be created automatically by the agreements module.")
            return False
        
        print("\n✅ 'agreements' table exists")
        
        # Get columns
        columns = inspector.get_columns('agreements')
        print(f"\n📊 Columns in agreements table:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
        
        # Check if there are any agreements
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM agreements"))
            count = result.scalar()
            print(f"\n📈 Total agreements in database: {count}")
            
            if count > 0:
                # Show recent agreements
                result = conn.execute(text("""
                    SELECT id, contact_name, contact_email, campaign_name, status, created_at
                    FROM agreements 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                
                print("\n🔍 Recent agreements:")
                for row in result:
                    print(f"\n   ID: {row[0]}")
                    print(f"   Contact: {row[1]} ({row[2]})")
                    print(f"   Campaign: {row[3]}")
                    print(f"   Status: {row[4]}")
                    print(f"   Created: {row[5]}")
            
            # Check for the specific agreement ID from the error
            agreement_id = "0e0a939b-552e-4e98-8bfc-dec035772ed5"
            result = conn.execute(text(
                "SELECT * FROM agreements WHERE id = :id"
            ), {"id": agreement_id})
            
            row = result.fetchone()
            if row:
                print(f"\n✅ Found agreement {agreement_id}")
            else:
                print(f"\n❌ Agreement {agreement_id} NOT found in database")
                print("   This agreement may not have been created successfully.")
        
        return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_agreements_table()
    sys.exit(0 if success else 1) 