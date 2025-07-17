from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import threading
import logging
from sqlalchemy import text

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

@router.post("/migrate-sales-columns")
def migrate_sales_columns(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Add missing sales statistics columns to realtor_contacts table
    """
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'realtor_contacts' 
                AND column_name IN ('closed_sales', 'total_value', 'price_range', 'average_price')
            """))
            existing_columns = [row[0] for row in result]
            
            if len(existing_columns) == 4:
                return {"message": "All sales columns already exist", "status": "no_change"}
            
            # Add missing columns
            conn.execute(text("""
                ALTER TABLE realtor_contacts 
                ADD COLUMN IF NOT EXISTS closed_sales VARCHAR,
                ADD COLUMN IF NOT EXISTS total_value VARCHAR,
                ADD COLUMN IF NOT EXISTS price_range VARCHAR,
                ADD COLUMN IF NOT EXISTS average_price VARCHAR;
            """))
            conn.commit()
            
            return {
                "message": "Successfully added sales statistics columns", 
                "status": "success",
                "columns_added": ["closed_sales", "total_value", "price_range", "average_price"]
            }
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

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
    Stop a running scraping job
    """
    job = db.query(ScrapingJob).filter(
        ScrapingJob.id == job_id,
        ScrapingJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ["PENDING", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="Job is not running")
    
    job.status = "CANCELLED"
    db.commit()
    
    return {"message": "Job stopped successfully"}

@router.post("/process-selected", response_model=schemas.ProcessedJobResponse)
async def process_selected_jobs(
    request: schemas.ProcessJobsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Process and merge multiple selected jobs:
    1. Merge and deduplicate contacts
    2. Crawl website content
    3. Validate emails with ZeroBounce
    """
    # Validate that all jobs belong to the user and are completed
    jobs = db.query(ScrapingJob).filter(
        ScrapingJob.id.in_(request.job_ids),
        ScrapingJob.user_id == current_user.id,
        ScrapingJob.status == "COMPLETED"
    ).all()
    
    if len(jobs) != len(request.job_ids):
        raise HTTPException(
            status_code=400,
            detail="Some jobs not found or not completed"
        )
    
    # Create a new processed job entry
    from . import models
    processed_job = models.ProcessedJob(
        user_id=current_user.id,
        source_job_ids=request.job_ids,
        status="PENDING"
    )
    db.add(processed_job)
    db.commit()
    db.refresh(processed_job)
    
    # Start background processing
    background_tasks.add_task(
        tasks.process_merged_jobs,
        processed_job.id,
        request.job_ids
    )
    
    return schemas.ProcessedJobResponse(
        id=processed_job.id,
        status=processed_job.status,
        created_at=processed_job.created_at,
        source_job_count=len(request.job_ids)
    )

@router.get("/processed/{processed_id}", response_model=schemas.ProcessedJobDetail)
def get_processed_job(
    processed_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """Get details of a processed/merged job"""
    from . import models
    
    processed_job = db.query(models.ProcessedJob).filter(
        models.ProcessedJob.id == processed_id,
        models.ProcessedJob.user_id == current_user.id
    ).first()
    
    if not processed_job:
        raise HTTPException(status_code=404, detail="Processed job not found")
    
    # Get merged contacts
    contacts = db.query(models.MergedContact).filter(
        models.MergedContact.processed_job_id == processed_id
    ).all()
    
    return schemas.ProcessedJobDetail(
        id=processed_job.id,
        status=processed_job.status,
        created_at=processed_job.created_at,
        source_job_ids=processed_job.source_job_ids,
        total_contacts=processed_job.total_contacts,
        duplicates_removed=processed_job.duplicates_removed,
        emails_validated=processed_job.emails_validated,
        websites_crawled=processed_job.websites_crawled,
        contacts=[schemas.MergedContactResponse.from_orm(c) for c in contacts]
    )

@router.post("/processed/{processed_id}/personalize-emails")
def create_personalized_emails(
    processed_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Redirect processed contacts to email personalization
    """
    from . import models
    
    # Get the processed job
    processed_job = db.query(models.ProcessedJob).filter(
        models.ProcessedJob.id == processed_id,
        models.ProcessedJob.user_id == current_user.id
    ).first()
    
    if not processed_job:
        raise HTTPException(status_code=404, detail="Processed job not found")
    
    # Get merged contacts
    contacts = db.query(models.MergedContact).filter(
        models.MergedContact.processed_job_id == processed_id
    ).all()
    
    # Convert to CSV format for email personalizer
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'first_name', 'last_name', 'company', 'email', 
        'city', 'state', 'website_content', 'phone'
    ])
    
    writer.writeheader()
    for contact in contacts:
        writer.writerow({
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'company': contact.company,
            'email': contact.email,
            'city': contact.city,
            'state': contact.state,
            'website_content': contact.website_content[:500] if contact.website_content else '',
            'phone': contact.cell_phone
        })
    
    # Return CSV data that can be used by email personalizer
    return {
        "csv_data": output.getvalue(),
        "contact_count": len(contacts)
    }

@router.get("/{job_id}/export/csv")
def export_job_csv(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user),
):
    """
    Export job results as CSV file
    """
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Get the job
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
    
    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found for this job")
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'first_name', 'last_name', 'company', 'city', 'state', 'dma',
        'cell_phone', 'phone2', 'email', 'personal_email',
        'agent_website', 'facebook_profile', 'fb_or_website',
        'years_exp', 'seller_deals_total_deals', 'seller_deals_total_value',
        'seller_deals_avg_price', 'buyer_deals_total_deals', 
        'buyer_deals_total_value', 'buyer_deals_avg_price',
        'profile_url', 'source'
    ])
    
    writer.writeheader()
    
    for contact in contacts:
        writer.writerow({
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'company': contact.company,
            'city': contact.city,
            'state': contact.state,
            'dma': contact.dma,
            'cell_phone': contact.cell_phone,
            'phone2': contact.phone2,
            'email': contact.email,
            'personal_email': contact.personal_email,
            'agent_website': contact.agent_website,
            'facebook_profile': contact.facebook_profile,
            'fb_or_website': contact.fb_or_website,
            'years_exp': contact.years_exp,
            'seller_deals_total_deals': contact.seller_deals_total_deals,
            'seller_deals_total_value': contact.seller_deals_total_value,
            'seller_deals_avg_price': contact.seller_deals_avg_price,
            'buyer_deals_total_deals': contact.buyer_deals_total_deals,
            'buyer_deals_total_value': contact.buyer_deals_total_value,
            'buyer_deals_avg_price': contact.buyer_deals_avg_price,
            'profile_url': contact.profile_url,
            'source': contact.source
        })
    
    output.seek(0)
    
    # Generate filename
    filename = f"realtor_export_{job.name or job_id}_{len(contacts)}_contacts.csv"
    filename = filename.replace(' ', '_').replace('/', '_')
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    ) 