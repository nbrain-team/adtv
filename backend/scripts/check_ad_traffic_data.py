#!/usr/bin/env python3
"""Check and recover Ad Traffic data"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ad_traffic_data():
    """Check for Ad Traffic data in various tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        
        print("\n=== Checking Ad Traffic Data ===\n")
        print(f"All tables in database: {all_tables}\n")
        
        # Check for ad_traffic_clients
        if 'ad_traffic_clients' in all_tables:
            result = conn.execute(text("SELECT COUNT(*) FROM ad_traffic_clients"))
            count = result.scalar()
            print(f"✅ ad_traffic_clients table exists with {count} records")
            
            if count > 0:
                result = conn.execute(text("SELECT id, name, created_at FROM ad_traffic_clients ORDER BY created_at DESC LIMIT 5"))
                print("\nRecent clients:")
                for row in result:
                    print(f"  - {row.name} (ID: {row.id}, Created: {row.created_at})")
        else:
            print("❌ ad_traffic_clients table NOT found")
            
        # Check for campaigns (both old and new names)
        print("\n--- Checking Campaigns ---")
        
        if 'ad_traffic_campaigns' in all_tables:
            result = conn.execute(text("SELECT COUNT(*) FROM ad_traffic_campaigns"))
            count = result.scalar()
            print(f"✅ ad_traffic_campaigns table exists with {count} records")
            
            if count > 0:
                result = conn.execute(text("""
                    SELECT c.id, c.name, c.status, c.created_at, cl.name as client_name 
                    FROM ad_traffic_campaigns c 
                    LEFT JOIN ad_traffic_clients cl ON c.client_id = cl.id 
                    ORDER BY c.created_at DESC LIMIT 5
                """))
                print("\nRecent campaigns:")
                for row in result:
                    print(f"  - {row.name} for {row.client_name} (Status: {row.status}, Created: {row.created_at})")
        else:
            print("❌ ad_traffic_campaigns table NOT found")
            
        # Check for old campaigns table
        if 'campaigns' in all_tables:
            # Check if it has original_video_url column (ad traffic) or not (event builder)
            columns = [col['name'] for col in inspector.get_columns('campaigns')]
            
            if 'original_video_url' in columns:
                print("\n⚠️  Found OLD ad_traffic campaigns table!")
                result = conn.execute(text("SELECT COUNT(*) FROM campaigns WHERE original_video_url IS NOT NULL"))
                count = result.scalar()
                print(f"   Contains {count} ad traffic campaigns")
                
                if count > 0:
                    print("\n   🔄 These campaigns need to be migrated to ad_traffic_campaigns!")
                    result = conn.execute(text("""
                        SELECT id, name, status, created_at 
                        FROM campaigns 
                        WHERE original_video_url IS NOT NULL
                        ORDER BY created_at DESC LIMIT 5
                    """))
                    print("\n   Recent old campaigns:")
                    for row in result:
                        print(f"     - {row.name} (Status: {row.status}, Created: {row.created_at})")
            else:
                print("\n✅ campaigns table exists but is for Event Campaign Builder (not ad traffic)")
                
        # Check for video clips
        print("\n--- Checking Video Clips ---")
        if 'video_clips' in all_tables:
            result = conn.execute(text("SELECT COUNT(*) FROM video_clips"))
            count = result.scalar()
            print(f"✅ video_clips table exists with {count} records")
        else:
            print("❌ video_clips table NOT found")
            
        # Check for social posts
        print("\n--- Checking Social Posts ---")
        if 'social_posts' in all_tables:
            result = conn.execute(text("SELECT COUNT(*) FROM social_posts"))
            count = result.scalar()
            print(f"✅ social_posts table exists with {count} records")
        else:
            print("❌ social_posts table NOT found")

if __name__ == "__main__":
    check_ad_traffic_data()
    print("\n✅ Check complete!") 