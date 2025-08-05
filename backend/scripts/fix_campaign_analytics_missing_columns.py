"""
Add missing columns to campaign_analytics table
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def add_missing_columns():
    """Add missing columns to campaign_analytics table"""
    session = Session()
    
    try:
        # Check if columns exist and add them if missing
        columns_to_add = [
            ("contacts_with_email", "INTEGER DEFAULT 0"),
            ("contacts_with_phone", "INTEGER DEFAULT 0"),
            ("enrichment_success_rate", "FLOAT DEFAULT 0.0"),
            ("email_capture_rate", "FLOAT DEFAULT 0.0"),
            ("phone_capture_rate", "FLOAT DEFAULT 0.0"),
            ("email_generation_rate", "FLOAT DEFAULT 0.0"),
            ("email_send_rate", "FLOAT DEFAULT 0.0"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                result = session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'campaign_analytics' 
                    AND column_name = '{column_name}'
                """))
                
                if not result.fetchone():
                    # Add the column
                    session.execute(text(f"""
                        ALTER TABLE campaign_analytics 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    print(f"✓ Added column: {column_name}")
                else:
                    print(f"  Column already exists: {column_name}")
                    
            except Exception as e:
                print(f"✗ Error checking/adding column {column_name}: {e}")
        
        session.commit()
        print("\n✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Adding missing columns to campaign_analytics table...")
    add_missing_columns() 