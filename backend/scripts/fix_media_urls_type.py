#!/usr/bin/env python3
"""
Fix media_urls in social_posts table - convert from dict to list
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL environment variable not set")
    sys.exit(1)

def fix_media_urls():
    """Convert media_urls from dict to list where needed"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("=== Fixing media_urls in social_posts ===")
        
        try:
            # First, check for posts with dict media_urls
            result = conn.execute(text("""
                SELECT id, media_urls 
                FROM social_posts 
                WHERE media_urls IS NOT NULL
                AND jsonb_typeof(media_urls::jsonb) = 'object'
            """))
            
            posts_to_fix = result.fetchall()
            print(f"Found {len(posts_to_fix)} posts with dict media_urls")
            
            # Fix each post
            fixed_count = 0
            for post_id, media_urls in posts_to_fix:
                try:
                    # Convert dict to list
                    if isinstance(media_urls, str):
                        media_dict = json.loads(media_urls)
                    else:
                        media_dict = media_urls
                    
                    # Extract values from dict to create list
                    if isinstance(media_dict, dict):
                        # Get values sorted by key to maintain order
                        media_list = [v for k, v in sorted(media_dict.items()) if v]
                        
                        # Update the post
                        conn.execute(text("""
                            UPDATE social_posts 
                            SET media_urls = :media_urls
                            WHERE id = :post_id
                        """), {"media_urls": json.dumps(media_list), "post_id": post_id})
                        
                        fixed_count += 1
                        print(f"Fixed post {post_id}: {media_dict} -> {media_list}")
                except Exception as e:
                    print(f"Error fixing post {post_id}: {e}")
            
            conn.commit()
            print(f"\n✓ Fixed {fixed_count} posts")
            
            # Check if there are more to fix
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM social_posts 
                WHERE media_urls IS NOT NULL
                AND jsonb_typeof(media_urls::jsonb) = 'object'
            """))
            remaining = result.scalar()
            
            if remaining > 0:
                print(f"Note: {remaining} more posts need fixing. Run this script again.")
            else:
                print("✓ All posts have been fixed!")
                
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    fix_media_urls() 