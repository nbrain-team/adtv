from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import threading

from core import auth
from core.database import get_db, User
from .database import ScrapeJob, engine
from .models import RealtorLead
from . import schemas
from . import tasks

router = APIRouter()

# Start the background task processor in a separate thread
task_thread = None

def ensure_task_processor_running():
    """Ensure the background task processor is running"""
    global task_thread
    if task_thread is None or not task_thread.is_alive():
        task_thread = threading.Thread(target=tasks.run_task_processor, daemon=True)
        task_thread.start()

@router.post("/", response_model=schemas.ScrapingJobResponse, status_code=202)
def create_scraping_job(
    request: schemas.ScrapeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Starts a new scraping job for the given URL.
    """
    # Ensure task processor is running
    ensure_task_processor_running()
    
    # Check if there's already an active job
    with Session(engine) as session:
        active_job = session.query(ScrapeJob).filter(
            ScrapeJob.status.in_(["pending", "processing"])
        ).first()
        
        if active_job:
            raise HTTPException(
                status_code=400, 
                detail="Another job is already in progress. Please wait for it to complete."
            )
    
    # Create the job in the database
    with Session(engine) as session:
        new_job = ScrapeJob(
            start_url=request.url,
            user_id=current_user.id,
            status="pending"
        )
        session.add(new_job)
        session.commit()
        session.refresh(new_job)
        
        return schemas.ScrapingJobResponse(
            id=new_job.id,
            start_url=new_job.start_url,
            status=new_job.status,
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
    with Session(engine) as session:
        jobs = session.query(ScrapeJob).filter(
            ScrapeJob.user_id == current_user.id
        ).order_by(ScrapeJob.created_at.desc()).offset(skip).limit(limit).all()
        
        results = []
        for job in jobs:
            # Count associated leads
            contact_count = session.query(RealtorLead).filter(
                RealtorLead.job_id == job.id
            ).count()
            
            results.append(schemas.ScrapingJobResponse(
                id=job.id,
                start_url=job.start_url,
                status=job.status,
                created_at=job.created_at,
                contact_count=contact_count
            ))
        
        return results

@router.get("/{job_id}", response_model=schemas.ScrapingJobDetail)
def get_job_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Retrieves the details and all scraped contacts for a specific job.
    """
    with Session(engine) as session:
        job = session.query(ScrapeJob).filter(
            ScrapeJob.id == job_id,
            ScrapeJob.user_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get all leads for this job
        leads = session.query(RealtorLead).filter(
            RealtorLead.job_id == job.id
        ).all()
        
        # Convert leads to response format
        realtor_contacts = []
        for lead in leads:
            contact = schemas.RealtorContactResponse(
                id=str(lead.id),
                first_name=lead.first_name,
                last_name=lead.last_name,
                company=lead.company,
                city=lead.city,
                state=lead.state,
                cell_phone=lead.cell_phone,
                email=lead.email,
                profile_url=lead.profile_url
            )
            realtor_contacts.append(contact)
        
        return schemas.ScrapingJobDetail(
            id=job.id,
            start_url=job.start_url,
            status=job.status,
            created_at=job.created_at,
            error_message=job.error_message,
            realtor_contacts=realtor_contacts
        )

@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Delete a scraping job and its associated leads.
    """
    with Session(engine) as session:
        job = session.query(ScrapeJob).filter(
            ScrapeJob.id == job_id,
            ScrapeJob.user_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete associated leads first
        session.query(RealtorLead).filter(
            RealtorLead.job_id == job.id
        ).delete()
        
        # Delete the job
        session.delete(job)
        session.commit()
        
        return {"message": "Job deleted successfully"} 