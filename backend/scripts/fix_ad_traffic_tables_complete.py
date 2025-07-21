#!/usr/bin/env python3
"""Comprehensive fix for all ad traffic database issues"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def fix_all_ad_traffic_issues():
    """Fix all database issues for ad traffic module"""
    
    with engine.begin() as conn:
        print("=== FIXING AD TRAFFIC DATABASE ISSUES ===\n")
        
        # 1. First ensure ad_traffic_clients table exists
        print("1. Checking ad_traffic_clients table...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'ad_traffic_clients'
            )
        """))
        if not result.scalar():
            print("Creating ad_traffic_clients table...")
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
        else:
            # Add social_accounts column if missing
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='ad_traffic_clients' AND column_name='social_accounts'
            """))
            if result.rowcount == 0:
                print("Adding social_accounts to ad_traffic_clients...")
                conn.execute(text("""
                    ALTER TABLE ad_traffic_clients 
                    ADD COLUMN social_accounts JSON DEFAULT '{}'
                """))
        
        # 2. Ensure campaigns table exists with all columns
        print("\n2. Checking campaigns table...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'campaigns'
            )
        """))
        if not result.scalar():
            print("Creating campaigns table...")
            conn.execute(text("""
                CREATE TABLE campaigns (
                    id VARCHAR PRIMARY KEY,
                    client_id VARCHAR NOT NULL REFERENCES ad_traffic_clients(id),
                    name VARCHAR NOT NULL,
                    original_video_url VARCHAR NOT NULL,
                    duration_weeks INTEGER NOT NULL DEFAULT 1,
                    platforms VARCHAR[] NOT NULL DEFAULT '{}',
                    status VARCHAR NOT NULL DEFAULT 'PENDING',
                    progress INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
        else:
            # Add missing columns
            columns_to_add = [
                ('original_video_url', 'VARCHAR NOT NULL DEFAULT \'\''),
                ('duration_weeks', 'INTEGER NOT NULL DEFAULT 1'),
                ('platforms', 'VARCHAR[] NOT NULL DEFAULT \'{}\''),
                ('progress', 'INTEGER DEFAULT 0'),
                ('error_message', 'TEXT'),
                ('updated_at', 'TIMESTAMP WITH TIME ZONE')
            ]
            
            for column_name, column_type in columns_to_add:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='campaigns' AND column_name='{column_name}'
                """))
                if result.rowcount == 0:
                    print(f"Adding {column_name} to campaigns...")
                    conn.execute(text(f"""
                        ALTER TABLE campaigns 
                        ADD COLUMN {column_name} {column_type}
                    """))
        
        # 3. Ensure video_clips table exists with campaign_id
        print("\n3. Checking video_clips table...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'video_clips'
            )
        """))
        if not result.scalar():
            print("Creating video_clips table...")
            conn.execute(text("""
                CREATE TABLE video_clips (
                    id VARCHAR PRIMARY KEY,
                    campaign_id VARCHAR NOT NULL REFERENCES campaigns(id),
                    title VARCHAR NOT NULL,
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
        else:
            # Add campaign_id if missing
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='video_clips' AND column_name='campaign_id'
            """))
            if result.rowcount == 0:
                print("Adding campaign_id to video_clips...")
                conn.execute(text("""
                    ALTER TABLE video_clips 
                    ADD COLUMN campaign_id VARCHAR NOT NULL DEFAULT ''
                """))
                # Try to add foreign key constraint
                try:
                    conn.execute(text("""
                        ALTER TABLE video_clips 
                        ADD CONSTRAINT fk_video_clips_campaign 
                        FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                    """))
                except:
                    print("Warning: Could not add foreign key constraint for video_clips.campaign_id")
        
        # 4. Ensure social_posts table exists with all columns
        print("\n4. Checking social_posts table...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'social_posts'
            )
        """))
        if not result.scalar():
            print("Creating social_posts table...")
            conn.execute(text("""
                CREATE TABLE social_posts (
                    id VARCHAR PRIMARY KEY,
                    client_id VARCHAR NOT NULL REFERENCES ad_traffic_clients(id),
                    campaign_id VARCHAR REFERENCES campaigns(id),
                    video_clip_id VARCHAR REFERENCES video_clips(id),
                    content TEXT NOT NULL,
                    platforms VARCHAR[] NOT NULL DEFAULT '{}',
                    media_urls VARCHAR[] DEFAULT '{}',
                    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'DRAFT',
                    published_at TIMESTAMP WITH TIME ZONE,
                    platform_data JSON DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
        else:
            # Add missing columns
            columns_to_add = [
                ('campaign_id', 'VARCHAR'),
                ('video_clip_id', 'VARCHAR'),
                ('platforms', 'VARCHAR[] NOT NULL DEFAULT \'{}\''),
                ('media_urls', 'VARCHAR[] DEFAULT \'{}\''),
                ('status', 'VARCHAR NOT NULL DEFAULT \'DRAFT\''),
                ('published_at', 'TIMESTAMP WITH TIME ZONE'),
                ('platform_data', 'JSON DEFAULT \'{}\''),
                ('updated_at', 'TIMESTAMP WITH TIME ZONE')
            ]
            
            for column_name, column_type in columns_to_add:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='social_posts' AND column_name='{column_name}'
                """))
                if result.rowcount == 0:
                    print(f"Adding {column_name} to social_posts...")
                    conn.execute(text(f"""
                        ALTER TABLE social_posts 
                        ADD COLUMN {column_name} {column_type}
                    """))
        
        # 5. Create uploads directory
        upload_dir = "uploads/campaigns"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print(f"\n5. Created {upload_dir} directory for video uploads")
        
        print("\n✅ All ad traffic database issues have been fixed!")
        print("\nNOTE: If you still see foreign key errors, you may need to:")
        print("1. Delete any orphaned records")
        print("2. Or temporarily disable foreign key checks")

if __name__ == "__main__":
    try:
        fix_all_ad_traffic_issues()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 