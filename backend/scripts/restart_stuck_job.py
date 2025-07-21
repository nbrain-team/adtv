#!/usr/bin/env python3
"""Restart stuck scraper jobs"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine, SessionLocal
from datetime import datetime
from realtor_importer import tasks
import threading

def restart_stuck_job():
    with engine.connect() as conn:
        print("=== RESTARTING STUCK SCRAPER JOB ===\n")
        
        # 1. Find the stuck job
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
        
        print(f"Found stuck job: {job_name} (ID: {job_id[:8]}...)")
        print(f"Created: {job[3]}")
        print(f"Last Updated: {job[4]}")
        
        # 2. Reset the job to PENDING
        print("\n2. Resetting job status to PENDING...")
        with engine.begin() as trans_conn:
            trans_conn.execute(text("""
                UPDATE scraping_jobs
                SET status = 'PENDING',
                    updated_at = NOW()
                WHERE id = :job_id
            """), {"job_id": job_id})
        print("✅ Job reset to PENDING")
        
        # 3. Check if task processor is running
        print("\n3. Starting task processor...")
        
        # Start the task processor in a thread
        task_thread = threading.Thread(target=tasks.run_task_processor, daemon=False)
        task_thread.start()
        print("✅ Task processor started")
        
        print("\n4. Monitoring job progress...")
        print("The job should start processing now.")
        print("Run 'python scripts/check_scraper_logs.py' in a few minutes to check progress.")
        
        # Keep the script running for a bit to let the processor start
        import time
        for i in range(10):
            time.sleep(1)
            print(f"   Waiting... {10-i} seconds")
        
        print("\n✅ Job restart initiated. The scraper should be processing now.")
        print("Note: This script will exit but the scraper will continue in the background.")

if __name__ == "__main__":
    restart_stuck_job() 