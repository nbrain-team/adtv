#!/usr/bin/env python3
"""Diagnose scraper issues"""
import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def diagnose_scraper():
    """Check for common scraper issues"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("=== SCRAPER DIAGNOSTICS ===\n")
            
            # Get latest job
            cur.execute("""
                SELECT id, name, status, url, created_at, updated_at,
                       EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' - updated_at)) as seconds_since_update
                FROM scraping_jobs
                WHERE status = 'IN_PROGRESS'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            job = cur.fetchone()
            
            if not job:
                print("❌ No active job found")
                return
            
            print(f"Current Job: {job['name']} ({job['id'][:8]}...)")
            print(f"URL: {job['url']}")
            print(f"Status: {job['status']}")
            print(f"Time since last update: {int(job['seconds_since_update'])} seconds")
            
            # Check contacts
            cur.execute("""
                SELECT COUNT(*) as count
                FROM realtor_contacts
                WHERE scraping_job_id = %s
            """, (job['id'],))
            contacts = cur.fetchone()['count']
            print(f"Contacts saved: {contacts}")
            
            print("\n=== POSSIBLE ISSUES ===")
            
            if contacts == 0 and job['seconds_since_update'] > 60:
                print("⚠️  No contacts saved after 1+ minute. Possible causes:")
                print("   1. Page structure changed - selectors not finding profiles")
                print("   2. Site blocking the scraper (captcha, rate limit)")
                print("   3. Network/proxy issues")
                print("   4. Scraper crashed but job status not updated")
                
            print("\n=== RECOMMENDATIONS ===")
            print("1. Check Render logs for:")
            print("   - 'Found X agent profiles' messages")
            print("   - Error messages or exceptions")
            print("   - 'SCRAPING PAGE X' messages")
            print("\n2. If no profile messages, the scraper isn't finding data")
            print("3. Consider failing this job and trying a different URL")
            print("\n4. To fail this job, run: python scripts/fail_stuck_job.py")
            
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose_scraper() 