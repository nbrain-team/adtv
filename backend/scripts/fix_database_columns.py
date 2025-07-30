#!/usr/bin/env python3
"""
Fix all missing database columns for Campaign Builder and Ad Traffic
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_all_database_columns():
    """Fix all missing columns in the database"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 1. Fix campaign_analytics table
            logger.info("Fixing campaign_analytics table...")
            
            # Check if table exists
            inspector = inspect(engine)
            if 'campaign_analytics' in inspector.get_table_names():
                # Add missing columns
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS contacts_with_email INTEGER DEFAULT 0
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS contacts_with_phone INTEGER DEFAULT 0
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS email_capture_rate FLOAT DEFAULT 0.0
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS phone_capture_rate FLOAT DEFAULT 0.0
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS email_generation_rate FLOAT DEFAULT 0.0
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS email_send_rate FLOAT DEFAULT 0.0
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS sending_start_time TIMESTAMP
                """))
                conn.execute(text("""
                    ALTER TABLE campaign_analytics 
                    ADD COLUMN IF NOT EXISTS sending_end_time TIMESTAMP
                """))
                conn.commit()
                logger.info("✅ campaign_analytics table fixed")
            else:
                logger.warning("⚠️  campaign_analytics table not found")
            
            # 2. Fix ad_traffic_clients table
            logger.info("Fixing ad_traffic_clients table...")
            
            if 'ad_traffic_clients' in inspector.get_table_names():
                # Add missing columns
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
                logger.info("✅ ad_traffic_clients table fixed")
            else:
                logger.warning("⚠️  ad_traffic_clients table not found")
            
            # 3. Fix ad_traffic_campaigns table
            logger.info("Fixing ad_traffic_campaigns table...")
            
            if 'ad_traffic_campaigns' in inspector.get_table_names():
                conn.execute(text("""
                    ALTER TABLE ad_traffic_campaigns 
                    ADD COLUMN IF NOT EXISTS video_urls JSON DEFAULT '[]'::json
                """))
                conn.execute(text("""
                    ALTER TABLE ad_traffic_campaigns 
                    ADD COLUMN IF NOT EXISTS start_date TIMESTAMP
                """))
                conn.commit()
                logger.info("✅ ad_traffic_campaigns table fixed")
            else:
                logger.warning("⚠️  ad_traffic_campaigns table not found")
            
            # 4. Fix video_clips table
            logger.info("Fixing video_clips table...")
            
            if 'video_clips' in inspector.get_table_names():
                conn.execute(text("""
                    ALTER TABLE video_clips 
                    ADD COLUMN IF NOT EXISTS source_video_url VARCHAR
                """))
                conn.execute(text("""
                    ALTER TABLE video_clips 
                    ADD COLUMN IF NOT EXISTS aspect_ratio VARCHAR
                """))
                conn.commit()
                logger.info("✅ video_clips table fixed")
            else:
                logger.warning("⚠️  video_clips table not found")
            
            # 5. Fix social_posts table
            logger.info("Fixing social_posts table...")
            
            if 'social_posts' in inspector.get_table_names():
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
                
                # Handle platform_data to platform_post_ids rename
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
                
                # Fix media_urls - convert arrays to JSON dicts
                logger.info("Fixing media_urls field...")
                
                # First ensure column exists
                conn.execute(text("""
                    ALTER TABLE social_posts 
                    ADD COLUMN IF NOT EXISTS media_urls JSON DEFAULT '{}'::json
                """))
                
                # Convert empty arrays to empty dicts
                conn.execute(text("""
                    UPDATE social_posts 
                    SET media_urls = '{}'::json 
                    WHERE media_urls IS NOT NULL AND media_urls::text = '[]'
                """))
                
                conn.commit()
                logger.info("✅ social_posts table fixed")
            else:
                logger.warning("⚠️  social_posts table not found")
            
            logger.info("\n✅ All database column fixes completed successfully!")
            
            # Show current table status
            logger.info("\n=== Current Table Status ===")
            for table in ['campaign_analytics', 'ad_traffic_clients', 'ad_traffic_campaigns', 'video_clips', 'social_posts']:
                if table in inspector.get_table_names():
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"✅ {table}: {count} records")
                else:
                    logger.info(f"❌ {table}: NOT FOUND")
            
        except Exception as e:
            logger.error(f"Error fixing database columns: {e}")
            raise

if __name__ == "__main__":
    fix_all_database_columns()
    print("\n✅ Database fix completed!") 