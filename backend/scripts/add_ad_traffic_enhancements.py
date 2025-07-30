#!/usr/bin/env python3
"""
Add enhanced fields for Ad Traffic module
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_ad_traffic_enhancements():
    """Add new fields for ad traffic enhancements"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add fields to ad_traffic_clients
            logger.info("Adding budget and targeting fields to ad_traffic_clients...")
            conn.execute(text("""
                ALTER TABLE ad_traffic_clients 
                ADD COLUMN IF NOT EXISTS daily_budget FLOAT DEFAULT 0.0
            """))
            conn.execute(text("""
                ALTER TABLE ad_traffic_clients 
                ADD COLUMN IF NOT EXISTS ad_duration_days INTEGER DEFAULT 7
            """))
            conn.execute(text("""
                ALTER TABLE ad_traffic_clients 
                ADD COLUMN IF NOT EXISTS geo_targeting JSON DEFAULT '[]'::json
            """))
            conn.commit()
            
            # Add fields to ad_traffic_campaigns
            logger.info("Adding video_urls and start_date to ad_traffic_campaigns...")
            conn.execute(text("""
                ALTER TABLE ad_traffic_campaigns 
                ADD COLUMN IF NOT EXISTS video_urls JSON DEFAULT '[]'::json
            """))
            conn.execute(text("""
                ALTER TABLE ad_traffic_campaigns 
                ADD COLUMN IF NOT EXISTS start_date TIMESTAMP
            """))
            conn.commit()
            
            # Add fields to video_clips
            logger.info("Adding source_video_url and aspect_ratio to video_clips...")
            conn.execute(text("""
                ALTER TABLE video_clips 
                ADD COLUMN IF NOT EXISTS source_video_url VARCHAR
            """))
            conn.execute(text("""
                ALTER TABLE video_clips 
                ADD COLUMN IF NOT EXISTS aspect_ratio VARCHAR
            """))
            conn.commit()
            
            # Add fields to social_posts
            logger.info("Adding approval and metrics fields to social_posts...")
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN IF NOT EXISTS published_time TIMESTAMP
            """))
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN IF NOT EXISTS approved_by VARCHAR
            """))
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP
            """))
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN IF NOT EXISTS metrics JSON DEFAULT '{}'::json
            """))
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN IF NOT EXISTS budget_spent FLOAT DEFAULT 0.0
            """))
            
            # Rename platform_data to platform_post_ids if it exists
            conn.execute(text("""
                DO $$ 
                BEGIN 
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='social_posts' AND column_name='platform_data') THEN
                        ALTER TABLE social_posts RENAME COLUMN platform_data TO platform_post_ids;
                    ELSE
                        ALTER TABLE social_posts ADD COLUMN IF NOT EXISTS platform_post_ids JSON DEFAULT '{}'::json;
                    END IF;
                END $$;
            """))
            
            # Convert media_urls from ARRAY to JSON
            conn.execute(text("""
                DO $$ 
                BEGIN 
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='social_posts' AND column_name='media_urls' 
                              AND data_type = 'ARRAY') THEN
                        ALTER TABLE social_posts ADD COLUMN media_urls_new JSON DEFAULT '{}'::json;
                        UPDATE social_posts SET media_urls_new = to_json(media_urls);
                        ALTER TABLE social_posts DROP COLUMN media_urls;
                        ALTER TABLE social_posts RENAME COLUMN media_urls_new TO media_urls;
                    ELSE
                        ALTER TABLE social_posts ADD COLUMN IF NOT EXISTS media_urls JSON DEFAULT '{}'::json;
                    END IF;
                END $$;
            """))
            
            conn.commit()
            
            logger.info("Successfully added all enhancement fields")
            
        except Exception as e:
            logger.error(f"Error adding fields: {e}")
            raise

if __name__ == "__main__":
    add_ad_traffic_enhancements()
    print("✅ Ad Traffic enhancements migration completed successfully!") 