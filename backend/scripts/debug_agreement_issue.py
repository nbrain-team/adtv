#!/usr/bin/env python3
"""
Debug script to check why agreements aren't showing in RSVP table
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
import json

def main():
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return 1
    
    engine = create_engine(DATABASE_URL)
    
    print("=" * 70)
    print("AGREEMENT SYSTEM DEBUG")
    print("=" * 70)
    
    # Check if agreements table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n📋 Step 1: Checking tables...")
    print(f"   Tables in database: {', '.join(tables[:10])}")
    
    if 'agreements' not in tables:
        print("   ❌ agreements table DOES NOT EXIST!")
        print("   Run: python scripts/force_create_agreements_table.py")
        return 1
    else:
        print("   ✅ agreements table exists")
    
    # Check campaign_contacts columns
    print("\n📋 Step 2: Checking campaign_contacts columns...")
    if 'campaign_contacts' in tables:
        columns = {col['name'] for col in inspector.get_columns('campaign_contacts')}
        agreement_fields = ['agreement_status', 'agreement_sent_at', 'agreement_signed_at', 'agreement_data']
        
        missing = []
        for field in agreement_fields:
            if field in columns:
                print(f"   ✅ {field} exists")
            else:
                print(f"   ❌ {field} MISSING")
                missing.append(field)
        
        if missing:
            print("\n   ⚠️ Missing fields need to be added!")
            with engine.begin() as conn:
                for field in missing:
                    try:
                        if field == 'agreement_data':
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field} TEXT"))
                        elif field.endswith('_at'):
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field} TIMESTAMP"))
                        else:
                            conn.execute(text(f"ALTER TABLE campaign_contacts ADD COLUMN {field} VARCHAR(50)"))
                        print(f"   ✅ Added {field}")
                    except Exception as e:
                        print(f"   ❌ Error adding {field}: {e}")
    
    # Check for Danny's contact
    print("\n📋 Step 3: Checking for Danny's contact...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, first_name, last_name, email, is_rsvp, 
                   agreement_status, agreement_data, campaign_id
            FROM campaign_contacts 
            WHERE email = 'danny@nbrain.ai' 
            LIMIT 5
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"   Found {len(rows)} contacts with email danny@nbrain.ai:")
            for row in rows:
                print(f"\n   Contact ID: {row[0]}")
                print(f"   Name: {row[1]} {row[2]}")
                print(f"   Is RSVP: {row[4]}")
                print(f"   Agreement Status: {row[5]}")
                print(f"   Campaign ID: {row[7]}")
                
                if row[6]:  # agreement_data
                    try:
                        data = json.loads(row[6])
                        print(f"   Agreement Data: {json.dumps(data, indent=2)}")
                    except:
                        print(f"   Agreement Data (raw): {row[6][:100]}...")
                else:
                    print("   Agreement Data: None")
        else:
            print("   No contacts found with email danny@nbrain.ai")
    
    # Check agreements for Danny
    print("\n📋 Step 4: Checking agreements for Danny...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, contact_name, contact_email, status, created_at, agreement_url
            FROM agreements 
            WHERE contact_email = 'danny@nbrain.ai'
            ORDER BY created_at DESC
            LIMIT 5
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"   Found {len(rows)} agreements for danny@nbrain.ai:")
            for row in rows:
                print(f"\n   Agreement ID: {row[0]}")
                print(f"   Contact Name: {row[1]}")
                print(f"   Status: {row[3]}")
                print(f"   Created: {row[4]}")
                print(f"   URL: {row[5]}")
        else:
            print("   No agreements found for danny@nbrain.ai")
    
    # Check specific agreement IDs from logs
    print("\n📋 Step 5: Checking specific agreements from logs...")
    agreement_ids = [
        '257f9d1a-13dd-4bfc-8e68-757f901cddb9',
        '1fff9832-ec49-45d5-8962-32bd755c6797',
        '74a6c87c-06d3-4e56-ad8f-9088c48a64fe'
    ]
    
    with engine.connect() as conn:
        for aid in agreement_ids:
            result = conn.execute(text("""
                SELECT id, contact_name, status, created_at
                FROM agreements 
                WHERE id = :id
            """), {'id': aid})
            
            row = result.fetchone()
            if row:
                print(f"   ✅ {aid[:8]}... exists | {row[1]} | {row[2]}")
            else:
                print(f"   ❌ {aid[:8]}... NOT FOUND")
    
    # Check if there's a mismatch between contact IDs
    print("\n📋 Step 6: Checking for contact/agreement mismatches...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM campaign_contacts cc
            WHERE cc.agreement_data IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM agreements a 
                WHERE a.contact_id = cc.id
            )
        """))
        
        orphaned = result.scalar()
        if orphaned > 0:
            print(f"   ⚠️ Found {orphaned} contacts with agreement_data but no matching agreement record")
    
    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print("=" * 70)
    
    print("\n📊 SUMMARY:")
    print("1. If agreements table is missing, run force_create_agreements_table.py")
    print("2. If agreement fields are missing from contacts, they've been added now")
    print("3. Check if agreements are being created but not linked to contacts")
    print("4. Restart the backend service after any changes")
    
    return 0

if __name__ == "__main__":
    exit(main()) 