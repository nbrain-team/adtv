#!/usr/bin/env python3
"""Debug script to check campaigns and posts in the database"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
from datetime import datetime

def debug_campaigns():
    with engine.connect() as conn:
        print("=== DEBUGGING CAMPAIGNS AND POSTS ===\n")
        
        # 1. Check all campaigns
        print("1. All campaigns in database:")
        result = conn.execute(text("""
            SELECT c.id, c.name, c.status, c.progress, c.created_at, 
                   ac.name as client_name
            FROM campaigns c
            JOIN ad_traffic_clients ac ON c.client_id = ac.id
            ORDER BY c.created_at DESC
        """))
        
        campaigns = []
        for row in result:
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'status': row[2],
                'progress': row[3],
                'created_at': row[4],
                'client_name': row[5]
            })
            print(f"   - {row[1]} (ID: {row[0][:8]}...)")
            print(f"     Status: {row[2]}, Progress: {row[3]}%")
            print(f"     Client: {row[5]}")
            print(f"     Created: {row[4]}")
        
        print(f"\nTotal campaigns: {len(campaigns)}")
        
        # 2. Check video clips
        print("\n2. Video clips by campaign:")
        for campaign in campaigns:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM video_clips 
                WHERE campaign_id = :campaign_id
            """), {"campaign_id": campaign['id']})
            
            clip_count = result.scalar()
            print(f"   - {campaign['name']}: {clip_count} clips")
        
        # 3. Check social posts
        print("\n3. Social posts by campaign:")
        for campaign in campaigns:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM social_posts 
                WHERE campaign_id = :campaign_id
            """), {"campaign_id": campaign['id']})
            
            post_count = result.scalar()
            print(f"   - {campaign['name']}: {post_count} posts")
            
            if post_count > 0:
                # Show some post details
                result = conn.execute(text("""
                    SELECT id, content, scheduled_time, status
                    FROM social_posts 
                    WHERE campaign_id = :campaign_id
                    ORDER BY scheduled_time
                    LIMIT 3
                """), {"campaign_id": campaign['id']})
                
                print("     Sample posts:")
                for post in result:
                    print(f"       - {post[3]} on {post[2]}: {post[1][:50]}...")
        
        # 4. Check for orphaned posts
        print("\n4. Checking for orphaned posts (no campaign):")
        result = conn.execute(text("""
            SELECT COUNT(*) FROM social_posts 
            WHERE campaign_id IS NULL
        """))
        orphaned = result.scalar()
        print(f"   Orphaned posts: {orphaned}")
        
        # 5. Check table structure
        print("\n5. Checking social_posts table structure:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'social_posts'
            ORDER BY ordinal_position
        """))
        
        print("   Columns:")
        for col in result:
            print(f"     - {col[0]}: {col[1]} (nullable: {col[2]})")

if __name__ == "__main__":
    debug_campaigns() 