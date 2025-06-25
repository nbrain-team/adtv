from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from core import auth
from core.database import get_db, User, ScrapingJob, RealtorContact
from . import schemas
from . import tasks

router = APIRouter()

@router.post("/", response_model=schemas.ScrapingJobBase, status_code=202)
def create_scraping_job(
    request: schemas.ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Starts a new scraping job for the given URL.
    """
    # Create the job in the database
    new_job = ScrapingJob(
        start_url=request.url,
        user_id=current_user.id
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Add the scraping task to the background runner
    background_tasks.add_task(tasks.run_scraping_job, job_id=new_job.id)
    
    return new_job

@router.get("/", response_model=List[schemas.ScrapingJobSummary])
def get_all_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Returns a list of all scraping jobs initiated by the current user.
    """
    jobs = db.query(ScrapingJob).filter(ScrapingJob.user_id == current_user.id).order_by(ScrapingJob.created_at.desc()).offset(skip).limit(limit).all()
    
    # This is inefficient for large numbers of contacts, but fine for this project's scale.
    # A better approach would be a subquery or a counter cache column.
    results = []
    for job in jobs:
        contact_count = db.query(RealtorContact).filter(RealtorContact.job_id == job.id).count()
        job_summary = schemas.ScrapingJobSummary(
            **job.__dict__,
            contact_count=contact_count
        )
        results.append(job_summary)
        
    return results

@router.get("/{job_id}", response_model=schemas.ScrapingJob)
def get_job_details(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Retrieves the details and all scraped contacts for a specific job.
    """
    job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id, ScrapingJob.user_id == current_user.id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return job 