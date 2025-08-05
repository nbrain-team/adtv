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
BATCH_SIZE = 20  # Reduced from 50 for more frequent saves


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


def process_merged_jobs(processed_job_id: str, job_ids: List[str]):
    """
    Process and merge multiple scraping jobs:
    1. Merge and deduplicate contacts
    2. Crawl website content
    3. Validate emails with ZeroBounce
    """
    from . import models
    
    with SessionLocal() as session:
        processed_job = session.query(models.ProcessedJob).filter_by(id=processed_job_id).first()
        if not processed_job:
            logger.error(f"Processed job {processed_job_id} not found")
            return
        
        try:
            processed_job.status = "PROCESSING"
            session.commit()
            
            # Step 1: Collect all contacts from source jobs
            all_contacts = []
            for job_id in job_ids:
                contacts = session.query(RealtorContact).filter_by(job_id=job_id).all()
                all_contacts.extend(contacts)
            
            logger.info(f"Collected {len(all_contacts)} total contacts from {len(job_ids)} jobs")
            
            # Step 2: Deduplicate by first_name + last_name + email
            merged_contacts = {}
            duplicates = 0
            
            for contact in all_contacts:
                # Create a key for deduplication
                key = (
                    (contact.first_name or '').lower().strip(),
                    (contact.last_name or '').lower().strip(),
                    (contact.email or contact.personal_email or '').lower().strip()
                )
                
                if key in merged_contacts:
                    # Merge - keep the most complete record
                    duplicates += 1
                    existing = merged_contacts[key]
                    merged_contacts[key] = merge_contact_records(existing, contact)
                else:
                    merged_contacts[key] = contact
            
            logger.info(f"After deduplication: {len(merged_contacts)} unique contacts, {duplicates} duplicates removed")
            
            # Step 3: Create MergedContact records and enrich data
            for i, (key, contact) in enumerate(merged_contacts.items()):
                merged = models.MergedContact(
                    processed_job_id=processed_job_id,
                    first_name=contact.first_name,
                    last_name=contact.last_name,
                    company=contact.company,
                    city=contact.city,
                    state=contact.state,
                    dma=contact.dma,
                    cell_phone=contact.cell_phone,
                    phone2=contact.phone2,
                    email=contact.email,
                    personal_email=contact.personal_email,
                    agent_website=contact.agent_website or contact.fb_or_website,
                    facebook_profile=contact.facebook_profile,
                    fb_or_website=contact.fb_or_website,
                    profile_url=contact.profile_url,
                    years_exp=contact.years_exp,
                    # Add sales stats if available
                    closed_sales=getattr(contact, 'closed_sales', None),
                    total_value=getattr(contact, 'total_value', None),
                    price_range=getattr(contact, 'price_range', None),
                    average_price=getattr(contact, 'average_price', None)
                )
                
                # Step 4: Crawl website content if available
                website_url = contact.agent_website or contact.fb_or_website
                if website_url and website_url.startswith('http'):
                    try:
                        website_content = crawl_website(website_url)
                        if website_content:
                            merged.website_content = website_content[:5000]  # Limit to 5000 chars
                            processed_job.websites_crawled += 1
                    except Exception as e:
                        logger.error(f"Error crawling website {website_url}: {e}")
                
                # Step 5: Validate email with ZeroBounce
                email_to_validate = contact.email or contact.personal_email
                if email_to_validate:
                    try:
                        validation_result = validate_email_zerobounce(email_to_validate)
                        if validation_result:
                            merged.email_valid = validation_result.get('status') == 'valid'
                            merged.email_status = validation_result.get('status')
                            merged.email_score = validation_result.get('score', 0)
                            processed_job.emails_validated += 1
                    except Exception as e:
                        logger.error(f"Error validating email {email_to_validate}: {e}")
                
                session.add(merged)
                
                # Commit in batches
                if i % 50 == 0:
                    session.commit()
            
            # Final commit
            session.commit()
            
            # Update processed job stats
            processed_job.total_contacts = len(merged_contacts)
            processed_job.duplicates_removed = duplicates
            processed_job.status = "COMPLETED"
            session.commit()
            
            logger.info(f"Processing completed: {len(merged_contacts)} contacts, {duplicates} duplicates removed")
            
        except Exception as e:
            logger.error(f"Error processing merged jobs: {e}")
            processed_job.status = "FAILED"
            session.commit()


def merge_contact_records(existing, new):
    """Merge two contact records, preferring non-null values"""
    # Create a dictionary of the existing contact
    merged_dict = {
        'first_name': existing.first_name or new.first_name,
        'last_name': existing.last_name or new.last_name,
        'company': existing.company or new.company,
        'city': existing.city or new.city,
        'state': existing.state or new.state,
        'dma': existing.dma or new.dma,
        'cell_phone': existing.cell_phone or new.cell_phone,
        'phone2': existing.phone2 or new.phone2,
        'email': existing.email or new.email,
        'personal_email': existing.personal_email or new.personal_email,
        'agent_website': existing.agent_website or new.agent_website,
        'facebook_profile': existing.facebook_profile or new.facebook_profile,
        'fb_or_website': existing.fb_or_website or new.fb_or_website,
        'profile_url': existing.profile_url or new.profile_url,
        'years_exp': existing.years_exp or new.years_exp,
        'source': existing.source,
        # Sales data - prefer non-null
        'closed_sales': getattr(existing, 'closed_sales', None) or getattr(new, 'closed_sales', None),
        'total_value': getattr(existing, 'total_value', None) or getattr(new, 'total_value', None),
        'price_range': getattr(existing, 'price_range', None) or getattr(new, 'price_range', None),
        'average_price': getattr(existing, 'average_price', None) or getattr(new, 'average_price', None)
    }
    
    # Create a new contact object with merged data
    class MergedContactObj:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    return MergedContactObj(**merged_dict)


def crawl_website(url: str) -> Optional[str]:
    """Crawl website and extract text content"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # Add timeout and headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit to 5000 characters

    except Exception as e:
        logger.error(f"Error crawling {url}: {e}")
        return None


def validate_email_zerobounce(email: str) -> Optional[Dict[str, Any]]:
    """Validate email using ZeroBounce API"""
    import requests
    
    api_key = "848cbcd03ba043eaa677fc9f56c77da6"
    
    try:
        url = f"https://api.zerobounce.net/v2/validate"
        params = {
            'api_key': api_key,
            'email': email
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return {
            'status': result.get('status'),  # valid, invalid, catch-all, spamtrap, abuse, etc.
            'score': result.get('zerobounce_score', 0),
            'sub_status': result.get('sub_status')
        }

    except Exception as e:
        logger.error(f"Error validating email {email}: {e}")
        return None 