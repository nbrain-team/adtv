from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import threading
import logging

from core import auth
from core.database import get_db, User, engine, ScrapingJob, RealtorContact
from . import schemas
from . import tasks

router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Start the background task processor in a separate thread
task_thread = None

def ensure_task_processor_running():
    """Ensure the background task processor is running"""
    global task_thread
    if task_thread is None or not task_thread.is_alive():
        logger.info("Starting background task processor thread...")
        task_thread = threading.Thread(target=tasks.run_task_processor, daemon=True)
        task_thread.start()
        logger.info("Background task processor thread started")
    else:
        logger.info("Background task processor thread is already running")

@router.post("/", response_model=schemas.ScrapingJobResponse, status_code=202)
def create_scraping_job(
    request: schemas.ScrapeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Starts a new scraping job for the given URL.
    """
    logger.info(f"Creating scraping job for URL: {request.url}")
    
    # Ensure task processor is running
    ensure_task_processor_running()
    
    # Check if there's already an active job
    active_job = db.query(ScrapingJob).filter(
        ScrapingJob.status.in_(["PENDING", "IN_PROGRESS"])
    ).first()
    
    if active_job:
        logger.warning(f"Active job already exists: {active_job.id}")
        raise HTTPException(
            status_code=400, 
            detail="Another job is already in progress. Please wait for it to complete."
        )
    
    # Create the job in the database
    new_job = ScrapingJob(
        name=request.name,  # Add the name field
        start_url=request.url,
        user_id=current_user.id,
        status="PENDING"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    logger.info(f"Created scraping job with ID: {new_job.id}")
    
    return schemas.ScrapingJobResponse(
        id=new_job.id,
        name=new_job.name,
        start_url=new_job.start_url,
        status=new_job.status.value,
        created_at=new_job.created_at,
        contact_count=0
    )

@router.get("/", response_model=List[schemas.ScrapingJobResponse])
def get_all_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Returns a list of all scraping jobs initiated by the current user.
    """
    jobs = db.query(ScrapingJob).filter(
        ScrapingJob.user_id == current_user.id
    ).order_by(ScrapingJob.created_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for job in jobs:
        # Count associated contacts
        contact_count = db.query(RealtorContact).filter(
            RealtorContact.job_id == job.id
        ).count()
        
        results.append(schemas.ScrapingJobResponse(
            id=job.id,
            name=job.name,
            start_url=job.start_url,
            status=job.status.value,
            created_at=job.created_at,
            contact_count=contact_count
        ))
    
    return results

@router.get("/{job_id}", response_model=schemas.ScrapingJobDetail)
def get_job_details(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Retrieves the details and all scraped contacts for a specific job.
    """
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all contacts for this job
    contacts = db.query(RealtorContact).filter(
        RealtorContact.job_id == job.id
    ).all()
    
    # Convert contacts to response format
    realtor_contacts = []
    for contact in contacts:
        contact_resp = schemas.RealtorContactResponse(
            id=contact.id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            company=contact.company,
            city=contact.city,
            state=contact.state,
            cell_phone=contact.cell_phone,
            email=contact.email,
            agent_website=contact.agent_website,
            phone2=contact.phone2,
            personal_email=contact.personal_email,
            facebook_profile=contact.facebook_profile,
            profile_url=contact.profile_url,
            dma=contact.dma,
            source=contact.source,
            years_exp=contact.years_exp,
            fb_or_website=contact.fb_or_website,
            seller_deals_total_deals=contact.seller_deals_total_deals,
            seller_deals_total_value=contact.seller_deals_total_value,
            seller_deals_avg_price=contact.seller_deals_avg_price,
            buyer_deals_total_deals=contact.buyer_deals_total_deals,
            buyer_deals_total_value=contact.buyer_deals_total_value,
            buyer_deals_avg_price=contact.buyer_deals_avg_price
        )
        realtor_contacts.append(contact_resp)
    
    return schemas.ScrapingJobDetail(
        id=job.id,
        name=job.name,
        start_url=job.start_url,
        status=job.status.value,
        created_at=job.created_at,
        error_message=None,  # The existing model doesn't have error_message
        realtor_contacts=realtor_contacts
    )

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Delete a scraping job and its associated contacts.
    """
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete associated contacts first (should cascade but being explicit)
    db.query(RealtorContact).filter(
        RealtorContact.job_id == job.id
    ).delete()
    
    # Delete the job
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted successfully"}

@router.post("/{job_id}/stop")
def stop_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Stop a running scraping job without deleting the data.
    """
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Only allow stopping jobs that are pending or in progress
    if job.status not in ["PENDING", "IN_PROGRESS"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot stop job with status: {job.status}"
        )
    
    # Update job status to CANCELLED
    job.status = "CANCELLED"
    job.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Job {job_id} has been cancelled by user {current_user.email}")
    
    return {"message": "Job stopped successfully", "status": "CANCELLED"} 