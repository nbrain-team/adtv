"""
Timeout and error handling improvements for the realtor scraper
"""
import signal
import time
from contextlib import contextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ScraperTimeout(Exception):
    """Custom exception for scraper timeouts"""
    pass

@contextmanager
def timeout(seconds: int):
    """Context manager for setting a timeout on operations"""
    def timeout_handler(signum, frame):
        raise ScraperTimeout(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Cancel the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def scrape_with_timeout(scrape_func, url: str, max_profiles: int, timeout_seconds: int = 3600, **kwargs):
    """
    Wrapper to add timeout to any scraping function
    
    Args:
        scrape_func: The scraping function to call
        url: URL to scrape
        max_profiles: Maximum number of profiles to scrape
        timeout_seconds: Maximum time allowed for scraping (default: 1 hour)
        **kwargs: Additional arguments to pass to scrape_func
    """
    try:
        with timeout(timeout_seconds):
            logger.info(f"Starting scrape with {timeout_seconds}s timeout")
            result = scrape_func(url, max_profiles, **kwargs)
            logger.info(f"Scrape completed successfully")
            return result
    except ScraperTimeout as e:
        logger.error(f"Scraper timeout: {e}")
        raise
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        raise

def add_job_timeout_check(db_session, job_id: str, max_runtime_hours: int = 2):
    """
    Check if a job has been running too long and mark it as failed
    
    Args:
        db_session: Database session
        job_id: Job ID to check
        max_runtime_hours: Maximum allowed runtime in hours (default: 2)
    """
    from datetime import datetime, timedelta
    from .models import ScrapingJob, ScrapingJobStatus
    
    job = db_session.query(ScrapingJob).filter_by(id=job_id).first()
    if not job:
        return
    
    # Check if job has been running too long
    if job.status in [ScrapingJobStatus.IN_PROGRESS, "PENDING"]:
        runtime = datetime.utcnow() - job.created_at
        if runtime > timedelta(hours=max_runtime_hours):
            logger.error(f"Job {job_id} has been running for {runtime}, marking as failed")
            job.status = ScrapingJobStatus.FAILED
            job.error_message = f"Job timed out after {max_runtime_hours} hours"
            db_session.commit()
            return True
    return False 