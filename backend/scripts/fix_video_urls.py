#!/usr/bin/env python3
"""
Fix video URLs in existing campaigns and video clips
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def fix_video_urls():
    """Fix video URLs to use proper URL paths instead of file paths"""
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Get all video clips with file paths instead of URLs
            result = conn.execute(text("""
                SELECT id, video_url 
                FROM video_clips 
                WHERE video_url LIKE '%uploads/campaigns/%'
                AND video_url NOT LIKE '/%'
            """))
            
            clips_to_fix = result.fetchall()
            print(f"Found {len(clips_to_fix)} video clips to fix")
            
            # Fix each video clip
            for clip_id, video_url in clips_to_fix:
                # Convert file path to URL path
                new_url = f"/{video_url}" if not video_url.startswith('/') else video_url
                
                conn.execute(text("""
                    UPDATE video_clips 
                    SET video_url = :new_url 
                    WHERE id = :clip_id
                """), {"new_url": new_url, "clip_id": clip_id})
                
                print(f"Fixed video clip {clip_id}: {video_url} -> {new_url}")
            
            # Also fix campaigns original_video_url
            result = conn.execute(text("""
                SELECT id, original_video_url 
                FROM campaigns 
                WHERE original_video_url LIKE '%uploads/campaigns/%'
                AND original_video_url NOT LIKE '/%'
            """))
            
            campaigns_to_fix = result.fetchall()
            print(f"\nFound {len(campaigns_to_fix)} campaigns to fix")
            
            for campaign_id, video_url in campaigns_to_fix:
                # Convert file path to URL path
                new_url = f"/{video_url}" if not video_url.startswith('/') else video_url
                
                conn.execute(text("""
                    UPDATE campaigns 
                    SET original_video_url = :new_url 
                    WHERE id = :campaign_id
                """), {"new_url": new_url, "campaign_id": campaign_id})
                
                print(f"Fixed campaign {campaign_id}: {video_url} -> {new_url}")
            
            trans.commit()
            print("\n✅ All video URLs fixed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error fixing video URLs: {e}")
            raise

if __name__ == "__main__":
    fix_video_urls() 