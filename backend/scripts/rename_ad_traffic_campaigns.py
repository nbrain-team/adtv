#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database import engine

def rename_ad_traffic_campaigns():
    """Rename campaigns table to ad_traffic_campaigns if it exists"""
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if old campaigns table exists
            if 'campaigns' in inspector.get_table_names():
                # Check if it's the ad_traffic campaigns table by looking for specific columns
                columns = [col['name'] for col in inspector.get_columns('campaigns')]
                
                # If it has 'original_video_url', it's the ad_traffic table
                if 'original_video_url' in columns:
                    print("Found ad_traffic campaigns table, renaming...")
                    
                    # Check if new table already exists
                    if 'ad_traffic_campaigns' not in inspector.get_table_names():
                        conn.execute(text('ALTER TABLE campaigns RENAME TO ad_traffic_campaigns'))
                        conn.commit()
                        print("✅ Successfully renamed campaigns to ad_traffic_campaigns")
                    else:
                        print("⚠️  ad_traffic_campaigns table already exists, skipping rename")
                else:
                    print("ℹ️  campaigns table exists but appears to be for Event Campaign Builder")
            else:
                print("ℹ️  No campaigns table found")
                
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        # Don't raise - allow the app to start even if migration fails

if __name__ == "__main__":
    rename_ad_traffic_campaigns() 