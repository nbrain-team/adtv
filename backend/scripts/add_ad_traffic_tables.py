"""
Migration script to add ad traffic tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine

def add_ad_traffic_tables():
    """Add the ad_traffic_clients and scheduled_posts tables"""
    
    with engine.connect() as conn:
        # Create ad_traffic_clients table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ad_traffic_clients (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id),
                name VARCHAR NOT NULL,
                company_name VARCHAR,
                email VARCHAR,
                phone VARCHAR,
                website VARCHAR,
                facebook_page_id VARCHAR,
                facebook_page_name VARCHAR,
                facebook_access_token TEXT,
                instagram_account_id VARCHAR,
                instagram_username VARCHAR,
                industry VARCHAR,
                description TEXT,
                brand_voice TEXT,
                target_audience TEXT,
                brand_colors JSON,
                logo_url VARCHAR,
                auto_post_enabled BOOLEAN DEFAULT FALSE,
                default_post_times JSON,
                hashtag_sets JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create scheduled_posts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id VARCHAR PRIMARY KEY,
                client_id VARCHAR NOT NULL REFERENCES ad_traffic_clients(id) ON DELETE CASCADE,
                campaign_id VARCHAR,
                content TEXT NOT NULL,
                media_urls JSON,
                video_clip_ids JSON,
                platforms JSON NOT NULL,
                platform_specific_content JSON,
                scheduled_time TIMESTAMP NOT NULL,
                status VARCHAR DEFAULT 'scheduled',
                published_at TIMESTAMP,
                facebook_post_id VARCHAR,
                instagram_post_id VARCHAR,
                error_message TEXT,
                engagement_metrics JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Add client_id columns to existing tables
        conn.execute(text("""
            ALTER TABLE video_processing_jobs 
            ADD COLUMN IF NOT EXISTS client_id VARCHAR;
        """))
        
        conn.execute(text("""
            ALTER TABLE video_clips 
            ADD COLUMN IF NOT EXISTS client_id VARCHAR;
        """))
        
        # Note: Not adding client_id to campaigns table since it might not exist
        # This can be added later when campaigns module is integrated
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_traffic_clients_user ON ad_traffic_clients(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_posts_client ON scheduled_posts(client_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_posts_time ON scheduled_posts(scheduled_time);"))
        
        conn.commit()
        print("✓ Successfully added ad traffic tables")

if __name__ == "__main__":
    add_ad_traffic_tables() 