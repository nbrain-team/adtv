#!/usr/bin/env python3
"""Monitor scraper progress in real-time"""
import os
import sys
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

def monitor_scraper():
    """Monitor scraper progress"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Clear screen
            os.system('clear' if os.name != 'nt' else 'cls')
            
            while True:
                # Get latest IN_PROGRESS job
                cur.execute("""
                    SELECT id, name, status, created_at, updated_at,
                           EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' - updated_at)) as seconds_since_update
                    FROM scraping_jobs
                    WHERE status = 'IN_PROGRESS'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                job = cur.fetchone()
                
                if not job:
                    print("\n❌ No active scraping job found")
                    break
                
                # Get contact count
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM realtor_contacts
                    WHERE scraping_job_id = %s
                """, (job['id'],))
                contact_count = cur.fetchone()['count']
                
                # Get last few contacts
                cur.execute("""
                    SELECT name, created_at
                    FROM realtor_contacts
                    WHERE scraping_job_id = %s
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (job['id'],))
                recent_contacts = cur.fetchall()
                
                # Clear and display
                os.system('clear' if os.name != 'nt' else 'cls')
                print("=" * 60)
                print("REALTOR SCRAPER MONITOR - LIVE")
                print("=" * 60)
                print(f"Job: {job['name']} (ID: {job['id'][:8]}...)")
                print(f"Status: {job['status']}")
                print(f"Started: {job['created_at']}")
                print(f"Last Update: {job['updated_at']}")
                print(f"Time Since Update: {int(job['seconds_since_update'])} seconds")
                print(f"\n📊 CONTACTS SAVED: {contact_count}")
                
                if job['seconds_since_update'] > 300:  # 5 minutes
                    print("\n⚠️  WARNING: Job hasn't updated in over 5 minutes!")
                
                if recent_contacts:
                    print("\n🆕 Recent Contacts:")
                    for contact in recent_contacts:
                        print(f"   - {contact['name']} ({contact['created_at']})")
                
                print("\n[Press Ctrl+C to exit]")
                time.sleep(5)  # Refresh every 5 seconds
                
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
    finally:
        conn.close()

if __name__ == "__main__":
    monitor_scraper() 