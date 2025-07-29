from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
from datetime import datetime
import csv
import io
import json
import logging

from . import auth
from .database import get_db, User, Campaign, CampaignContact, CampaignTemplate, CampaignAnalytics, engine
from contact_enricher.services import ContactEnricher
from core.llm_handler import generate_text

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    owner_name: str
    owner_email: EmailStr
    launch_date: datetime
    event_type: str  # 'virtual' or 'in_person'
    event_date: datetime
    event_times: Optional[List[str]] = []
    target_cities: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_address: Optional[str] = None
    calendly_link: Optional[str] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    launch_date: Optional[datetime] = None
    event_date: Optional[datetime] = None
    event_times: Optional[List[str]] = None
    target_cities: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_address: Optional[str] = None
    calendly_link: Optional[str] = None
    email_template: Optional[str] = None
    email_subject: Optional[str] = None

class CampaignResponse(BaseModel):
    id: str
    name: str
    owner_name: str
    owner_email: str
    launch_date: datetime
    event_type: str
    event_date: datetime
    event_times: Optional[List[str]]
    target_cities: Optional[str]
    hotel_name: Optional[str]
    hotel_address: Optional[str]
    calendly_link: Optional[str]
    status: str
    total_contacts: int
    enriched_contacts: int
    failed_enrichments: int
    emails_generated: int
    emails_sent: int
    created_at: datetime
    updated_at: datetime

class ContactResponse(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    company: Optional[str]
    title: Optional[str]
    neighborhood: Optional[str]
    enrichment_status: str
    email_status: str
    excluded: bool
    personalized_email: Optional[str]
    personalized_subject: Optional[str]

class CampaignTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    email_template: Optional[str] = None
    email_subject: Optional[str] = None

class CampaignTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    event_type: Optional[str]
    email_template: Optional[str]
    email_subject: Optional[str]
    created_at: datetime

class BulkContactUpdate(BaseModel):
    contact_ids: List[str]
    excluded: Optional[bool] = None

class ContactUpdate(BaseModel):
    personalized_email: Optional[str] = None
    personalized_subject: Optional[str] = None
    excluded: Optional[bool] = None

# Campaign CRUD
@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new campaign"""
    campaign = Campaign(
        user_id=current_user.id,
        **campaign_data.dict()
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # TODO: Send email notification to campaign owner
    
    return campaign

@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns for the current user"""
    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id
    ).order_by(desc(Campaign.created_at)).offset(skip).limit(limit).all()
    
    return campaigns

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    for field, value in campaign_data.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    campaign.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    
    return campaign

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted successfully"}

