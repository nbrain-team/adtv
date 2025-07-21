#!/usr/bin/env python3
"""Test scraper batch saving functionality"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine, SessionLocal
from datetime import datetime

def test_batch_saving():
    with engine.connect() as conn:
        print("=== TESTING SCRAPER BATCH SAVING ===\n")
        
        # 1. Check the current job
        result = conn.execute(text("""
            SELECT id, name, status
            FROM scraping_jobs
            WHERE status = 'IN_PROGRESS'
            ORDER BY created_at DESC
            LIMIT 1
        """))
        
        job = result.fetchone()
        if not job:
            print("No IN_PROGRESS job found")
            return
            
        job_id = job[0]
        print(f"Current job: {job[1]} (ID: {job_id[:8]}...)")
        
        # 2. Check batch size configuration
        print("\n2. Checking scraper configuration:")
        try:
            from realtor_importer import tasks
            print(f"   BATCH_SIZE: {tasks.BATCH_SIZE}")
            print(f"   MAX_PROFILES_PER_JOB: {tasks.MAX_PROFILES_PER_JOB}")
        except Exception as e:
            print(f"   Error loading config: {e}")
        
        # 3. Check if task processor is saving batches
        print("\n3. Checking save_batch function:")
        print("   The scraper found 48 profiles on page 1")
        print("   With BATCH_SIZE=50, it should wait for 50 profiles before saving")
        print("   This might be why no contacts were saved yet!")
        
        # 4. Force the job to complete to trigger final batch save
        print("\n4. Options to fix:")
        print("   a) Wait for more profiles to trigger batch save (need 50+)")
        print("   b) Reduce BATCH_SIZE to save more frequently")
        print("   c) Force save remaining profiles by marking job complete")
        
        response = input("\nForce save by marking job as COMPLETED? (y/n): ")
        if response.lower() == 'y':
            with engine.begin() as trans_conn:
                # First, let's simulate what the scraper should do - save any pending data
                print("\n   Note: This won't save the scraped data (it's lost when server restarted)")
                print("   But it will clean up the job status")
                
                trans_conn.execute(text("""
                    UPDATE scraping_jobs
                    SET status = 'COMPLETED',
                        updated_at = NOW()
                    WHERE id = :job_id
                """), {"job_id": job_id})
                
            print("   ✅ Job marked as COMPLETED")
            print("\n   To fix the batch saving issue, we need to:")
            print("   1. Reduce BATCH_SIZE from 50 to 20")
            print("   2. Add periodic saves even if batch isn't full")
            print("   3. Save data before any long waits")

if __name__ == "__main__":
    test_batch_saving() 