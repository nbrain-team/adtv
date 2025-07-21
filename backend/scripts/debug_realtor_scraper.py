#!/usr/bin/env python3
"""Debug script to check realtor scraper jobs and issues"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine
from datetime import datetime, timedelta
import json

def debug_realtor_scraper():
    with engine.connect() as conn:
        print("=== DEBUGGING REALTOR SCRAPER ===\n")
        
        # 1. Check all scraper jobs
        print("1. Recent scraper jobs (last 7 days):")
        result = conn.execute(text("""
            SELECT id, status, created_at, updated_at, error_message,
                   name, completed_at
            FROM scraping_jobs
            WHERE created_at > :date_limit
            ORDER BY created_at DESC
            LIMIT 20
        """), {"date_limit": datetime.now() - timedelta(days=7)})
        
        jobs = []
        for row in result:
            job = {
                'id': row[0],
                'status': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'error_message': row[4],
                'name': row[5],
                'completed_at': row[6]
            }
            jobs.append(job)
            
            print(f"\n   Job ID: {row[0][:8]}...")
            print(f"   Name: {row[5] or 'No name'}")
            print(f"   Status: {row[1]}")
            print(f"   Created: {row[2]}")
            print(f"   Updated: {row[3]}")
            
            if row[6]:  # completed_at
                duration = row[6] - row[2]
            elif row[3]:  # updated_at
                duration = row[3] - row[2]
            else:
                duration = datetime.now() - row[2]
            
            print(f"   Duration: {duration}")
            
            if row[4]:
                print(f"   ERROR: {row[4][:100]}...")
        
        # 2. Check stuck jobs
        print("\n2. Potentially stuck jobs (running > 1 hour):")
        result = conn.execute(text("""
            SELECT id, status, created_at, updated_at, name
            FROM scraping_jobs
            WHERE status IN ('PENDING', 'IN_PROGRESS')
            AND created_at < :time_limit
        """), {"time_limit": datetime.now() - timedelta(hours=1)})
        
        stuck_count = 0
        for row in result:
            stuck_count += 1
            duration = datetime.now() - row[2]
            print(f"   - Job {row[0][:8]}... '{row[4] or 'No name'}' has been {row[1]} for {duration}")
        
        if stuck_count == 0:
            print("   No stuck jobs found")
        
        # 3. Check realtor contacts
        print("\n3. Realtor contacts by job:")
        for job in jobs[:5]:  # Check last 5 jobs
            result = conn.execute(text("""
                SELECT COUNT(*) FROM realtor_contacts
                WHERE job_id = :job_id
            """), {"job_id": job['id']})
            
            count = result.scalar()
            print(f"   - Job {job['id'][:8]}... '{job['name'] or 'No name'}': {count} contacts saved")
        
        # 4. Check for completed jobs
        print("\n4. Job completion status:")
        result = conn.execute(text("""
            SELECT status, COUNT(*) as count
            FROM scraping_jobs
            WHERE created_at > :date_limit
            GROUP BY status
            ORDER BY count DESC
        """), {"date_limit": datetime.now() - timedelta(days=30)})
        
        for row in result:
            print(f"   - {row[0]}: {row[1]} jobs")
        
        # 5. Check for common errors
        print("\n5. Common errors (last 10):")
        result = conn.execute(text("""
            SELECT error_message, COUNT(*) as count
            FROM scraping_jobs
            WHERE error_message IS NOT NULL
            AND created_at > :date_limit
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 10
        """), {"date_limit": datetime.now() - timedelta(days=7)})
        
        error_count = 0
        for row in result:
            error_count += 1
            print(f"   - {row[1]}x: {row[0][:100]}...")
        
        if error_count == 0:
            print("   No errors found in the last 7 days")
        
        # 6. Check export directory
        print("\n6. Export directory check:")
        export_dirs = [
            "exports",
            "exports/realtor",
            "backend/exports",
            "backend/exports/realtor",
            "/tmp/exports",
            "/tmp/realtor_exports",
            "/opt/render/project/src/exports",
            "/opt/render/project/src/backend/exports"
        ]
        
        for dir_path in export_dirs:
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                print(f"   - {dir_path}: {len(files)} files")
                if files:
                    recent_files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(dir_path, x)))[-5:]
                    print(f"     Recent files: {', '.join(recent_files)}")
            else:
                print(f"   - {dir_path}: Directory not found")
        
        # 7. Check current job details
        print("\n7. Current/Recent job details:")
        if jobs:
            latest_job = jobs[0]
            print(f"   Latest job: {latest_job['name'] or 'No name'}")
            print(f"   Status: {latest_job['status']}")
            print(f"   Started: {latest_job['created_at']}")
            if latest_job['status'] == 'IN_PROGRESS':
                print("   ⚠️  This job is currently running")
                print("   Note: Jobs typically take 30-60 minutes for large searches")
                print("   The scraper exports are generated after completion")

if __name__ == "__main__":
    debug_realtor_scraper() 