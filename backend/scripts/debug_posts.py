#!/usr/bin/env python3
"""
Debug posts to check their data structure
"""
import os
import sys
from sqlalchemy import create_engine, text
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL environment variable not set")
    sys.exit(1)

def debug_posts():
    """Check posts data structure"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("=== Debugging Social Posts ===")
        
        # Get a few posts
        result = conn.execute(text("""
            SELECT id, content, platforms, media_urls, video_clip_id, status, created_at
            FROM social_posts
            ORDER BY created_at DESC
            LIMIT 5
        """))
        
        posts = result.fetchall()
        print(f"\nFound {len(posts)} recent posts:")
        
        for i, (post_id, content, platforms, media_urls, video_clip_id, status, created_at) in enumerate(posts):
            print(f"\n--- Post {i+1} ---")
            print(f"ID: {post_id}")
            print(f"Content: {content[:50]}...")
            print(f"Status: {status}")
            print(f"Platforms type: {type(platforms)}")
            print(f"Platforms: {platforms}")
            print(f"Media URLs type: {type(media_urls)}")
            print(f"Media URLs: {media_urls}")
            print(f"Video Clip ID: {video_clip_id}")
            print(f"Created: {created_at}")
            
            # Check if media_urls needs fixing
            if media_urls and isinstance(media_urls, dict) and not isinstance(media_urls, list):
                print("⚠️  Media URLs is a dict, should be a list!")

if __name__ == "__main__":
    debug_posts() 