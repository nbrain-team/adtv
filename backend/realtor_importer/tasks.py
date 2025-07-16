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
from datetime import datetime
import os

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
    logger.info(f"\n{'='*50}")
    logger.info(f"SAVING BATCH: {len(batch)} profiles")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"{'='*50}")
    
    saved_count = 0
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
            saved_count += 1
        except Exception as e:
            logger.error(f"  ERROR saving profile {i+1}: {str(e)}")
            logger.error(f"  Data: {data}")
            # Continue with other profiles instead of failing the whole batch
            continue
    
    try:
        session.commit()
        logger.info(f"✓ Batch saved successfully: {saved_count}/{len(batch)} profiles")
        
        # Get total count for this job
        total_count = session.query(RealtorContact).filter_by(job_id=job_id).count()
        logger.info(f"Total profiles saved for this job: {total_count}")
        
        # Update job's updated_at to show activity
        job = session.query(ScrapingJob).filter_by(id=job_id).first()
        if job:
            job.updated_at = datetime.utcnow()
            session.commit()
            
    except Exception as e:
        logger.error(f"ERROR committing batch: {str(e)}")
        session.rollback()
        raise


def run_task_processor():
    """
    Main task processor loop
    """
    logger.info("Starting Realtor importer task processor...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Log environment variables (without sensitive data)
    logger.info("Environment check:")
    logger.info(f"BRIGHTDATA_BROWSER_URL set: {'Yes' if os.getenv('BRIGHTDATA_BROWSER_URL') else 'No'}")
    logger.info(f"BRIGHTDATA_API_TOKEN set: {'Yes' if os.getenv('BRIGHTDATA_API_TOKEN') else 'No'}")
    logger.info(f"RESIDENTIAL_PROXY_URL set: {'Yes' if os.getenv('RESIDENTIAL_PROXY_URL') else 'No'}")
    
    while True:
        try:
            with SessionLocal() as session:
                # Find pending jobs
                pending_job = session.query(ScrapingJob).filter_by(
                    status=ScrapingJobStatus.PENDING
                ).first()
                
                if pending_job:
                    logger.info(f"Found pending job: {pending_job.id}")
                    logger.info(f"Job name: {pending_job.name}")
                    logger.info(f"Job URL: {pending_job.start_url}")
                    process_scrape_job(pending_job.id)
                else:
                    # No jobs, wait
                    logger.debug("No pending jobs, waiting 5 seconds...")
                    time.sleep(5)
        except Exception as e:
            logger.error(f"Error in task processor loop: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Continue running even if there's an error
            time.sleep(5) 