#!/usr/bin/env python3
"""
Production script to diagnose and fix agreement-related issues
Run this on Render via the Shell tab
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from datetime import datetime
import json

def main():
    # Get database URL from environment
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return 1
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("=" * 70)
    print("AGREEMENT SYSTEM DIAGNOSTIC & FIX")
    print("=" * 70)
    
    # 1. Check if agreements table exists
    print("\n📋 STEP 1: Checking agreements table...")
    if 'agreements' not in inspector.get_table_names():
        print("❌ agreements table does NOT exist - Creating it now...")
        
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agreements (
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
            print("✅ agreements table created successfully")
    else:
        print("✅ agreements table exists")
        
        # Check columns
        columns = inspector.get_columns('agreements')
        print(f"   Found {len(columns)} columns")
    
    # 2. Check campaign_contacts table for agreement fields
    print("\n📋 STEP 2: Checking campaign_contacts agreement fields...")
    if 'campaign_contacts' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('campaign_contacts')}
        
        required_fields = [
            'agreement_status',
            'agreement_sent_at',
            'agreement_signed_at',
            'agreement_data'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in columns:
                missing_fields.append(field)
                print(f"   ❌ Missing field: {field}")
        
        if missing_fields:
            print("   Adding missing fields...")
            with engine.begin() as conn:
                for field in missing_fields:
                    try:
                        if field == 'agreement_data':
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field} TEXT"))
                        elif field.endswith('_at'):
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field} TIMESTAMP"))
                        else:
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field} VARCHAR(50)"))
                        print(f"   ✅ Added field: {field}")
                    except Exception as e:
                        if 'already exists' in str(e).lower():
                            print(f"   ℹ️  Field {field} already exists")
                        else:
                            print(f"   ❌ Error adding {field}: {e}")
        else:
            print("   ✅ All agreement fields exist")
    else:
        print("   ❌ campaign_contacts table not found!")
    
    # 3. Check for specific agreement
    print("\n📋 STEP 3: Checking specific agreement...")
    agreement_id = '74a6c87c-06d3-4e56-ad8f-9088c48a64fe'
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, contact_name, status, created_at, agreement_url
            FROM agreements
            WHERE id = :agreement_id
        """), {'agreement_id': agreement_id})
        
        row = result.fetchone()
        if row:
            print(f"   ✅ Agreement found:")
            print(f"      ID: {row[0]}")
            print(f"      Contact: {row[1]}")
            print(f"      Status: {row[2]}")
            print(f"      Created: {row[3]}")
            print(f"      URL: {row[4]}")
        else:
            print(f"   ❌ Agreement {agreement_id} NOT found in database")
    
    # 4. Show recent agreements
    print("\n📋 STEP 4: Recent agreements (last 10)...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, contact_name, status, created_at, campaign_name
            FROM agreements
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"   • {row[0][:8]}... | {row[1]:20} | {row[2]:10} | {row[3]} | {row[4]}")
        else:
            print("   No agreements found in database")
    
    # 5. Check contacts with agreement data
    print("\n📋 STEP 5: Checking contacts with agreement data...")
    with engine.connect() as conn:
        # Check if agreement_data column exists
        if 'campaign_contacts' in inspector.get_table_names():
            columns = {col['name'] for col in inspector.get_columns('campaign_contacts')}
            if 'agreement_data' in columns:
                result = conn.execute(text("""
                    SELECT id, first_name, last_name, agreement_status, agreement_data
                    FROM campaign_contacts
                    WHERE agreement_data IS NOT NULL
                    LIMIT 10
                """))
                
                rows = result.fetchall()
                if rows:
                    print(f"   Found {len(rows)} contacts with agreement data:")
                    for row in rows:
                        try:
                            data = json.loads(row[4]) if row[4] else {}
                            agreement_id = data.get('agreement_id', 'N/A')
                            print(f"   • {row[1]} {row[2]} | Status: {row[3]} | Agreement ID: {agreement_id}")
                        except:
                            print(f"   • {row[1]} {row[2]} | Status: {row[3]} | Invalid agreement data")
                else:
                    print("   No contacts found with agreement data")
            else:
                print("   agreement_data column not found in campaign_contacts")
    
    # 6. Check for orphaned agreements (agreements without valid contacts)
    print("\n📋 STEP 6: Checking for data integrity...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM agreements
        """))
        total = result.scalar()
        print(f"   Total agreements in database: {total}")
        
        # Check for agreements with missing campaign
        result = conn.execute(text("""
            SELECT COUNT(*) FROM agreements a
            LEFT JOIN campaigns c ON a.campaign_id = c.id
            WHERE c.id IS NULL
        """))
        orphaned = result.scalar()
        if orphaned > 0:
            print(f"   ⚠️  Found {orphaned} agreements with missing campaigns")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    
    # Summary and recommendations
    print("\n📊 SUMMARY & RECOMMENDATIONS:")
    print("1. If agreements table was created, restart the backend service")
    print("2. If agreement fields were added, contacts should now track agreements")
    print("3. Check the backend logs for any error messages during agreement creation")
    print("4. The agreement URL format should be: https://adtv-frontend.onrender.com/agreement/{id}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 