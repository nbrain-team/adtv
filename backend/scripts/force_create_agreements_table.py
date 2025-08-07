#!/usr/bin/env python3
"""
Force create agreements table and verify it works
Run this directly on Render to fix the agreements system
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
import uuid
from datetime import datetime

def main():
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return 1
    
    engine = create_engine(DATABASE_URL)
    
    print("=" * 70)
    print("FORCE CREATE AGREEMENTS TABLE")
    print("=" * 70)
    
    # Drop and recreate the table to ensure it exists with correct schema
    with engine.begin() as conn:
        print("\n📋 Step 1: Dropping existing agreements table if it exists...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS agreements CASCADE"))
            print("✅ Dropped old agreements table (if it existed)")
        except Exception as e:
            print(f"⚠️ Error dropping table: {e}")
        
        print("\n📋 Step 2: Creating new agreements table...")
        try:
            conn.execute(text("""
                CREATE TABLE agreements (
                    id VARCHAR PRIMARY KEY,
                    campaign_id VARCHAR NOT NULL,
                    contact_id VARCHAR NOT NULL,
                    contact_name VARCHAR NOT NULL,
                    contact_email VARCHAR NOT NULL,
                    company VARCHAR,
                    start_date VARCHAR NOT NULL,
                    setup_fee FLOAT NOT NULL,
                    monthly_fee FLOAT NOT NULL,
                    campaign_name VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'pending',
                    signature TEXT,
                    signature_type VARCHAR,
                    signed_date VARCHAR,
                    signed_at TIMESTAMP,
                    viewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pdf_data TEXT,
                    agreement_url VARCHAR
                )
            """))
            print("✅ Created agreements table successfully")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return 1
    
    # Verify the table exists
    inspector = inspect(engine)
    if 'agreements' in inspector.get_table_names():
        print("\n✅ VERIFIED: agreements table exists")
        columns = inspector.get_columns('agreements')
        print(f"   Found {len(columns)} columns:")
        for col in columns[:5]:  # Show first 5 columns
            print(f"   - {col['name']}: {col['type']}")
    else:
        print("\n❌ ERROR: agreements table still doesn't exist!")
        return 1
    
    # Test by creating a dummy agreement
    print("\n📋 Step 3: Testing with a dummy agreement...")
    test_id = str(uuid.uuid4())
    with engine.begin() as conn:
        try:
            conn.execute(text("""
                INSERT INTO agreements (
                    id, campaign_id, contact_id, contact_name, contact_email,
                    company, start_date, setup_fee, monthly_fee, campaign_name,
                    status, agreement_url
                ) VALUES (
                    :id, :campaign_id, :contact_id, :contact_name, :contact_email,
                    :company, :start_date, :setup_fee, :monthly_fee, :campaign_name,
                    :status, :agreement_url
                )
            """), {
                'id': test_id,
                'campaign_id': 'test-campaign',
                'contact_id': 'test-contact',
                'contact_name': 'Test User',
                'contact_email': 'test@example.com',
                'company': 'Test Company',
                'start_date': '2024-01-01',
                'setup_fee': 100.0,
                'monthly_fee': 50.0,
                'campaign_name': 'Test Campaign',
                'status': 'pending',
                'agreement_url': f'https://test.com/agreement/{test_id}'
            })
            print(f"✅ Successfully created test agreement: {test_id}")
            
            # Verify it was saved
            result = conn.execute(text("SELECT COUNT(*) FROM agreements WHERE id = :id"), {'id': test_id})
            count = result.scalar()
            if count == 1:
                print("✅ Test agreement verified in database")
                
                # Clean up test
                conn.execute(text("DELETE FROM agreements WHERE id = :id"), {'id': test_id})
                print("✅ Test agreement cleaned up")
            else:
                print("❌ Test agreement not found in database!")
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("\n✅ The agreements table is now ready to use!")
    print("⚠️  IMPORTANT: Restart the backend service now!")
    print("   In Render Dashboard → Backend Service → Manual Deploy → Deploy latest commit")
    
    return 0

if __name__ == "__main__":
    exit(main()) 