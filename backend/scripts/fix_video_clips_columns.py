#!/usr/bin/env python3
"""Fix missing columns in video_clips table"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def fix_video_clips_columns():
    """Add all missing columns to video_clips table"""
    
    # List of columns that should exist in video_clips table
    columns_to_check = [
        ('campaign_id', 'VARCHAR'),
        ('title', 'VARCHAR DEFAULT \'\''),
        ('description', 'TEXT'),
        ('duration', 'INTEGER'),
        ('start_time', 'INTEGER'),
        ('end_time', 'INTEGER'),
        ('video_url', 'VARCHAR'),
        ('thumbnail_url', 'VARCHAR'),
        ('platform_versions', 'JSON DEFAULT \'{}\''),
        ('suggested_caption', 'TEXT'),
        ('suggested_hashtags', 'VARCHAR[]'),
        ('content_type', 'VARCHAR'),
        ('created_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
    ]
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'video_clips'
            )
        """))
        
        if not result.scalar():
            print("Creating video_clips table...")
            with engine.begin() as trans_conn:
                trans_conn.execute(text("""
                    CREATE TABLE video_clips (
                        id VARCHAR PRIMARY KEY,
                        campaign_id VARCHAR,
                        title VARCHAR DEFAULT '',
                        description TEXT,
                        duration INTEGER,
                        start_time INTEGER,
                        end_time INTEGER,
                        video_url VARCHAR,
                        thumbnail_url VARCHAR,
                        platform_versions JSON DEFAULT '{}',
                        suggested_caption TEXT,
                        suggested_hashtags VARCHAR[],
                        content_type VARCHAR,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                print("✅ Created video_clips table")
        else:
            print("Checking video_clips columns...")
            
            for column_name, column_type in columns_to_check:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='video_clips' AND column_name='{column_name}'
                """))
                
                if result.rowcount == 0:
                    print(f"Adding {column_name} to video_clips...")
                    with engine.begin() as trans_conn:
                        try:
                            trans_conn.execute(text(f"""
                                ALTER TABLE video_clips 
                                ADD COLUMN {column_name} {column_type}
                            """))
                            print(f"✅ Added {column_name}")
                        except Exception as e:
                            print(f"⚠️  Could not add {column_name}: {e}")
                else:
                    print(f"✅ {column_name} already exists")

    print("\n✅ Video clips table fixed!")

if __name__ == "__main__":
    try:
        fix_video_clips_columns()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 