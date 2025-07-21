#!/usr/bin/env python3
"""Check scraper logs and recent activity"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
from datetime import datetime, timedelta

def check_scraper_logs():
    with engine.connect() as conn:
        print("=== CHECKING SCRAPER ACTIVITY ===\n")
        
        # 1. Check job update patterns
        print("1. Job update timeline for current IN_PROGRESS job:")
        result = conn.execute(text("""
            SELECT id, name, status, created_at, updated_at,
                   EXTRACT(EPOCH FROM (updated_at - created_at)) as seconds_active
            FROM scraping_jobs
            WHERE status = 'IN_PROGRESS'
            ORDER BY created_at DESC
            LIMIT 1
        """))
        
        for row in result:
            print(f"   Job: {row[1]} (ID: {row[0][:8]}...)")
            print(f"   Created: {row[3]}")
            print(f"   Last Updated: {row[4]}")
            print(f"   Seconds Active: {row[5]:.1f}")
            
            time_since_update = datetime.utcnow() - row[4].replace(tzinfo=None)
            print(f"   Time Since Last Update: {time_since_update}")
            
            if time_since_update > timedelta(minutes=5):
                print("   ⚠️  WARNING: Job hasn't been updated in over 5 minutes!")
                print("   This likely means the scraper has crashed or stalled.")
        
        # 2. Check contact creation pattern
        print("\n2. Recent contact creation activity:")
        result = conn.execute(text("""
            SELECT job_id, COUNT(*) as count, 
                   MIN(created_at) as first_contact,
                   MAX(created_at) as last_contact
            FROM realtor_contacts
            WHERE created_at > :time_limit
            GROUP BY job_id
            ORDER BY last_contact DESC
            LIMIT 5
        """), {"time_limit": datetime.utcnow() - timedelta(hours=1)})
        
        recent_activity = False
        for row in result:
            recent_activity = True
            print(f"   Job {row[0][:8]}...: {row[1]} contacts")
            print(f"   First: {row[2]}")
            print(f"   Last: {row[3]}")
            if row[3]:
                time_since = datetime.utcnow() - row[3].replace(tzinfo=None)
                print(f"   Time since last contact: {time_since}")
        
        if not recent_activity:
            print("   No contacts created in the last hour")
        
        # 3. Check environment
        print("\n3. Environment check:")
        print(f"   BRIGHTDATA_BROWSER_URL: {'SET' if os.getenv('BRIGHTDATA_BROWSER_URL') else 'NOT SET'}")
        print(f"   BRIGHTDATA_API_TOKEN: {'SET' if os.getenv('BRIGHTDATA_API_TOKEN') else 'NOT SET'}")
        print(f"   OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
        
        # 4. Check for any completed jobs today
        print("\n4. Jobs completed today:")
        result = conn.execute(text("""
            SELECT id, name, created_at, updated_at,
                   (SELECT COUNT(*) FROM realtor_contacts WHERE job_id = scraping_jobs.id) as contacts
            FROM scraping_jobs
            WHERE status = 'COMPLETED'
            AND created_at > :today
            ORDER BY created_at DESC
        """), {"today": datetime.utcnow() - timedelta(days=1)})
        
        completed_count = 0
        for row in result:
            completed_count += 1
            duration = row[3] - row[2]
            print(f"   {row[1]} (ID: {row[0][:8]}...)")
            print(f"   Duration: {duration}")
            print(f"   Contacts: {row[4]}")
        
        if completed_count == 0:
            print("   No jobs completed in the last 24 hours")
        
        # 5. Check for failed jobs
        print("\n5. Recent failed jobs:")
        result = conn.execute(text("""
            SELECT id, name, error_message, created_at
            FROM scraping_jobs
            WHERE status = 'FAILED'
            AND created_at > :time_limit
            ORDER BY created_at DESC
            LIMIT 5
        """), {"time_limit": datetime.utcnow() - timedelta(days=3)})
        
        failed_count = 0
        for row in result:
            failed_count += 1
            print(f"   {row[1]} (ID: {row[0][:8]}...)")
            print(f"   Created: {row[3]}")
            print(f"   Error: {row[2][:100] if row[2] else 'No error message'}...")
        
        if failed_count == 0:
            print("   No failed jobs in the last 3 days")

if __name__ == "__main__":
    check_scraper_logs() 