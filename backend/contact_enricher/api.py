from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import json
import csv
from datetime import datetime
import logging

from core.database import get_db, User
from core.auth import get_current_active_user
from . import models, schemas, services

router = APIRouter(tags=["contact-enricher"])
logger = logging.getLogger(__name__)


@router.post("/projects/upload")
async def upload_csv(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a CSV file for enrichment"""
    logger.info(f"Starting file upload: {file.filename} for user {current_user.email}")
    logger.info(f"Project name: {name}, description: {description}")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=422, detail="Only CSV files are allowed")
    
    # Read CSV file
    try:
        contents = await file.read()
        logger.info(f"Read {len(contents)} bytes from file")
        
        # Try different encodings
        df = None
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(io.StringIO(contents.decode(encoding)))
                logger.info(f"Successfully read CSV with {encoding} encoding")
                logger.info(f"CSV shape: {df.shape}, columns: {list(df.columns)}")
                break
            except (UnicodeDecodeError, pd.errors.EmptyDataError) as e:
                logger.warning(f"Failed to read CSV with {encoding} encoding: {str(e)}")
                continue
        
        if df is None:
            raise HTTPException(
                status_code=422, 
                detail="Unable to read CSV file. Please ensure it's a valid CSV file with proper encoding."
            )
        
        if df.empty:
            raise HTTPException(
                status_code=422,
                detail="CSV file is empty or contains no data"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"Error processing CSV file: {str(e)}"
        )
    
    # Create project
    try:
        project = models.EnrichmentProject(
            user_id=current_user.id,
            name=name,
            description=description,
            original_filename=file.filename,
            original_row_count=len(df),
            status="pending"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info(f"Created project {project.id} with {project.original_row_count} rows")
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")
    
    # Save contacts
    try:
        contacts_created = 0
        for _, row in df.iterrows():
            contact = models.EnrichedContact(
                project_id=project.id,
                original_data=row.to_dict(),
                name=row.get('Name'),
                company=row.get('Company'),
                city=row.get('City'),
                state=row.get('State'),
                agent_website=row.get('Agent_Website'),
                facebook_profile=row.get('Facebook_Profile')
            )
            db.add(contact)
            contacts_created += 1
        
        db.commit()
        logger.info(f"Created {contacts_created} contacts for project {project.id}")
    except Exception as e:
        logger.error(f"Error saving contacts: {str(e)}", exc_info=True)
        db.rollback()
        # Delete the project if contacts fail
        db.delete(project)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error saving contacts: {str(e)}")
    
    return schemas.ProjectResponse.from_orm(project)


@router.options("/projects/upload")
async def upload_csv_options():
    from fastapi.responses import Response
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
    )


@router.get("/projects", response_model=List[schemas.EnrichmentProject])
async def get_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all enrichment projects for the current user"""
    projects = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.user_id == current_user.id
    ).order_by(models.EnrichmentProject.created_at.desc()).all()
    
    return projects


@router.get("/projects/{project_id}", response_model=schemas.EnrichmentProject)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific enrichment project"""
    project = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.id == project_id,
        models.EnrichmentProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.post("/projects/{project_id}/enrich")
async def start_enrichment(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start the enrichment process for a project"""
    project = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.id == project_id,
        models.EnrichmentProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != "pending":
        raise HTTPException(status_code=400, detail="Project already processed")
    
    # Start background enrichment
    background_tasks.add_task(
        enrich_project_contacts,
        project_id
    )
    
    project.status = "processing"
    db.commit()
    
    return {"message": "Enrichment started", "project_id": project_id}


