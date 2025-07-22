"""
Fix video_clips table schema for ad_traffic module
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_video_clips_schema():
    """Fix the video_clips table to work with ad_traffic module"""
    
    with engine.connect() as conn:
        try:
            # Check if the old video_clips table exists with job_id
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'video_clips' 
                AND column_name = 'job_id'
            """))
            
            has_job_id = result.fetchone() is not None
            
            if has_job_id:
                logger.info("Found old video_clips table with job_id column")
                
                # Drop the old video_clips table
                logger.info("Dropping old video_clips table...")
                conn.execute(text("DROP TABLE IF EXISTS video_clips CASCADE"))
                conn.commit()
                logger.info("✓ Dropped old video_clips table")
            
            # Create the correct video_clips table for ad_traffic
            logger.info("Creating new video_clips table for ad_traffic...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS video_clips (
                    id VARCHAR PRIMARY KEY,
                    campaign_id VARCHAR NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    description TEXT,
                    duration FLOAT NOT NULL,
                    start_time FLOAT NOT NULL,
                    end_time FLOAT NOT NULL,
                    video_url VARCHAR NOT NULL,
                    thumbnail_url VARCHAR,
                    platform_versions JSON DEFAULT '{}',
                    suggested_caption TEXT,
                    suggested_hashtags VARCHAR[],
                    content_type VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_video_clips_campaign ON video_clips(campaign_id);"))
            
            conn.commit()
            logger.info("✓ Successfully created video_clips table for ad_traffic")
            
        except Exception as e:
            logger.error(f"Error fixing video_clips schema: {e}")
            raise

if __name__ == "__main__":
    fix_video_clips_schema() 