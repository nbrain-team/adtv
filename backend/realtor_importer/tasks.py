"""
Background task processor for handling Realtor imports
"""
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from . import scraper
from core.database import engine, ScrapingJob, RealtorContact, SessionLocal, ScrapingJobStatus

# Maximum profiles to scrape per job (to control costs and prevent abuse)
MAX_PROFILES_PER_JOB = 700

# Batch size for saving results
BATCH_SIZE = 50


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
                max_profiles=MAX_PROFILES_PER_JOB,
                batch_callback=lambda batch: save_batch(session, job_id, batch)
            )
            
            print(f"Scraped {len(scraped_data)} profiles (max: {MAX_PROFILES_PER_JOB})")
            
            # Save any remaining data that wasn't part of a full batch
            if scraped_data:
                remaining_count = len(scraped_data) % BATCH_SIZE
                if remaining_count > 0:
                    remaining_batch = scraped_data[-remaining_count:]
                    save_batch(session, job_id, remaining_batch)
            
            job.status = ScrapingJobStatus.COMPLETED
            
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            job.status = ScrapingJobStatus.FAILED
            # Note: The existing model doesn't have error_message field
        
        session.commit()


def save_batch(session: Session, job_id: str, batch: List[Dict[str, Any]]):
    """Save a batch of scraped data"""
    print(f"Saving batch of {len(batch)} profiles...")
    for data in batch:
        contact = RealtorContact(
            job_id=job_id,
            **data
        )
        session.add(contact)
    session.commit()
    print(f"Batch saved successfully")


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