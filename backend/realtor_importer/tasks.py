"""
Background task processor for handling Realtor imports
"""
import time
import logging
import sys
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from . import scraper
from core.database import engine, ScrapingJob, RealtorContact, SessionLocal, ScrapingJobStatus

# Set up logging to ensure output is visible
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
            logger.error(f"Job {job_id} not found")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting scrape job {job_id}")
        logger.info(f"URL: {job.start_url}")
        logger.info(f"Max profiles: {MAX_PROFILES_PER_JOB}")
        logger.info(f"{'='*60}\n")
        
        job.status = ScrapingJobStatus.IN_PROGRESS
        session.commit()
        
        try:
            # Create a callback that also checks for cancellation
            def save_batch_with_cancel_check(batch: List[Dict[str, Any]]):
                # Check if job has been cancelled
                session.refresh(job)
                if job.status == "CANCELLED":
                    logger.warning(f"Job {job_id} has been cancelled, stopping scrape")
                    raise Exception("Job cancelled by user")
                
                # Save the batch
                save_batch(session, job_id, batch)
            
            # Use the new Playwright scraper for better bot detection evasion
            # This will automatically fall back to Selenium if Playwright is not available
            scraped_data = scraper.scrape_realtor_list_with_playwright(
                job.start_url, 
                max_profiles=MAX_PROFILES_PER_JOB,
                batch_callback=save_batch_with_cancel_check
            )
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Scraping completed for job {job_id}")
            logger.info(f"Total profiles scraped: {len(scraped_data)}")
            logger.info(f"{'='*60}\n")
            
            # Save any remaining data that wasn't part of a full batch
            if scraped_data:
                remaining_count = len(scraped_data) % BATCH_SIZE
                if remaining_count > 0:
                    remaining_batch = scraped_data[-remaining_count:]
                    save_batch_with_cancel_check(remaining_batch)
            
            # Final check for cancellation
            session.refresh(job)
            if job.status == "CANCELLED":
                logger.warning(f"Job {job_id} was cancelled")
            else:
                job.status = ScrapingJobStatus.COMPLETED
                session.commit()
                logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in job {job_id}: {str(e)}")
            session.refresh(job)
            if job.status != "CANCELLED":
                job.status = ScrapingJobStatus.FAILED
                job.error_message = str(e)
                session.commit()
            logger.error(f"Job {job_id} failed with error: {str(e)}")


def save_batch(session: Session, job_id: str, batch: List[Dict[str, Any]]):
    """Save a batch of scraped data"""
    logger.info(f"Saving batch of {len(batch)} profiles...")
    
    for i, data in enumerate(batch):
        try:
            # Log the data being saved for debugging
            logger.info(f"  Profile {i+1}: {data.get('first_name', 'Unknown')} {data.get('last_name', 'Unknown')} - {data.get('profile_url', 'No URL')}")
            
            # Ensure profile_url exists (it's required)
            if not data.get('profile_url'):
                logger.warning(f"  WARNING: Skipping profile without profile_url: {data}")
                continue
                
            contact = RealtorContact(
                job_id=job_id,
                **data
            )
            session.add(contact)
        except Exception as e:
            logger.error(f"  ERROR saving profile {i+1}: {str(e)}")
            logger.error(f"  Data: {data}")
            # Continue with other profiles instead of failing the whole batch
            continue
    
    try:
        session.commit()
        logger.info(f"Batch saved successfully")
    except Exception as e:
        logger.error(f"ERROR committing batch: {str(e)}")
        session.rollback()
        raise


def run_task_processor():
    """
    Main task processor loop
    """
    logger.info("Starting Realtor importer task processor...")
    
    while True:
        with SessionLocal() as session:
            # Find pending jobs
            pending_job = session.query(ScrapingJob).filter_by(
                status=ScrapingJobStatus.PENDING
            ).first()
            
            if pending_job:
                logger.info(f"Found pending job: {pending_job.id}")
                process_scrape_job(pending_job.id)
            else:
                # No jobs, wait
                time.sleep(5) 