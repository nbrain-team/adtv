#!/usr/bin/env python3
"""Mark stuck scraper job as failed"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
from datetime import datetime

def fail_stuck_job():
    with engine.connect() as conn:
        print("=== MARKING STUCK JOB AS FAILED ===\n")
        
        # Find the stuck job
        result = conn.execute(text("""
            SELECT id, name, status, created_at, updated_at
            FROM scraping_jobs
            WHERE status = 'IN_PROGRESS'
            ORDER BY created_at DESC
            LIMIT 1
        """))
        
        job = result.fetchone()
        if not job:
            print("No IN_PROGRESS jobs found")
            return
        
        job_id = job[0]
        job_name = job[1]
        duration = datetime.utcnow() - job[3].replace(tzinfo=None)
        
        print(f"Found stuck job: {job_name} (ID: {job_id[:8]}...)")
        print(f"Duration: {duration}")
        
        response = input("\nMark this job as FAILED? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
        
        # Mark as failed
        with engine.begin() as trans_conn:
            trans_conn.execute(text("""
                UPDATE scraping_jobs
                SET status = 'FAILED',
                    error_message = :error_msg,
                    updated_at = NOW()
                WHERE id = :job_id
            """), {
                "job_id": job_id,
                "error_msg": f"Job stalled after {duration}. Task processor likely crashed."
            })
        
        print("✅ Job marked as FAILED")
        print("\nYou can now start a new scraping job from the UI.")

if __name__ == "__main__":
    fail_stuck_job() 