@router.get("/projects/{project_id}/progress", response_model=schemas.EnrichmentProgress)
async def get_enrichment_progress(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the progress of an enrichment job"""
    project = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.id == project_id,
        models.EnrichmentProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Calculate estimated time
    if project.status == "processing" and project.processed_rows > 0:
        elapsed = (datetime.utcnow() - project.updated_at).total_seconds()
        rate = project.processed_rows / elapsed
        remaining = project.original_row_count - project.processed_rows
        estimated_time = int(remaining / rate) if rate > 0 else None
    else:
        estimated_time = None
    
    return schemas.EnrichmentProgress(
        project_id=project.id,
        status=project.status,
        processed_rows=project.processed_rows,
        total_rows=project.original_row_count,
        emails_found=project.emails_found,
        phones_found=project.phones_found,
        facebook_data_found=project.facebook_data_found,
        websites_scraped=project.websites_scraped,
        current_contact=None,  # Could track this if needed
        estimated_time_remaining=estimated_time
    )


@router.get("/projects/{project_id}/contacts", response_model=List[schemas.EnrichedContact])
async def get_project_contacts(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get enriched contacts for a project"""
    project = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.id == project_id,
        models.EnrichmentProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    contacts = db.query(models.EnrichedContact).filter(
        models.EnrichedContact.project_id == project_id
    ).offset(skip).limit(limit).all()
    
    return contacts


@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    export_request: schemas.ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export enriched data as CSV"""
    project = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.id == project_id,
        models.EnrichmentProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get contacts
    query = db.query(models.EnrichedContact).filter(
        models.EnrichedContact.project_id == project_id
    )
    
    if export_request.only_enriched:
        query = query.filter(
            (models.EnrichedContact.email_found != None) | 
            (models.EnrichedContact.phone_found != None)
        )
    
    contacts = query.all()
    
    # Build CSV
    output = io.StringIO()
    
    if contacts:
        # Get all possible columns
        first_contact = contacts[0]
        fieldnames = []
        
        if export_request.include_original:
            fieldnames.extend(first_contact.original_data.keys())
        
        # Add enriched fields
        enriched_fields = [
            'email_found', 'email_confidence', 'email_source', 'email_valid',
            'phone_found', 'phone_confidence', 'phone_source',
            'facebook_followers', 'facebook_recent_post', 'facebook_post_date',
            'website_scraped', 'data_completeness_score', 'enriched_at'
        ]
        fieldnames.extend(enriched_fields)
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for contact in contacts:
            row = {}
            
            if export_request.include_original:
                row.update(contact.original_data)
            
            # Add enriched data
            for field in enriched_fields:
                value = getattr(contact, field, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value)
                row[field] = value
            
            writer.writerow(row)
    
    # Return CSV
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=enriched_{project.name}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an enrichment project"""
    project = db.query(models.EnrichmentProject).filter(
        models.EnrichmentProject.id == project_id,
        models.EnrichmentProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/test-serp-api")
async def test_serp_api(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Test SERP API configuration"""
    import os
    from serpapi import GoogleSearch
    
    serp_key = os.getenv("SERP_API_KEY")
    if not serp_key:
        return {
            "status": "error",
            "message": "SERP_API_KEY not found in environment variables"
        }
    
    try:
        # Test with a simple search
        search = GoogleSearch({
            "q": "test",
            "api_key": serp_key,
            "num": 1
        })
        
        results = search.get_dict()
        
        return {
            "status": "success",
            "message": "SERP API is working correctly",
            "search_metadata": results.get("search_metadata", {}),
            "remaining_searches": results.get("search_metadata", {}).get("credits_remaining")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"SERP API error: {str(e)}"
        }


# Background task function
async def enrich_project_contacts(project_id: str):
    """Background task to enrich all contacts in a project"""
    from core.database import SessionLocal
    import asyncio
    
    try:
        enricher = services.ContactEnricher()
    except ValueError as e:
        # Handle missing API key
        logger.error(f"Failed to initialize enricher: {str(e)}")
        with SessionLocal() as db:
            project = db.query(models.EnrichmentProject).filter(
                models.EnrichmentProject.id == project_id
            ).first()
            if project:
                project.status = "failed"
                project.error_message = "SERP_API_KEY not configured in environment"
                db.commit()
        return
    
    with SessionLocal() as db:
        project = db.query(models.EnrichmentProject).filter(
            models.EnrichmentProject.id == project_id
        ).first()
        
        if not project:
            return
        
        contacts = db.query(models.EnrichedContact).filter(
            models.EnrichedContact.project_id == project_id
        ).all()
        
        for i, contact in enumerate(contacts):
            try:
                # Enrich contact
                enriched_data = await enricher.enrich_contact(contact.original_data)
                
                # Update contact with enriched data
                update_contact_with_enrichment(contact, enriched_data)
                
                # Update project stats
                project.processed_rows = i + 1
                if contact.email_found:
                    project.emails_found += 1
                if contact.phone_found:
                    project.phones_found += 1
                if contact.facebook_followers:
                    project.facebook_data_found += 1
                if contact.website_scraped:
                    project.websites_scraped += 1
                
                project.enriched_rows += 1
                project.updated_at = datetime.utcnow()
                
                db.commit()
                
                # Rate limiting
                await asyncio.sleep(1)  # Reduced from 2 seconds to 1 second
                
            except Exception as e:
                logger.error(f"Error enriching contact {contact.name}: {str(e)}")
                contact.errors.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e)
                })
                
                # If this is a critical error (like API key issues), mark project as failed
                error_str = str(e).lower()
                if any(critical in error_str for critical in ['api key', 'unauthorized', 'forbidden', 'invalid key']):
                    project.status = "failed"
                    project.error_message = f"API Error: {str(e)}"
                    db.commit()
                    logger.error(f"Critical error, stopping enrichment: {str(e)}")
                    return
                
                db.commit()
                continue
        
        # Mark project as completed
        project.status = "completed"
        project.completed_at = datetime.utcnow()
        db.commit()


def update_contact_with_enrichment(contact: models.EnrichedContact, 
                                   enriched_data: Dict[str, Any]):
    """Update contact model with enriched data"""
    results = enriched_data.get('enrichment_results', {})
    
    # Email data
    best_email = None
    email_confidence = 0.0
    email_source = None
    
    # Check all sources for emails
    if 'google' in results:
        for email_data in results['google'].get('emails', []):
            if email_data['confidence'] > email_confidence:
                best_email = email_data['email']
                email_confidence = email_data['confidence']
                email_source = 'google'
    
    if 'website' in results:
        website_emails = results['website'].get('emails', [])
        if website_emails:
            best_email = website_emails[0]
            email_confidence = 0.9
            email_source = 'website'
            contact.website_emails = website_emails
    
    if 'facebook' in results:
        fb_emails = results['facebook'].get('emails', [])
        if fb_emails:
            best_email = fb_emails[0]
            email_confidence = 0.95
            email_source = 'facebook'
    
    if best_email:
        contact.email_found = best_email
        contact.email_confidence = email_confidence * 100
        contact.email_source = email_source
    
    # Email validation
    if 'email_validation' in results and best_email:
        validation = results['email_validation']
        contact.email_valid = validation.get('valid')
        contact.email_validation_details = validation
    
    # Phone data
    best_phone = None
    phone_confidence = 0.0
    phone_source = None
    
    if 'google' in results:
        for phone_data in results['google'].get('phones', []):
            if phone_data['confidence'] > phone_confidence:
                best_phone = phone_data['phone']
                phone_confidence = phone_data['confidence']
                phone_source = 'google'
    
    if 'website' in results:
        website_phones = results['website'].get('phones', [])
        if website_phones:
            best_phone = website_phones[0]
            phone_confidence = 0.9
            phone_source = 'website'
            contact.website_phones = website_phones
    
    if best_phone:
        contact.phone_found = best_phone
        contact.phone_confidence = phone_confidence * 100
        contact.phone_source = phone_source
        contact.phone_formatted = best_phone
    
    # Facebook data
    if 'facebook' in results:
        fb_data = results['facebook']
        contact.facebook_followers = fb_data.get('followers')
        
        posts = fb_data.get('posts', [])
        if posts:
            recent_post = posts[0]
            contact.facebook_recent_post = recent_post.get('message')
            contact.facebook_post_date = datetime.fromisoformat(
                recent_post.get('created_time')
            ) if recent_post.get('created_time') else None
            contact.facebook_engagement = {
                'likes': recent_post.get('likes', 0),
                'comments': recent_post.get('comments', 0),
                'shares': recent_post.get('shares', 0)
            }
        
        contact.facebook_page_info = fb_data
        contact.facebook_last_checked = datetime.utcnow()
    
    # Website data
    if 'website' in results:
        website_data = results['website']
        contact.website_social_links = website_data.get('social_links', {})
        contact.website_scraped = website_data.get('scraped', False)
        contact.website_scrape_date = datetime.utcnow()
    
    # Calculate scores
    contact.data_completeness_score = calculate_completeness_score(contact)
    contact.confidence_score = calculate_confidence_score(contact)


def calculate_completeness_score(contact: models.EnrichedContact) -> float:
    """Calculate data completeness score (0-100)"""
    score = 0.0
    fields = [
        (contact.email_found, 30),
        (contact.phone_found, 30),
        (contact.facebook_followers is not None, 20),
        (contact.website_scraped, 10),
        (contact.email_valid is not None, 10)
    ]
    
    for field, weight in fields:
        if field:
            score += weight
    
    return score


def calculate_confidence_score(contact: models.EnrichedContact) -> float:
    """Calculate overall confidence score (0-100)"""
    scores = []
    
    if contact.email_confidence:
        scores.append(contact.email_confidence)
    
    if contact.phone_confidence:
        scores.append(contact.phone_confidence)
    
    if contact.email_valid is True:
        scores.append(100)
    elif contact.email_valid is False:
        scores.append(0)
    
    if scores:
        return sum(scores) / len(scores)
    
    return 0.0 