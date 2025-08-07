#!/usr/bin/env python3
"""
Manually create the agreements table if it doesn't exist
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_agreements_table():
    """Create the agreements table manually"""
    
    print("=" * 60)
    print("CREATING AGREEMENTS TABLE")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        
        if 'agreements' in inspector.get_table_names():
            print("\n✅ 'agreements' table already exists")
            return True
        
        print("\n📝 Creating agreements table...")
        
        create_table_query = """
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
        );
        """
        
        with engine.begin() as conn:
            conn.execute(text(create_table_query))
            print("✅ Agreements table created successfully!")
        
        # Verify it was created
        inspector = inspect(engine)
        if 'agreements' in inspector.get_table_names():
            columns = inspector.get_columns('agreements')
            print(f"\n📊 Created with {len(columns)} columns:")
            for col in columns:
                print(f"   - {col['name']}")
            return True
        else:
            print("❌ Failed to verify table creation")
            return False
            
    except Exception as e:
        print(f"\n❌ Error creating table: {e}")
        
        # If it's a duplicate table error, that's actually ok
        if "already exists" in str(e).lower():
            print("ℹ️  Table already exists (this is OK)")
            return True
        return False

if __name__ == "__main__":
    success = create_agreements_table()
    sys.exit(0 if success else 1) 