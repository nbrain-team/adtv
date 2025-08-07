#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.begin() as conn:
        # Create agreements table
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
        print("✅ Agreements table created!")
        
        # Also add columns to campaign_contacts
        try:
            conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN agreement_status VARCHAR(50)"))
            print("✅ Added agreement_status")
        except:
            pass
        
        try:
            conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN agreement_sent_at TIMESTAMP"))
            print("✅ Added agreement_sent_at")
        except:
            pass
            
        try:
            conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN agreement_signed_at TIMESTAMP"))
            print("✅ Added agreement_signed_at")
        except:
            pass
            
        try:
            conn.execute(text("ALTER TABLE campaign_contacts ADD COLUMN agreement_data TEXT"))
            print("✅ Added agreement_data")
        except:
            pass
            
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n🎉 All done! Agreements table is ready.") 