"""
Migration script to add video processing tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine

def add_video_processing_tables():
    """Add the video_processing_jobs and video_clips tables"""
    
    with engine.connect() as conn:
        # Create video_processing_jobs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS video_processing_jobs (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id),
                filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                platforms JSON NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create video_clips table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS video_clips (
                id VARCHAR PRIMARY KEY,
                job_id VARCHAR NOT NULL REFERENCES video_processing_jobs(id) ON DELETE CASCADE,
                title VARCHAR NOT NULL,
                description TEXT,
                duration FLOAT NOT NULL,
                start_time FLOAT NOT NULL,
                end_time FLOAT NOT NULL,
                platform VARCHAR NOT NULL,
                file_path VARCHAR,
                thumbnail_path VARCHAR,
                clip_metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_video_jobs_user ON video_processing_jobs(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_video_clips_job ON video_clips(job_id);"))
        
        conn.commit()
        print("✓ Successfully added video processing tables")

if __name__ == "__main__":
    add_video_processing_tables() 