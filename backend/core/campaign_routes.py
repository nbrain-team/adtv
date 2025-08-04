from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
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
    owner_phone: Optional[str] = None
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
    owner_phone: Optional[str] = None

class CampaignResponse(BaseModel):
    id: str
    name: str
    owner_name: str
    owner_email: str
    # owner_phone: Optional[str]  # TEMPORARILY DISABLED UNTIL MIGRATION RUNS
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
    phone: Optional[str]
    neighborhood: Optional[str]
    # Enriched data
    enriched_company: Optional[str]
    enriched_title: Optional[str]
    enriched_phone: Optional[str]
    enriched_linkedin: Optional[str]
    enriched_website: Optional[str]
    enriched_industry: Optional[str]
    enriched_company_size: Optional[str]
    enriched_location: Optional[str]
    # Status
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
        **campaign_data.dict(exclude={'owner_phone'})  # Exclude owner_phone until migration runs
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

@router.get("/all-contacts")
async def get_all_campaign_contacts(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all contacts from all campaigns for the current user"""
    try:
        # Get all campaigns for the user
        campaigns = db.query(Campaign).filter(
            Campaign.user_id == current_user.id
        ).all()
        
        # If no campaigns, return empty array
        if not campaigns:
            return []
        
        # Get all contacts from these campaigns
        campaign_ids = [c.id for c in campaigns]
        contacts = db.query(CampaignContact).filter(
            CampaignContact.campaign_id.in_(campaign_ids)
        ).all()
        
        # Add campaign names to contacts
        campaign_map = {c.id: c.name for c in campaigns}
        
        return [{
            **contact.__dict__,
            'campaign_name': campaign_map.get(contact.campaign_id, '')
        } for contact in contacts]
    except Exception as e:
        logger.error(f"Error fetching all contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Campaign templates - static routes before dynamic routes
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
    
    for field, value in campaign_data.dict(exclude_unset=True, exclude={'owner_phone'}).items():
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
    """Delete a campaign and stop all background tasks"""
    try:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Stop any running background tasks by marking contacts as cancelled
        db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.enrichment_status.in_(['pending', 'processing'])
        ).update({
            'enrichment_status': 'cancelled',
            'enrichment_error': 'Campaign deleted'
        }, synchronize_session=False)
        
        # Delete related records first to avoid foreign key issues
        # Delete analytics records
        db.query(CampaignAnalytics).filter(
            CampaignAnalytics.campaign_id == campaign_id
        ).delete(synchronize_session=False)
        
        # Delete contacts
        db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id
        ).delete(synchronize_session=False)
        
        # Now delete the campaign
        db.delete(campaign)
        db.commit()
        
        logger.info(f"Successfully deleted campaign {campaign_id}")
        return {"message": "Campaign deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
        # If it's a column error, try to delete without cascade
        if "column" in str(e) and "does not exist" in str(e):
            try:
                # Try direct deletion without relying on relationships
                db.execute(text("DELETE FROM campaign_analytics WHERE campaign_id = :campaign_id"), 
                          {"campaign_id": campaign_id})
                db.execute(text("DELETE FROM campaign_contacts WHERE campaign_id = :campaign_id"), 
                          {"campaign_id": campaign_id})
                db.execute(text("DELETE FROM campaigns WHERE id = :campaign_id"), 
                          {"campaign_id": campaign_id})
                db.commit()
                return {"message": "Campaign deleted successfully"}
            except Exception as e2:
                db.rollback()
                logger.error(f"Direct deletion also failed: {str(e2)}")
                raise HTTPException(status_code=500, detail=f"Failed to delete campaign: {str(e2)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete campaign: {str(e)}")

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
            'name': ['Name', 'name', 'full_name', 'Full Name', 'Contact Name'],
            'first_name': ['first_name', 'firstname', 'first', 'fname', 'First Name'],
            'last_name': ['last_name', 'lastname', 'last', 'lname', 'Last Name'],
            'email': ['email', 'email_address', 'e-mail', 'Email', 'Email Address'],
            'company': ['company', 'company_name', 'organization', 'Company', 'Company Name'],
            'title': ['title', 'job_title', 'position', 'Title', 'Job Title', 'Position'],
            'phone': ['phone', 'phone_number', 'telephone', 'Phone', 'Phone Number', 'cell', 'Cell Phone'],
            'neighborhood': ['neighborhood', 'neighborhood_1', 'Neighborhood 1', 'Neighborhood', 'area', 'district']
        }
        
        # Log CSV headers for debugging
        if reader.fieldnames:
            logger.info(f"CSV headers found: {reader.fieldnames}")
        
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
            
            # Handle full name if first/last names are not provided separately
            if contact_data.get('name') and not (contact_data['first_name'] or contact_data['last_name']):
                name_parts = contact_data['name'].strip().split(' ', 1)
                contact_data['first_name'] = name_parts[0] if name_parts else ''
                contact_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
            
            # Clean up neighborhood data - remove state abbreviation if present
            if contact_data['neighborhood']:
                # Handle format like "Madison AL" -> "Madison"
                neighborhood_parts = contact_data['neighborhood'].strip().rsplit(' ', 1)
                if len(neighborhood_parts) == 2 and len(neighborhood_parts[1]) == 2 and neighborhood_parts[1].isupper():
                    # Looks like "Neighborhood ST" format
                    contact_data['neighborhood'] = neighborhood_parts[0]
                    contact_data['state'] = neighborhood_parts[1]  # Store state for enrichment
                    # Create geocoded address for Google Maps
                    contact_data['geocoded_address'] = f"{neighborhood_parts[0]}, {neighborhood_parts[1]}, USA"
                else:
                    contact_data['state'] = ''
                    # Try to determine state and format address
                    neighborhood = contact_data['neighborhood'].strip()
                    # Check if it's an Alabama city (default assumption based on your data)
                    alabama_cities = [
                        'Madison', 'Huntsville', 'Birmingham', 'Montgomery', 'Mobile',
                        'Tuscaloosa', 'Auburn', 'Decatur', 'Florence', 'Dothan',
                        'Hoover', 'Vestavia Hills', 'Prattville', 'Opelika', 'Enterprise',
                        'Northport', 'Anniston', 'Phenix City', 'Moontown', 'Monrovia',
                        'Research Park', 'Weatherly Heights', 'Meridianville', 'New Market', 'Ryland'
                    ]
                    
                    # Clean up common variations
                    clean_neighborhood = neighborhood.replace(', Huntsville', '').replace(', Alabama', '').strip()
                    
                    if any(city.lower() in clean_neighborhood.lower() for city in alabama_cities):
                        contact_data['state'] = 'AL'
                        contact_data['geocoded_address'] = f"{clean_neighborhood}, AL, USA"
                    else:
                        # Default to Alabama if no state specified
                        contact_data['state'] = 'AL'
                        contact_data['geocoded_address'] = f"{neighborhood}, AL, USA"
            else:
                contact_data['geocoded_address'] = ''
            
            # Skip rows where all key fields are empty (name or company required)
            if not any([contact_data['first_name'], contact_data['last_name'], contact_data['company']]):
                logger.debug(f"Skipping row {row_num} - no name or company data")
                continue
            
            # Log first few rows for debugging
            if row_num <= 3:
                logger.info(f"Row {row_num} data: {contact_data}")
            
            # Create contact with mapped data
            contact = CampaignContact(
                campaign_id=campaign_id,
                first_name=contact_data['first_name'],
                last_name=contact_data['last_name'],
                email=contact_data['email'],  # Can be empty
                company=contact_data['company'],
                title=contact_data['title'],
                phone=contact_data['phone'],  # Can be empty
                neighborhood=contact_data['neighborhood'],
                state=contact_data.get('state', ''),  # Save state properly
                geocoded_address=contact_data.get('geocoded_address', '')  # Save geocoded address
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
    
    # Get current contact stats
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    ).all()
    
    contacts_with_email = sum(1 for c in contacts if c.email)
    contacts_with_phone = sum(1 for c in contacts if c.enriched_phone or c.phone)
    
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
            ),
            "email_capture_rate": (
                contacts_with_email / len(contacts) * 100
                if contacts else 0
            ),
            "phone_capture_rate": (
                contacts_with_phone / len(contacts) * 100
                if contacts else 0
            ),
            "contacts_with_email": contacts_with_email,
            "contacts_with_phone": contacts_with_phone
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
        try:
            analytics = CampaignAnalytics(
                campaign_id=campaign_id,
                enrichment_start_time=datetime.utcnow(),
                contacts_uploaded=campaign.total_contacts
            )
            db.add(analytics)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not create analytics record: {e}")
            db.rollback()
            # Create a minimal analytics record without new fields
            analytics = None
        
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
                # Check if campaign still exists every 10 contacts
                if i % 10 == 0:
                    campaign_check = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                    if not campaign_check:
                        logger.warning(f"Campaign {campaign_id} no longer exists, stopping enrichment")
                        break
                
                # Check if this contact has been cancelled
                db.refresh(contact)
                if contact.enrichment_status == 'cancelled':
                    logger.info(f"Contact {contact.id} cancelled, skipping")
                    continue
                
                logger.info(f"Enriching contact {i+1}/{len(contacts)}: {contact.first_name} {contact.last_name} at {contact.company}")
                contact.enrichment_status = 'processing'
                db.commit()
                
                # Enrich contact using the exact same format as contact enricher
                state = contact.state or 'Alabama'  # Use stored state or default to Alabama for this campaign
                
                # Prepare data in the exact format expected by ContactEnricher
                contact_data = {
                    'Name': f"{contact.first_name} {contact.last_name}".strip(),
                    'Company': contact.company or '',
                    'Email': contact.email or '',
                    'Phone': contact.phone or '',
                    'City': contact.neighborhood or '',  # Use neighborhood as city for location-based searches
                    'State': state
                }
                
                logger.info(f"Enriching with data: {contact_data}")
                
                enriched_data = loop.run_until_complete(enricher.enrich_contact(contact_data))
                
                # Extract enrichment results using the same logic as contact enricher
                if enriched_data and 'enrichment_results' in enriched_data:
                    results = enriched_data['enrichment_results']
                    
                    # Process Google SERP results
                    if 'google' in results:
                        google_data = results['google']
                        
                        # Extract best email
                        best_email = None
                        best_email_confidence = 0
                        for email_data in google_data.get('emails', []):
                            if email_data['confidence'] > best_email_confidence:
                                best_email = email_data['email']
                                best_email_confidence = email_data['confidence']
                        
                        if best_email and not contact.email:  # Only update if no original email
                            contact.email = best_email
                        
                        # Extract best phone
                        best_phone = None
                        best_phone_confidence = 0
                        for phone_data in google_data.get('phones', []):
                            if phone_data.get('confidence', 0) > best_phone_confidence:
                                best_phone = phone_data['phone']
                                best_phone_confidence = phone_data.get('confidence', 0)
                        
                        if best_phone:
                            contact.enriched_phone = best_phone
                        
                        # Extract LinkedIn from sources
                        for source in google_data.get('sources', []):
                            if 'linkedin.com' in source.lower():
                                contact.enriched_linkedin = source
                                break
                    
                    # Process website scraping results
                    if 'website' in results:
                        website_data = results['website']
                        
                        # Website emails take priority
                        website_emails = website_data.get('emails', [])
                        if website_emails and not contact.email:
                            contact.email = website_emails[0]
                        
                        # Website phones
                        website_phones = website_data.get('phones', [])
                        if website_phones and not contact.enriched_phone:
                            contact.enriched_phone = website_phones[0]
                        
                        # Company info
                        contact.enriched_company = website_data.get('company_name') or contact.company
                        contact.enriched_location = website_data.get('location') or contact.enriched_location
                        contact.enriched_industry = website_data.get('industry')
                        contact.enriched_website = website_data.get('website')
                    
                    # Process Facebook results if available
                    if 'facebook' in results:
                        facebook_data = results['facebook']
                        fb_emails = facebook_data.get('emails', [])
                        if fb_emails and not contact.email:
                            contact.email = fb_emails[0]
                        
                        fb_phones = facebook_data.get('phones', [])
                        if fb_phones and not contact.enriched_phone:
                            contact.enriched_phone = fb_phones[0]
                    
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
        db.commit()  # Commit the status change immediately
        
        # Calculate email and phone capture rates
        all_contacts = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id
        ).all()
        
        contacts_with_email = sum(1 for c in all_contacts if c.email)
        contacts_with_phone = sum(1 for c in all_contacts if c.enriched_phone or c.phone)
        
        # Record end time and capture rates
        if analytics:
            try:
                analytics.enrichment_end_time = datetime.utcnow()
                analytics.contacts_enriched = enriched_count
                analytics.contacts_with_email = contacts_with_email
                analytics.contacts_with_phone = contacts_with_phone
                analytics.enrichment_success_rate = (
                    enriched_count / len(contacts) * 100 if contacts else 0
                )
                analytics.email_capture_rate = (
                    contacts_with_email / len(all_contacts) * 100 if all_contacts else 0
                )
                analytics.phone_capture_rate = (
                    contacts_with_phone / len(all_contacts) * 100 if all_contacts else 0
                )
                db.commit()
            except Exception as e:
                logger.warning(f"Could not update analytics: {e}")
                db.rollback()
        
        logger.info(f"Enrichment completed: {enriched_count}/{len(contacts)} successful")
        logger.info(f"Email capture rate: {(contacts_with_email / len(all_contacts) * 100 if all_contacts else 0):.1f}%")
        logger.info(f"Phone capture rate: {(contacts_with_phone / len(all_contacts) * 100 if all_contacts else 0):.1f}%")
        
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
        analytics = None  # Initialize analytics variable
        try:
            analytics = db.query(CampaignAnalytics).filter(
                CampaignAnalytics.campaign_id == campaign_id
            ).order_by(desc(CampaignAnalytics.timestamp)).first()
            
            if analytics:
                try:
                    analytics.email_generation_start_time = datetime.utcnow()
                    db.commit()
                except Exception as e:
                    logger.warning(f"Could not update analytics start time: {e}")
                    db.rollback()
        except Exception as e:
            logger.warning(f"Could not query analytics (likely missing columns): {e}")
            db.rollback()  # Clear the failed transaction
            # Continue without analytics - don't let this stop email generation
        
        # Ensure we have a clean session state
        db.commit()  # Commit any pending changes
        
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
                # Build the personalization context
                event_time = campaign.event_times[0] if campaign.event_times else ''
                
                # Map owner names to phone numbers
                owner_phones = {
                    'Kalena Conley': '(619) 374-7405',
                    'Evan Jones': '(619) 374-2561',
                    'Sigrid Smith': '(619) 292-8580',
                    'Amy Dodsworth': '(619) 259-0014',
                    'Bailey Jacobs': '(619) 333-0342'
                }
                
                # Get owner phone based on name
                owner_phone = owner_phones.get(campaign.owner_name, '(619) 374-7405')  # Default to Kalena's
                
                # Build template with all variables replaced
                template_with_vars = campaign.email_template or 'Create a professional invitation email'
                subject_with_vars = campaign.email_subject or f'Invitation: {campaign.name}'
                
                # Replace campaign-level variables
                replacements = {
                    # Single curly brace replacements (for backward compatibility)
                    '{event_date}': campaign.event_date.strftime('%B %d, %Y'),
                    '{event_time}': event_time,
                    '{hotel_name}': campaign.hotel_name or '',
                    '{hotel_address}': campaign.hotel_address or '',
                    '{calendly_link}': campaign.calendly_link or '',
                    '{owner_name}': campaign.owner_name,
                    '{campaign_name}': campaign.name,
                    '{target_cities}': campaign.target_cities or '',
                    '{first_name}': contact.first_name,
                    '{last_name}': contact.last_name,
                    '{company}': contact.enriched_company or contact.company or '',
                    '{title}': contact.enriched_title or contact.title or '',
                    # Double curly brace replacements (ADTV templates)
                    '{{FirstName}}': contact.first_name,
                    '{{City}}': campaign.target_cities.split('\n')[0] if campaign.target_cities else '',
                    '{{Market}}': contact.neighborhood or '',
                    '{{Markets}}': contact.neighborhood or '',
                    # Square bracket replacements (ADTV templates)
                    '[[Date1]]': f"{campaign.event_date.strftime('%A, %B %d')} at {campaign.event_times[0] if campaign.event_times else ''}",
                    '[[Date2]]': f"{campaign.event_date.strftime('%A, %B %d')} at {campaign.event_times[1] if campaign.event_times and len(campaign.event_times) > 1 else campaign.event_times[0] if campaign.event_times else ''}",
                    '[[HotelName]]': campaign.calendly_link if campaign.event_type == 'virtual' else (campaign.hotel_name or ''),
                    '[[HotelAddress]]': '' if campaign.event_type == 'virtual' else (campaign.hotel_address or ''),
                    '[[AssociateName]]': campaign.owner_name,
                    '[[Campaign Owner Name]]': campaign.owner_name,
                    '[[Campaign Owner Email]]': campaign.owner_email,
                    '[[Campaign Owner Phone]]': owner_phone,
                    '[[VideoLink]]': 'https://vimeo.com/adtv-intro', # Default video link
                    '[[InfoLink]]': 'https://adtv.com/info', # Default info link
                    '[[ContactInfo]]': campaign.owner_email,
                    '[[AssociatePhone]]': owner_phone
                }
                
                # Apply replacements
                for key, value in replacements.items():
                    template_with_vars = template_with_vars.replace(key, value)
                    subject_with_vars = subject_with_vars.replace(key, value)
                
                # Remove "Warm regards," if it exists (to match requested footer format)
                template_with_vars = template_with_vars.replace('Warm regards,\n', '')
                template_with_vars = template_with_vars.replace('Warm regards,', '')
                
                prompt = f"""
                You are writing a personalized email for a real estate TV show opportunity using the provided template.
                
                Recipient Information:
                - First Name: {contact.first_name}
                - Company: {contact.enriched_company or contact.company}
                - Neighborhood/Market: {contact.neighborhood or contact.enriched_location or ''}
                
                Campaign Details:
                - Event Type: {campaign.event_type}
                - Event Date: {campaign.event_date.strftime('%B %d, %Y')}
                - Event Time: {event_time}
                {'- Hotel: ' + campaign.hotel_name if campaign.hotel_name and campaign.event_type == 'in_person' else ''}
                {'- Address: ' + campaign.hotel_address if campaign.hotel_address and campaign.event_type == 'in_person' else ''}
                {'- Meeting Link: ' + campaign.calendly_link if campaign.calendly_link and campaign.event_type == 'virtual' else ''}
                - Host/Owner: {campaign.owner_name}
                
                Email Template:
                {template_with_vars}
                
                CRITICAL Instructions:
                1. Use ONLY the recipient's first name (not full name) when addressing them
                2. Focus on the uniqueness and importance of their specific neighborhood/market
                3. Highlight what makes their neighborhood special and why they're the expert there
                4. DO NOT mention any sales numbers or statistics
                5. Replace ALL placeholders in {{}} or [[]] with actual values
                6. REMOVE any instructional text in square brackets like [mention specific aspect] - these are instructions for you, not content for the email
                7. When you see [the real estate TV show], replace it with "Selling {campaign.target_cities.split()[0] if campaign.target_cities else 'your city'} on HGTV"
                8. Make it personal by referencing specific aspects of their neighborhood
                9. Keep the tone conversational and authentic
                10. Ensure the email flows naturally without any template markers or instructional brackets
                11. For virtual events, the meeting location should be the Calendly link
                12. Emphasize their expertise and reputation in their specific market area
                13. The email MUST end with this EXACT footer format (no "Warm regards," or other closing - just the signature):
                
                {campaign.owner_name}
                Associate Producer
                {campaign.owner_email}
                {owner_phone}
                
                The email should feel like it was written specifically for this person and their unique market expertise.
                Return only the final email body text with all placeholders replaced and NO bracketed instructions.
                """
                
                # Generate email using async function
                email_content = loop.run_until_complete(generate_text(prompt))
                
                contact.personalized_email = email_content
                contact.personalized_subject = subject_with_vars
                contact.email_status = 'generated'
                generated_count += 1
                
            except Exception as e:
                contact.email_status = 'failed'
                print(f"Error generating email for contact {contact.id}: {e}")
            
            contact.updated_at = datetime.utcnow()
            db.commit()
        
        # Close the event loop
        loop.close()
        
        # Update campaign stats and commit
        try:
            campaign.emails_generated = generated_count
            campaign.status = 'ready_to_send'
            db.commit()
            logger.info(f"Successfully generated {generated_count} emails for campaign {campaign_id}")
        except Exception as e:
            logger.error(f"Error updating campaign status: {e}")
            db.rollback()
        
        # Record end time
        try:
            if 'analytics' in locals() and analytics:
                try:
                    analytics.email_generation_end_time = datetime.utcnow()
                    analytics.emails_generated = generated_count
                    db.commit()
                except Exception as e:
                    logger.warning(f"Could not update analytics end time: {e}")
                    db.rollback()
        except Exception as e:
            logger.warning(f"Error updating analytics: {e}")
        
        # TODO: Send notification email to campaign owner
        
    except Exception as e:
        logger.error(f"Error generating emails: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        db.close() 