# Contact management
@router.post("/{campaign_id}/upload-contacts")
async def upload_contacts(
    campaign_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload contacts CSV for a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        # Read CSV
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_data)
        
        # Map possible column names to our fields
        column_mappings = {
            'first_name': ['first_name', 'firstname', 'first', 'fname', 'First Name'],
            'last_name': ['last_name', 'lastname', 'last', 'lname', 'Last Name'],
            'email': ['email', 'email_address', 'e-mail', 'Email', 'Email Address'],
            'company': ['company', 'company_name', 'organization', 'Company', 'Company Name'],
            'title': ['title', 'job_title', 'position', 'Title', 'Job Title', 'Position'],
            'phone': ['phone', 'phone_number', 'telephone', 'Phone', 'Phone Number', 'cell', 'Cell Phone'],
            'neighborhood': ['neighborhood', 'neighborhood 1', 'Neighborhood 1', 'Neighborhood', 'area', 'district']
        }
        
        contacts = []
        for row_num, row in enumerate(reader, 1):
            # Find the actual column names in the CSV
            contact_data = {}
            for field, possible_names in column_mappings.items():
                value = None
                for col_name in possible_names:
                    if col_name in row:
                        value = row[col_name]
                        break
                contact_data[field] = value or ''
            
            # Create contact with mapped data
            contact = CampaignContact(
                campaign_id=campaign_id,
                first_name=contact_data['first_name'],
                last_name=contact_data['last_name'],
                email=contact_data['email'],
                company=contact_data['company'],
                title=contact_data['title'],
                phone=contact_data['phone'],
                neighborhood=contact_data['neighborhood']
            )
            contacts.append(contact)
        
        if not contacts:
            raise HTTPException(status_code=400, detail="No valid contacts found in CSV")
        
        # Bulk insert contacts
        db.bulk_save_objects(contacts)
        
        # Update campaign stats
        campaign.total_contacts = len(contacts)
        campaign.status = 'enriching'
        
        db.commit()
        
        # Start enrichment in background
        background_tasks.add_task(enrich_campaign_contacts, campaign_id, current_user.id)
        
        return {
            "message": f"Uploaded {len(contacts)} contacts",
            "campaign_id": campaign_id,
            "status": "enriching"
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please ensure the CSV is UTF-8 encoded.")
    except Exception as e:
        print(f"Error uploading contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@router.get("/{campaign_id}/contacts", response_model=List[ContactResponse])
async def get_campaign_contacts(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    excluded: Optional[bool] = None,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get contacts for a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    query = db.query(CampaignContact).filter(CampaignContact.campaign_id == campaign_id)
    
    if excluded is not None:
        query = query.filter(CampaignContact.excluded == excluded)
    
    contacts = query.offset(skip).limit(limit).all()
    
    return contacts

@router.put("/{campaign_id}/contacts/bulk-update")
async def bulk_update_contacts(
    campaign_id: str,
    update_data: BulkContactUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk update contacts (exclude/include)"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update contacts
    db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.id.in_(update_data.contact_ids)
    ).update(
        {CampaignContact.excluded: update_data.excluded},
        synchronize_session=False
    )
    
    db.commit()
    
    return {"message": f"Updated {len(update_data.contact_ids)} contacts"}

@router.put("/{campaign_id}/contacts/{contact_id}")
async def update_contact(
    campaign_id: str,
    contact_id: str,
    update_data: ContactUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a single contact"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    contact = db.query(CampaignContact).filter(
        CampaignContact.id == contact_id,
        CampaignContact.campaign_id == campaign_id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(contact, field, value)
    
    if update_data.personalized_email is not None:
        contact.manually_edited = True
    
    contact.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Contact updated successfully"}

# Campaign templates
@router.post("/templates", response_model=CampaignTemplateResponse)
async def create_template(
    template_data: CampaignTemplateCreate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a campaign template"""
    template = CampaignTemplate(
        user_id=current_user.id,
        **template_data.dict()
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template

@router.get("/templates", response_model=List[CampaignTemplateResponse])
async def get_templates(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all campaign templates for the user"""
    templates = db.query(CampaignTemplate).filter(
        CampaignTemplate.user_id == current_user.id
    ).order_by(desc(CampaignTemplate.created_at)).all()
    
    return templates

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign template"""
    template = db.query(CampaignTemplate).filter(
        CampaignTemplate.id == template_id,
        CampaignTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted successfully"}

# Campaign actions
@router.post("/{campaign_id}/generate-emails")
async def generate_emails(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate personalized emails for all contacts"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != 'ready_for_personalization':
        raise HTTPException(
            status_code=400, 
            detail="Campaign must be in 'ready_for_personalization' status"
        )
    
    # Start email generation in background
    background_tasks.add_task(generate_campaign_emails, campaign_id, current_user.id)
    
    campaign.status = 'generating_emails'
    db.commit()
    
    return {"message": "Email generation started", "status": "generating_emails"}

@router.get("/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get campaign analytics"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get latest analytics
    analytics = db.query(CampaignAnalytics).filter(
        CampaignAnalytics.campaign_id == campaign_id
    ).order_by(desc(CampaignAnalytics.timestamp)).all()
    
    return {
        "campaign_id": campaign_id,
        "current_stats": {
            "total_contacts": campaign.total_contacts,
            "enriched_contacts": campaign.enriched_contacts,
            "failed_enrichments": campaign.failed_enrichments,
            "emails_generated": campaign.emails_generated,
            "emails_sent": campaign.emails_sent,
            "enrichment_success_rate": (
                campaign.enriched_contacts / campaign.total_contacts * 100 
                if campaign.total_contacts > 0 else 0
            )
        },
        "timeline": analytics
    }

@router.get("/{campaign_id}/enrichment-status")
async def get_enrichment_status(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed enrichment status for a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get contact status breakdown
    pending = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.enrichment_status == 'pending'
    ).count()
    
    processing = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.enrichment_status == 'processing'
    ).count()
    
    success = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.enrichment_status == 'success'
    ).count()
    
    failed = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.enrichment_status == 'failed'
    ).count()
    
    # Get failed contacts with errors
    failed_contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.enrichment_status == 'failed'
    ).limit(10).all()
    
    return {
        "campaign_id": campaign_id,
        "status": campaign.status,
        "total_contacts": campaign.total_contacts,
        "enrichment_breakdown": {
            "pending": pending,
            "processing": processing,
            "success": success,
            "failed": failed
        },
        "progress_percentage": round((success + failed) / campaign.total_contacts * 100, 2) if campaign.total_contacts > 0 else 0,
        "failed_samples": [
            {
                "name": f"{c.first_name} {c.last_name}".strip(),
                "company": c.company,
                "error": c.enrichment_error
            }
            for c in failed_contacts
        ]
    }

# Background tasks
def enrich_campaign_contacts(campaign_id: str, user_id: str):
    """Background task to enrich campaign contacts"""
    from sqlalchemy.orm import sessionmaker
    import asyncio
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    logger.info(f"Starting enrichment for campaign {campaign_id}")
    
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return
        
        # Record start time
        analytics = CampaignAnalytics(
            campaign_id=campaign_id,
            enrichment_start_time=datetime.utcnow(),
            contacts_uploaded=campaign.total_contacts
        )
        db.add(analytics)
        
        # Get contacts to enrich
        contacts = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.enrichment_status == 'pending'
        ).all()
        
        logger.info(f"Found {len(contacts)} contacts to enrich for campaign {campaign_id}")
        
        enricher = ContactEnricher()
        enriched_count = 0
        failed_count = 0
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for i, contact in enumerate(contacts):
            try:
                logger.info(f"Enriching contact {i+1}/{len(contacts)}: {contact.first_name} {contact.last_name} at {contact.company}")
                contact.enrichment_status = 'processing'
                db.commit()
                
                # Enrich contact - map to expected field names
                enriched_data = loop.run_until_complete(enricher.enrich_contact({
                    'Name': f"{contact.first_name} {contact.last_name}".strip(),
                    'Company': contact.company or '',
                    'Email': contact.email or '',
                    'Phone': contact.phone or ''
                }))
                
                # Extract enrichment results
                if enriched_data and 'enrichment_results' in enriched_data:
                    results = enriched_data['enrichment_results']
                    
                    # Update contact with enriched data from various sources
                    if 'google' in results:
                        google_data = results['google']
                        contact.enriched_phone = google_data.get('phone') or contact.enriched_phone
                        contact.enriched_linkedin = google_data.get('linkedin_url') or contact.enriched_linkedin
                        contact.enriched_website = google_data.get('website') or contact.enriched_website
                    
                    if 'website' in results:
                        website_data = results['website']
                        contact.enriched_company = website_data.get('company_name') or contact.company
                        contact.enriched_location = website_data.get('location') or contact.enriched_location
                    
                    # Use original values as fallback
                    contact.enriched_company = contact.enriched_company or contact.company
                    contact.enriched_title = contact.enriched_title or contact.title
                    
                    contact.enrichment_status = 'success'
                    enriched_count += 1
                    logger.info(f"Successfully enriched contact {i+1}/{len(contacts)}")
                else:
                    contact.enrichment_status = 'failed'
                    contact.enrichment_error = 'No enrichment data found'
                    failed_count += 1
                    logger.warning(f"No enrichment data found for contact {i+1}/{len(contacts)}")
                    
            except Exception as e:
                contact.enrichment_status = 'failed'
                contact.enrichment_error = str(e)
                failed_count += 1
                logger.error(f"Error enriching contact {i+1}/{len(contacts)}: {str(e)}")
            
            contact.updated_at = datetime.utcnow()
            db.commit()
            
            # Update campaign stats periodically
            if (i + 1) % 10 == 0:
                campaign.enriched_contacts = enriched_count
                campaign.failed_enrichments = failed_count
                db.commit()
                logger.info(f"Progress: {i+1}/{len(contacts)} contacts processed")
        
        # Close the event loop
        loop.close()
        
        # Update campaign stats
        campaign.enriched_contacts = enriched_count
        campaign.failed_enrichments = failed_count
        campaign.status = 'ready_for_personalization'
        
        # Record end time
        analytics.enrichment_end_time = datetime.utcnow()
        analytics.contacts_enriched = enriched_count
        analytics.enrichment_success_rate = (
            enriched_count / len(contacts) * 100 if contacts else 0
        )
        
        db.commit()
        
        # TODO: Send notification email to campaign owner
        
    except Exception as e:
        print(f"Error enriching contacts: {e}")
    finally:
        db.close()

def generate_campaign_emails(campaign_id: str, user_id: str):
    """Background task to generate personalized emails"""
    from sqlalchemy.orm import sessionmaker
    import asyncio
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return
        
        # Record start time
        analytics = db.query(CampaignAnalytics).filter(
            CampaignAnalytics.campaign_id == campaign_id
        ).order_by(desc(CampaignAnalytics.timestamp)).first()
        
        if analytics:
            analytics.email_generation_start_time = datetime.utcnow()
        
        # Get contacts to generate emails for
        contacts = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.enrichment_status == 'success',
            CampaignContact.excluded == False,
            CampaignContact.email_status == 'pending'
        ).all()
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        generated_count = 0
        
        for contact in contacts:
            try:
                # Generate personalized email
                # TODO: Use actual email template and personalization logic
                prompt = f"""
                Generate a personalized email for:
                Name: {contact.first_name} {contact.last_name}
                Company: {contact.enriched_company or contact.company}
                Title: {contact.enriched_title or contact.title}
                
                Event Details:
                Type: {campaign.event_type}
                Date: {campaign.event_date}
                {'Hotel: ' + campaign.hotel_name if campaign.hotel_name else ''}
                {'Calendly: ' + campaign.calendly_link if campaign.calendly_link else ''}
                
                Template: {campaign.email_template or 'Create a professional invitation email'}
                """
                
                # Generate email using async function
                email_content = loop.run_until_complete(generate_text(prompt))
                
                contact.personalized_email = email_content
                contact.personalized_subject = campaign.email_subject or f"Invitation: {campaign.name}"
                contact.email_status = 'generated'
                generated_count += 1
                
            except Exception as e:
                contact.email_status = 'failed'
                print(f"Error generating email for contact {contact.id}: {e}")
            
            contact.updated_at = datetime.utcnow()
            db.commit()
        
        # Close the event loop
        loop.close()
        
        # Update campaign stats
        campaign.emails_generated = generated_count
        campaign.status = 'ready_to_send'
        
        # Record end time
        if analytics:
            analytics.email_generation_end_time = datetime.utcnow()
            analytics.emails_generated = generated_count
        
        db.commit()
        
        # TODO: Send notification email to campaign owner
        
    except Exception as e:
        print(f"Error generating emails: {e}")
    finally:
        db.close() 