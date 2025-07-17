"""
Migration script to add processed_jobs and merged_contacts tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine

def add_processed_jobs_tables():
    """Add the processed_jobs and merged_contacts tables"""
    
    with engine.connect() as conn:
        # Create processed_jobs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS processed_jobs (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id),
                source_job_ids JSON NOT NULL,
                status VARCHAR DEFAULT 'PENDING',
                total_contacts INTEGER DEFAULT 0,
                duplicates_removed INTEGER DEFAULT 0,
                emails_validated INTEGER DEFAULT 0,
                websites_crawled INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create merged_contacts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS merged_contacts (
                id VARCHAR PRIMARY KEY,
                processed_job_id VARCHAR NOT NULL REFERENCES processed_jobs(id) ON DELETE CASCADE,
                first_name VARCHAR,
                last_name VARCHAR,
                company VARCHAR,
                city VARCHAR,
                state VARCHAR,
                dma VARCHAR,
                cell_phone VARCHAR,
                phone2 VARCHAR,
                email VARCHAR,
                personal_email VARCHAR,
                agent_website VARCHAR,
                facebook_profile VARCHAR,
                fb_or_website VARCHAR,
                profile_url VARCHAR,
                years_exp INTEGER,
                closed_sales VARCHAR,
                total_value VARCHAR,
                price_range VARCHAR,
                average_price VARCHAR,
                website_content TEXT,
                email_valid BOOLEAN,
                email_score FLOAT,
                email_status VARCHAR,
                source_count INTEGER DEFAULT 1,
                merge_confidence FLOAT DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Also add the new columns to realtor_contacts if they don't exist
        try:
            conn.execute(text("""
                ALTER TABLE realtor_contacts 
                ADD COLUMN IF NOT EXISTS closed_sales VARCHAR,
                ADD COLUMN IF NOT EXISTS total_value VARCHAR,
                ADD COLUMN IF NOT EXISTS price_range VARCHAR,
                ADD COLUMN IF NOT EXISTS average_price VARCHAR;
            """))
        except Exception as e:
            print(f"Note: Could not add columns to realtor_contacts (they may already exist): {e}")
        
        conn.commit()
        print("✓ Successfully added processed_jobs and merged_contacts tables")

if __name__ == "__main__":
    add_processed_jobs_tables() 