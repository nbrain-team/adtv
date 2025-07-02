"""
Background task processor for handling Realtor imports
"""
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from . import scraper
from core.database import engine, ScrapingJob, RealtorContact, SessionLocal, ScrapingJobStatus

# Maximum profiles to scrape per job (to control costs and prevent abuse)
MAX_PROFILES_PER_JOB = 25


def process_scrape_job(job_id: str):
    """
    Process a single scrape job
    """
    with SessionLocal() as session:
        job = session.query(ScrapingJob).filter_by(id=job_id).first()
        if not job:
            print(f"Job {job_id} not found")
            return
        
        job.status = ScrapingJobStatus.IN_PROGRESS
        session.commit()
        
        try:
            # Use the new Playwright scraper for better bot detection evasion
            # This will automatically fall back to Selenium if Playwright is not available
            scraped_data = scraper.scrape_realtor_list_with_playwright(
                job.start_url, 
                max_profiles=MAX_PROFILES_PER_JOB
            )
            
            print(f"Scraped {len(scraped_data)} profiles (max: {MAX_PROFILES_PER_JOB})")
            
            # Save scraped data
            for data in scraped_data:
                contact = RealtorContact(
                    job_id=job_id,
                    **data
                )
                session.add(contact)
            
            job.status = ScrapingJobStatus.COMPLETED
            
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            job.status = ScrapingJobStatus.FAILED
            # Note: The existing model doesn't have error_message field
        
        session.commit()


def run_task_processor():
    """
    Main task processor loop
    """
    print("Starting Realtor importer task processor...")
    
    while True:
        with SessionLocal() as session:
            # Find pending jobs
            pending_job = session.query(ScrapingJob).filter_by(
                status=ScrapingJobStatus.PENDING
            ).first()
            
            if pending_job:
                print(f"Processing job {pending_job.id}")
                process_scrape_job(pending_job.id)
            else:
                # No jobs, wait
                time.sleep(5) 