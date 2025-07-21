#!/usr/bin/env python3
"""Force batch processor to save accumulated profiles"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def check_batch_status():
    """Check if batch processor is accumulating data"""
    from realtor_importer import tasks
    
    print(f"=== BATCH PROCESSOR STATUS ===")
    print(f"Current BATCH_SIZE setting: {tasks.BATCH_SIZE}")
    print(f"Expected: 20")
    
    # Check if there's a pending batch in memory
    if hasattr(tasks, '_current_batch'):
        print(f"\nPending batch size: {len(tasks._current_batch)}")
    else:
        print("\nNo pending batch found in memory")
    
    # Check database for current job
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, status, 
                       (SELECT COUNT(*) FROM realtor_contacts WHERE scraping_job_id = scraping_jobs.id) as contact_count
                FROM scraping_jobs
                WHERE status = 'IN_PROGRESS'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            job = cur.fetchone()
            
            if job:
                print(f"\nCurrent job: {job['name']}")
                print(f"Contacts saved in DB: {job['contact_count']}")
                
                if job['contact_count'] == 0:
                    print("\n⚠️  WARNING: Scraper is finding profiles but not saving them!")
                    print("This suggests the batch processor thread may have stopped.")
                    print("\nTo fix:")
                    print("1. Fail this job: python scripts/fail_stuck_job.py")
                    print("2. Start a new job - the batch processor will restart")
            else:
                print("\nNo active job found")
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_batch_status() 