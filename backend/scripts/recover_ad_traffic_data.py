#!/usr/bin/env python3
"""Recover Ad Traffic data from old table structure"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from core.database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recover_ad_traffic_data():
    """Recover Ad Traffic data from old tables to new structure"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        
        print("\n=== Ad Traffic Data Recovery ===\n")
        
        # First ensure the new tables exist
        if 'ad_traffic_clients' not in all_tables:
            print("❌ ad_traffic_clients table doesn't exist! Run migration scripts first.")
            return
            
        if 'ad_traffic_campaigns' not in all_tables:
            print("❌ ad_traffic_campaigns table doesn't exist! Run migration scripts first.")
            return
            
        # Check if there's data in the old campaigns table
        if 'campaigns' in all_tables:
            columns = [col['name'] for col in inspector.get_columns('campaigns')]
            
            if 'original_video_url' in columns:
                print("Found old ad_traffic campaigns data!")
                
                # Count campaigns to migrate
                result = conn.execute(text("SELECT COUNT(*) FROM campaigns WHERE original_video_url IS NOT NULL"))
                old_count = result.scalar()
                
                if old_count > 0:
                    print(f"\n🔄 Migrating {old_count} campaigns...")
                    
                    # First, check if the campaigns already exist in new table
                    result = conn.execute(text("SELECT COUNT(*) FROM ad_traffic_campaigns"))
                    new_count = result.scalar()
                    
                    if new_count > 0:
                        print(f"⚠️  ad_traffic_campaigns already has {new_count} records.")
                        response = input("Do you want to continue and potentially create duplicates? (y/N): ")
                        if response.lower() != 'y':
                            print("Migration cancelled.")
                            return
                    
                    # Migrate the campaigns
                    try:
                        conn.execute(text("""
                            INSERT INTO ad_traffic_campaigns (
                                id, client_id, name, original_video_url, duration_weeks,
                                platforms, status, progress, error_message, created_at, updated_at
                            )
                            SELECT 
                                id, client_id, name, original_video_url, duration_weeks,
                                platforms, status, progress, error_message, created_at, updated_at
                            FROM campaigns
                            WHERE original_video_url IS NOT NULL
                            ON CONFLICT (id) DO NOTHING
                        """))
                        conn.commit()
                        
                        # Check how many were migrated
                        result = conn.execute(text("SELECT COUNT(*) FROM ad_traffic_campaigns"))
                        final_count = result.scalar()
                        migrated = final_count - new_count
                        
                        print(f"✅ Successfully migrated {migrated} campaigns!")
                        
                        # Also migrate related video_clips and social_posts if they reference the old campaigns
                        if 'video_clips' in all_tables:
                            conn.execute(text("""
                                UPDATE video_clips 
                                SET campaign_id = campaign_id
                                WHERE campaign_id IN (
                                    SELECT id FROM ad_traffic_campaigns
                                )
                            """))
                            conn.commit()
                            print("✅ Updated video_clips references")
                            
                        if 'social_posts' in all_tables:
                            conn.execute(text("""
                                UPDATE social_posts 
                                SET campaign_id = campaign_id
                                WHERE campaign_id IN (
                                    SELECT id FROM ad_traffic_campaigns
                                )
                            """))
                            conn.commit()
                            print("✅ Updated social_posts references")
                            
                    except Exception as e:
                        conn.rollback()
                        print(f"❌ Error during migration: {e}")
                        return
                else:
                    print("No ad traffic campaigns found in old table.")
            else:
                print("✅ Old campaigns table is for Event Campaign Builder, not ad traffic.")
        else:
            print("No old campaigns table found.")
            
        # Final check
        print("\n--- Final Status ---")
        result = conn.execute(text("SELECT COUNT(*) FROM ad_traffic_clients"))
        print(f"ad_traffic_clients: {result.scalar()} records")
        
        result = conn.execute(text("SELECT COUNT(*) FROM ad_traffic_campaigns"))
        print(f"ad_traffic_campaigns: {result.scalar()} records")
        
        result = conn.execute(text("SELECT COUNT(*) FROM video_clips"))
        print(f"video_clips: {result.scalar()} records")
        
        result = conn.execute(text("SELECT COUNT(*) FROM social_posts"))
        print(f"social_posts: {result.scalar()} records")

if __name__ == "__main__":
    recover_ad_traffic_data()
    print("\n✅ Recovery complete!") 