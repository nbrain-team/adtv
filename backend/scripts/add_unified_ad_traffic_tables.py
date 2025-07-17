"""
Migration script to add unified ad traffic tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine

def add_unified_ad_traffic_tables():
    """Add the unified ad traffic tables"""
    
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
                social_accounts JSON DEFAULT '{}',
                industry VARCHAR,
                description TEXT,
                brand_voice TEXT,
                target_audience TEXT,
                brand_colors JSON,
                logo_url VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create video_clip_campaigns table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS video_clip_campaigns (
                id VARCHAR PRIMARY KEY,
                client_id VARCHAR NOT NULL REFERENCES ad_traffic_clients(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                original_video_url VARCHAR NOT NULL,
                duration_weeks INTEGER NOT NULL,
                platforms JSON NOT NULL,
                status VARCHAR DEFAULT 'processing',
                progress INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create video_clips table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS video_clips (
                id VARCHAR PRIMARY KEY,
                campaign_id VARCHAR NOT NULL REFERENCES video_clip_campaigns(id) ON DELETE CASCADE,
                title VARCHAR NOT NULL,
                description TEXT,
                duration FLOAT NOT NULL,
                start_time FLOAT NOT NULL,
                end_time FLOAT NOT NULL,
                video_url VARCHAR NOT NULL,
                thumbnail_url VARCHAR,
                platform_versions JSON DEFAULT '{}',
                suggested_caption TEXT,
                suggested_hashtags JSON DEFAULT '[]',
                content_type VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create social_media_posts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS social_media_posts (
                id VARCHAR PRIMARY KEY,
                client_id VARCHAR NOT NULL REFERENCES ad_traffic_clients(id) ON DELETE CASCADE,
                campaign_id VARCHAR REFERENCES video_clip_campaigns(id) ON DELETE SET NULL,
                video_clip_id VARCHAR REFERENCES video_clips(id) ON DELETE SET NULL,
                content TEXT NOT NULL,
                platforms JSON NOT NULL,
                media_urls JSON DEFAULT '[]',
                scheduled_time TIMESTAMP NOT NULL,
                status VARCHAR DEFAULT 'draft',
                published_at TIMESTAMP,
                platform_data JSON DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_traffic_clients_user ON ad_traffic_clients(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_video_clip_campaigns_client ON video_clip_campaigns(client_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_video_clips_campaign ON video_clips(campaign_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_social_media_posts_client ON social_media_posts(client_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_social_media_posts_campaign ON social_media_posts(campaign_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_social_media_posts_scheduled ON social_media_posts(scheduled_time);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_social_media_posts_status ON social_media_posts(status);"))
        
        conn.commit()
        print("✓ Successfully added unified ad traffic tables")

if __name__ == "__main__":
    add_unified_ad_traffic_tables() 