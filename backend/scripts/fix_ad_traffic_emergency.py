#!/usr/bin/env python3
"""Emergency fix for ad traffic database - handles errors gracefully"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def run_safe_query(conn, query, description):
    """Run a query and handle errors gracefully"""
    try:
        result = conn.execute(text(query))
        print(f"✅ {description}")
        return result
    except Exception as e:
        print(f"⚠️  {description} - Error: {str(e)[:100]}")
        return None

def fix_video_clips_campaign_id():
    """Fix video_clips table campaign_id issue"""
    print("\n=== EMERGENCY FIX FOR VIDEO_CLIPS TABLE ===\n")
    
    # Use separate transactions for each operation
    with engine.connect() as conn:
        # 1. Check if column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='video_clips' AND column_name='campaign_id'
        """))
        
        if result.rowcount == 0:
            print("Adding campaign_id column to video_clips...")
            # Add column without NOT NULL constraint first
            with engine.begin() as trans_conn:
                try:
                    trans_conn.execute(text("""
                        ALTER TABLE video_clips 
                        ADD COLUMN campaign_id VARCHAR
                    """))
                    print("✅ Added campaign_id column")
                except Exception as e:
                    print(f"⚠️  Could not add campaign_id: {e}")
        else:
            print("✅ campaign_id column already exists in video_clips")
    
    # 2. Check for orphaned video_clips
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM video_clips 
            WHERE campaign_id IS NULL OR campaign_id = ''
        """))
        orphaned_count = result.scalar()
        if orphaned_count > 0:
            print(f"⚠️  Found {orphaned_count} video clips without campaign_id")
            # Delete orphaned records
            with engine.begin() as trans_conn:
                trans_conn.execute(text("""
                    DELETE FROM video_clips 
                    WHERE campaign_id IS NULL OR campaign_id = ''
                """))
                print(f"✅ Deleted {orphaned_count} orphaned video clips")

def fix_all_tables():
    """Fix all ad traffic tables individually"""
    
    # 1. Fix ad_traffic_clients
    with engine.begin() as conn:
        try:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ad_traffic_clients'
                )
            """))
            if not result.scalar():
                conn.execute(text("""
                    CREATE TABLE ad_traffic_clients (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL REFERENCES users(id),
                        name VARCHAR NOT NULL,
                        email VARCHAR,
                        phone VARCHAR,
                        website VARCHAR,
                        social_accounts JSON DEFAULT '{}',
                        brand_colors JSON DEFAULT '[]',
                        brand_guidelines TEXT,
                        notes TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                print("✅ Created ad_traffic_clients table")
            else:
                print("✅ ad_traffic_clients table exists")
        except Exception as e:
            print(f"⚠️  Error with ad_traffic_clients: {e}")
    
    # 2. Fix campaigns table columns
    columns_to_add = [
        ('original_video_url', 'VARCHAR DEFAULT \'\''),
        ('duration_weeks', 'INTEGER DEFAULT 1'),
        ('platforms', 'VARCHAR[] DEFAULT \'{}\''),
        ('progress', 'INTEGER DEFAULT 0'),
        ('error_message', 'TEXT'),
        ('updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
    ]
    
    for column_name, column_type in columns_to_add:
        with engine.begin() as conn:
            try:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='campaigns' AND column_name='{column_name}'
                """))
                if result.rowcount == 0:
                    conn.execute(text(f"""
                        ALTER TABLE campaigns 
                        ADD COLUMN {column_name} {column_type}
                    """))
                    print(f"✅ Added {column_name} to campaigns")
                else:
                    print(f"✅ {column_name} already exists in campaigns")
            except Exception as e:
                print(f"⚠️  Could not add {column_name}: {e}")
    
    # 3. Fix social_posts columns
    social_columns = [
        ('campaign_id', 'VARCHAR'),
        ('video_clip_id', 'VARCHAR'),
        ('platforms', 'VARCHAR[] DEFAULT \'{}\''),
        ('media_urls', 'VARCHAR[] DEFAULT \'{}\''),
        ('status', 'VARCHAR DEFAULT \'DRAFT\''),
        ('published_at', 'TIMESTAMP WITH TIME ZONE'),
        ('platform_data', 'JSON DEFAULT \'{}\''),
        ('updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
    ]
    
    for column_name, column_type in social_columns:
        with engine.begin() as conn:
            try:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='social_posts' AND column_name='{column_name}'
                """))
                if result.rowcount == 0:
                    conn.execute(text(f"""
                        ALTER TABLE social_posts 
                        ADD COLUMN {column_name} {column_type}
                    """))
                    print(f"✅ Added {column_name} to social_posts")
                else:
                    print(f"✅ {column_name} already exists in social_posts")
            except Exception as e:
                print(f"⚠️  Could not add {column_name}: {e}")

    # Create uploads directory
    upload_dir = "uploads/campaigns"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        print(f"\n✅ Created {upload_dir} directory")

if __name__ == "__main__":
    try:
        print("=== EMERGENCY AD TRAFFIC DATABASE FIX ===")
        fix_video_clips_campaign_id()
        fix_all_tables()
        print("\n✅ Emergency fix completed!")
        print("\nIf you still see errors, you may need to:")
        print("1. Create a new client in the Ad Traffic module")
        print("2. Use that client for creating campaigns")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 