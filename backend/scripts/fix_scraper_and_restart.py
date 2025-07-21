#!/usr/bin/env python3
"""Fix scraper batch saving issue and restart"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def fix_and_restart():
    """Fix current job and provide restart instructions"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("=== FIXING SCRAPER BATCH ISSUE ===\n")
            
            # Check current job
            cur.execute("""
                SELECT id, name, status, url, created_at, updated_at,
                       (SELECT COUNT(*) FROM realtor_contacts WHERE scraping_job_id = scraping_jobs.id) as contact_count
                FROM scraping_jobs
                WHERE status = 'IN_PROGRESS'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            job = cur.fetchone()
            
            if job:
                print(f"Current job: {job['name']} ({job['id'][:8]}...)")
                print(f"URL: {job['url']}")
                print(f"Contacts saved: {job['contact_count']}")
                print(f"Status: {job['status']}")
                
                if job['contact_count'] == 0:
                    print("\n⚠️  Job found profiles but didn't save them due to batch size mismatch")
                    print("Marking job as FAILED...")
                    
                    cur.execute("""
                        UPDATE scraping_jobs 
                        SET status = 'FAILED', 
                            error_message = 'Batch size mismatch - profiles found but not saved. Fixed in next run.',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (job['id'],))
                    conn.commit()
                    print("✓ Job marked as FAILED")
                else:
                    print(f"\n✓ Job has {job['contact_count']} contacts saved")
            else:
                print("No active job found")
            
            print("\n=== NEXT STEPS ===")
            print("1. The batch size issue has been fixed (now 20 instead of 50)")
            print("2. Deploy the latest code to Render:")
            print("   - Go to Render Dashboard")
            print("   - Click 'Manual Deploy' → 'Deploy latest commit'")
            print("3. After deployment completes, start a new scraper job")
            print("4. The new job will save contacts every 20 profiles")
            
            print("\n=== VERIFICATION ===")
            print("After starting a new job, you can monitor it with:")
            print("  python scripts/monitor_scraper_live.py")
            print("Or check status with:")
            print("  python scripts/debug_realtor_scraper.py")
            
    finally:
        conn.close()

if __name__ == "__main__":
    fix_and_restart() 