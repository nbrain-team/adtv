#!/usr/bin/env python3
"""Fix stuck realtor scraper jobs"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
from datetime import datetime, timedelta

def fix_stuck_jobs():
    with engine.connect() as conn:
        print("=== FIXING STUCK SCRAPER JOBS ===\n")
        
        # 1. Find stuck jobs (running > 2 hours)
        print("1. Finding stuck jobs (running > 2 hours)...")
        result = conn.execute(text("""
            SELECT id, status, created_at, updated_at, name
            FROM scraping_jobs
            WHERE status IN ('PENDING', 'IN_PROGRESS')
            AND created_at < :time_limit
        """), {"time_limit": datetime.now() - timedelta(hours=2)})
        
        stuck_jobs = []
        for row in result:
            duration = datetime.now() - row[2]
            stuck_jobs.append({
                'id': row[0],
                'status': row[1],
                'created_at': row[2],
                'duration': duration,
                'name': row[4]
            })
            print(f"   - Job {row[0][:8]}... '{row[4] or 'No name'}' has been {row[1]} for {duration}")
        
        if not stuck_jobs:
            print("   No stuck jobs found!")
            return
        
        # 2. Ask for confirmation
        print(f"\n2. Found {len(stuck_jobs)} stuck jobs")
        response = input("Mark these as failed? (y/n): ")
        
        if response.lower() != 'y':
            print("   Cancelled")
            return
        
        # 3. Mark stuck jobs as failed
        print("\n3. Marking stuck jobs as failed...")
        with engine.begin() as trans_conn:
            for job in stuck_jobs:
                trans_conn.execute(text("""
                    UPDATE scraping_jobs
                    SET status = 'FAILED',
                        error_message = :error_msg,
                        updated_at = :now
                    WHERE id = :job_id
                """), {
                    'job_id': job['id'],
                    'error_msg': f'Job timed out after {job["duration"]}',
                    'now': datetime.now()
                })
                print(f"   ✅ Marked job {job['id'][:8]}... '{job['name'] or 'No name'}' as failed")
        
        print(f"\n✅ Fixed {len(stuck_jobs)} stuck jobs")
        
        # 4. Check for jobs without exports
        print("\n4. Checking for completed jobs without exports...")
        result = conn.execute(text("""
            SELECT j.id, j.created_at, j.name,
                   (SELECT COUNT(*) FROM realtor_contacts WHERE job_id = j.id) as contact_count
            FROM scraping_jobs j
            LEFT JOIN download_files d ON j.id = d.job_id
            WHERE j.status = 'COMPLETED'
            AND d.id IS NULL
            ORDER BY j.created_at DESC
            LIMIT 10
        """))
        
        missing_exports = []
        for row in result:
            if row[3] > 0:  # Has contacts but no export
                missing_exports.append({
                    'id': row[0],
                    'created_at': row[1],
                    'name': row[2],
                    'contact_count': row[3]
                })
                print(f"   - Job {row[0][:8]}... '{row[2] or 'No name'}' has {row[3]} contacts but no export file")
        
        if missing_exports:
            print(f"\n   Found {len(missing_exports)} jobs with missing exports")
            print("   These jobs may need to be re-exported")
        else:
            print("   All completed jobs have exports")

if __name__ == "__main__":
    fix_stuck_jobs() 