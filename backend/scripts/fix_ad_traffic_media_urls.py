#!/usr/bin/env python3
"""
Fix media_urls field in social_posts table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from core.database import DATABASE_URL
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_media_urls():
    """Fix media_urls field from array to JSON dict"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            inspector = inspect(engine)
            
            # Check if social_posts table exists
            if 'social_posts' not in inspector.get_table_names():
                logger.warning("social_posts table not found")
                return
            
            # Check current data type of media_urls
            columns = inspector.get_columns('social_posts')
            media_urls_col = next((col for col in columns if col['name'] == 'media_urls'), None)
            
            if not media_urls_col:
                logger.info("media_urls column not found, adding it...")
                conn.execute(text("""
                    ALTER TABLE social_posts 
                    ADD COLUMN IF NOT EXISTS media_urls JSON DEFAULT '{}'::json
                """))
                conn.commit()
                return
            
            # Check if it's already JSON
            logger.info(f"Current media_urls type: {media_urls_col['type']}")
            
            # Get posts with array media_urls
            result = conn.execute(text("""
                SELECT id, media_urls 
                FROM social_posts 
                WHERE media_urls IS NOT NULL
                LIMIT 5
            """))
            
            sample_rows = result.fetchall()
            if sample_rows:
                logger.info(f"Sample media_urls data: {sample_rows[0].media_urls}")
                
                # Check if it's an array that needs conversion
                if isinstance(sample_rows[0].media_urls, list):
                    logger.info("Converting media_urls from array to JSON dict...")
                    
                    # Convert empty arrays to empty dicts
                    conn.execute(text("""
                        UPDATE social_posts 
                        SET media_urls = '{}'::json 
                        WHERE media_urls = '[]'::json OR media_urls::text = '[]'
                    """))
                    conn.commit()
                    
                    # For non-empty arrays, convert to dict with platform keys
                    result = conn.execute(text("""
                        SELECT id, media_urls, platforms 
                        FROM social_posts 
                        WHERE media_urls IS NOT NULL 
                        AND media_urls::text != '{}' 
                        AND media_urls::text != '[]'
                    """))
                    
                    for row in result:
                        if isinstance(row.media_urls, list) and len(row.media_urls) > 0:
                            # Convert array to dict with platform keys
                            media_dict = {}
                            platforms = row.platforms if row.platforms else []
                            
                            for i, url in enumerate(row.media_urls):
                                if i < len(platforms):
                                    media_dict[platforms[i]] = url
                                else:
                                    media_dict[f"platform_{i}"] = url
                            
                            conn.execute(text("""
                                UPDATE social_posts 
                                SET media_urls = :media_dict 
                                WHERE id = :id
                            """), {"media_dict": json.dumps(media_dict), "id": row.id})
                    
                    conn.commit()
                    logger.info("✅ Converted array media_urls to JSON dict")
                else:
                    logger.info("media_urls already in correct format")
            else:
                logger.info("No posts with media_urls found")
            
            # Verify the fix
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN media_urls IS NULL THEN 1 END) as null_count,
                       COUNT(CASE WHEN media_urls::text = '{}' THEN 1 END) as empty_dict_count,
                       COUNT(CASE WHEN media_urls::text = '[]' THEN 1 END) as empty_array_count
                FROM social_posts
            """))
            
            stats = result.fetchone()
            logger.info(f"\nFinal stats:")
            logger.info(f"  Total posts: {stats.total}")
            logger.info(f"  NULL media_urls: {stats.null_count}")
            logger.info(f"  Empty dict: {stats.empty_dict_count}")
            logger.info(f"  Empty array (should be 0): {stats.empty_array_count}")
            
        except Exception as e:
            logger.error(f"Error fixing media_urls: {e}")
            raise

if __name__ == "__main__":
    fix_media_urls()
    print("\n✅ Media URLs fix completed!") 