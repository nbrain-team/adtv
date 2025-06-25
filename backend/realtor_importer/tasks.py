import time
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import SessionLocal, ScrapingJob, RealtorContact, ScrapingJobStatus
from . import scraper

# A limit to prevent excessively long-running scrapes during this initial phase.
MAX_PROFILES_TO_SCRAPE = 25

def run_scraping_job(job_id: str):
    """
    The main background task for a single scraping job.
    """
    db: Session = SessionLocal()
    try:
        # --- 1. Get the Job and Update Status ---
        job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        if not job:
            print(f"Job {job_id} not found.")
            return

        print(f"Starting scraping job {job_id} for URL: {job.start_url}")
        job.status = ScrapingJobStatus.IN_PROGRESS
        db.commit()

        # --- 2. Scrape the List Page for Profile URLs ---
        profile_urls = scraper.scrape_realtor_list_page(job.start_url)
        if not profile_urls:
            print(f"No profile URLs found at {job.start_url}. Ending job.")
            job.status = ScrapingJobStatus.FAILED
            db.commit()
            return
            
        print(f"Found {len(profile_urls)} profiles to scrape. Capping at {MAX_PROFILES_TO_SCRAPE}.")

        # --- 3. Scrape Each Profile Page ---
        for i, url in enumerate(profile_urls[:MAX_PROFILES_TO_SCRAPE]):
            print(f"Scraping profile {i+1}/{len(profile_urls)}: {url}")
            
            # Check if this contact already exists to avoid duplicates
            exists = db.query(RealtorContact).filter(RealtorContact.profile_url == url).first()
            if exists:
                print(f"Contact for {url} already exists. Skipping.")
                continue

            contact_data = scraper.scrape_realtor_profile_page(url)
            if contact_data:
                new_contact = RealtorContact(
                    job_id=job.id,
                    **contact_data
                )
                db.add(new_contact)
                db.commit()
            
            # Per user request, wait 15 seconds between crawls to be respectful.
            time.sleep(15)

        # --- 4. Finalize Job ---
        job.status = ScrapingJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()
        print(f"Successfully completed job {job_id}.")

    except Exception as e:
        print(f"An error occurred during job {job_id}: {e}")
        if 'job' in locals() and job:
            job.status = ScrapingJobStatus.FAILED
            db.commit()
    finally:
        db.close() 