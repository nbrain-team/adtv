#!/usr/bin/env python3
"""Fix all missing columns in ad traffic tables"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def fix_ad_traffic_columns():
    """Add all missing columns to ad traffic tables"""
    
    with engine.begin() as conn:
        # Fix social_posts table
        print("Checking social_posts table...")
        
        # Add campaign_id if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='social_posts' AND column_name='campaign_id'
        """))
        if result.rowcount == 0:
            print("Adding campaign_id to social_posts...")
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN campaign_id VARCHAR
            """))
            # Add foreign key constraint
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD CONSTRAINT fk_social_posts_campaign 
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            """))
        
        # Add video_clip_id if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='social_posts' AND column_name='video_clip_id'
        """))
        if result.rowcount == 0:
            print("Adding video_clip_id to social_posts...")
            conn.execute(text("""
                ALTER TABLE social_posts 
                ADD COLUMN video_clip_id VARCHAR
            """))
        
        # Fix campaigns table
        print("\nChecking campaigns table...")
        
        # Add original_video_url if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='original_video_url'
        """))
        if result.rowcount == 0:
            print("Adding original_video_url to campaigns...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN original_video_url VARCHAR NOT NULL DEFAULT ''
            """))
        
        # Add duration_weeks if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='duration_weeks'
        """))
        if result.rowcount == 0:
            print("Adding duration_weeks to campaigns...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN duration_weeks INTEGER NOT NULL DEFAULT 1
            """))
        
        # Add platforms if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='platforms'
        """))
        if result.rowcount == 0:
            print("Adding platforms to campaigns...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN platforms VARCHAR[] NOT NULL DEFAULT '{}'
            """))
        
        # Add progress if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='progress'
        """))
        if result.rowcount == 0:
            print("Adding progress to campaigns...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN progress INTEGER DEFAULT 0
            """))
        
        # Add error_message if missing
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='error_message'
        """))
        if result.rowcount == 0:
            print("Adding error_message to campaigns...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN error_message TEXT
            """))
        
        # Check if uploads directory exists
        upload_dir = "uploads/campaigns"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print(f"\n✅ Created {upload_dir} directory for video uploads")
        
        print("\n✅ All ad traffic columns have been fixed!")

if __name__ == "__main__":
    try:
        fix_ad_traffic_columns()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1) 