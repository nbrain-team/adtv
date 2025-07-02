"""
Background task processor for handling Realtor imports
"""
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from . import scraper
from .database import engine, ScrapeJob
from .models import RealtorLead


def process_scrape_job(job_id: int):
    """
    Process a single scrape job
    """
    with Session(engine) as session:
        job = session.query(ScrapeJob).filter_by(id=job_id).first()
        if not job:
            print(f"Job {job_id} not found")
            return
        
        job.status = "processing"
        session.commit()
        
        try:
            # Use the new Playwright scraper for better bot detection evasion
            # This will automatically fall back to Selenium if Playwright is not available
            scraped_data = scraper.scrape_realtor_list_with_playwright(
                job.start_url, 
                max_profiles=10  # Limit for testing
            )
            
            # Save scraped data
            for data in scraped_data:
                lead = RealtorLead(
                    job_id=job_id,
                    **data
                )
                session.add(lead)
            
            job.status = "completed"
            job.leads_found = len(scraped_data)
            
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            job.status = "failed"
            job.error_message = str(e)
        
        session.commit()


def run_task_processor():
    """
    Main task processor loop
    """
    print("Starting Realtor importer task processor...")
    
    while True:
        with Session(engine) as session:
            # Find pending jobs
            pending_job = session.query(ScrapeJob).filter_by(status="pending").first()
            
            if pending_job:
                print(f"Processing job {pending_job.id}")
                process_scrape_job(pending_job.id)
            else:
                # No jobs, wait
                time.sleep(5) 