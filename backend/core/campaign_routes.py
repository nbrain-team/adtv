from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, text, func
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
from datetime import datetime
import csv
import io
import json
import logging

from . import auth
from .database import get_db, User, Campaign, CampaignContact, CampaignTemplate, CampaignAnalytics, CampaignEmailTemplate, engine
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
    video_link: Optional[str] = None
    event_link: Optional[str] = None
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
    owner_phone: Optional[str] = None
    video_link: Optional[str] = None
    event_link: Optional[str] = None
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
    owner_phone: Optional[str] = None
    video_link: Optional[str] = None
    event_link: Optional[str] = None
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
    # RSVP fields
    is_rsvp: Optional[bool] = False
    rsvp_status: Optional[str] = None
    rsvp_date: Optional[datetime] = None

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

class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body: str
    template_type: str = 'general'

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    template_type: Optional[str] = None
    is_active: Optional[bool] = None

class BulkRSVPUpdate(BaseModel):
    contact_ids: List[str]
    is_rsvp: bool = True
    rsvp_status: Optional[str] = None

class RSVPStatusUpdate(BaseModel):
    rsvp_status: str  # attended, no_show, signed_agreement, cancelled

class SendCommunication(BaseModel):
    template_id: str
    contact_ids: Optional[List[str]] = None  # If None, send to all RSVPs

# Campaign CRUD
def safe_campaign_response(campaign) -> dict:
    """Safely convert a Campaign object to a response dict, handling missing fields"""
    return {
        "id": campaign.id,
        "name": campaign.name,
        "owner_name": campaign.owner_name,
        "owner_email": campaign.owner_email,
        "owner_phone": getattr(campaign, 'owner_phone', None),
        "video_link": getattr(campaign, 'video_link', None),
        "event_link": getattr(campaign, 'event_link', None),
        "launch_date": campaign.launch_date,
        "event_type": campaign.event_type,
        "event_date": campaign.event_date,
        "event_times": campaign.event_times,
        "target_cities": campaign.target_cities,
        "hotel_name": campaign.hotel_name,
        "hotel_address": campaign.hotel_address,
        "calendly_link": campaign.calendly_link,
        "status": campaign.status,
        "total_contacts": campaign.total_contacts,
        "enriched_contacts": campaign.enriched_contacts,
        "failed_enrichments": campaign.failed_enrichments,
        "emails_generated": campaign.emails_generated,
        "emails_sent": campaign.emails_sent,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at
    }

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
    
    return safe_campaign_response(campaign)

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
    
    return [safe_campaign_response(campaign) for campaign in campaigns]

@router.get("/all-contacts")
async def get_all_campaign_contacts(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all contacts from all campaigns for the current user"""
    try:
        logger.info(f"Fetching all contacts for user: {current_user.id}")
        
        # Get all campaigns for the user
        campaigns = db.query(Campaign).filter(
            Campaign.user_id == current_user.id
        ).all()
        
        logger.info(f"Found {len(campaigns)} campaigns for user {current_user.id}")
        
        # If no campaigns, return empty array
        if not campaigns:
            logger.info("No campaigns found, returning empty array")
            return []
        
        # Get all contacts from these campaigns
        campaign_ids = [c.id for c in campaigns]
        logger.info(f"Campaign IDs: {campaign_ids}")
        
        contacts = db.query(CampaignContact).filter(
            CampaignContact.campaign_id.in_(campaign_ids)
        ).all()
        
        logger.info(f"Found {len(contacts)} contacts across all campaigns")
        
        # Add campaign names to contacts
        campaign_map = {c.id: c.name for c in campaigns}
        
        # Properly serialize contacts
        result = []
        for i, contact in enumerate(contacts):
            try:
                contact_dict = {
                    'id': contact.id,
                    'campaign_id': contact.campaign_id,
                    'campaign_name': campaign_map.get(contact.campaign_id, ''),
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'email': contact.email,
                    'company': contact.company,
                    'title': contact.title,
                    'phone': contact.phone,
                    'neighborhood': contact.neighborhood,
                    'state': getattr(contact, 'state', None),  # Safe access
                    'geocoded_address': getattr(contact, 'geocoded_address', None),  # Safe access
                    # Enriched data
                    'enriched_company': contact.enriched_company,
                    'enriched_title': contact.enriched_title,
                    'enriched_phone': contact.enriched_phone,
                    'enriched_linkedin': contact.enriched_linkedin,
                    'enriched_website': contact.enriched_website,
                    'enriched_industry': contact.enriched_industry,
                    'enriched_company_size': contact.enriched_company_size,
                    'enriched_location': contact.enriched_location,
                    # Email data
                    'personalized_email': contact.personalized_email,
                    'personalized_subject': contact.personalized_subject,
                    # Status
                    'enrichment_status': contact.enrichment_status,
                    'email_status': contact.email_status,
                    'excluded': contact.excluded,
                    'manually_edited': getattr(contact, 'manually_edited', False),  # Safe access
                    # Timestamps
                    'created_at': contact.created_at.isoformat() if contact.created_at else None,
                    'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
                    # RSVP fields
                    'is_rsvp': contact.is_rsvp,
                    'rsvp_status': contact.rsvp_status,
                    'rsvp_date': contact.rsvp_date
                }
                result.append(contact_dict)
            except Exception as e:
                logger.error(f"Error serializing contact {i} (ID: {contact.id}): {str(e)}")
                logger.error(f"Contact attributes: {dir(contact)}")
                raise
        
        logger.info(f"Successfully serialized {len(result)} contacts")
        return result
    except Exception as e:
        logger.error(f"Error fetching all contacts: {str(e)}", exc_info=True)
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
    
    return safe_campaign_response(campaign)

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
    
    return safe_campaign_response(campaign)

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

@router.get("/{campaign_id}/export-incomplete")
async def export_incomplete_contacts(
    campaign_id: str,
    missing_fields: str = "email,phone",  # Comma-separated list of fields to check
    logic: str = "or",  # "or" = missing any field, "and" = missing all fields
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export contacts with missing email or phone fields as CSV"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Parse the fields to check
    fields_to_check = [field.strip() for field in missing_fields.split(',')]
    
    # Query all contacts for the campaign
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    ).all()
    
    # Filter contacts with missing fields
    incomplete_contacts = []
    for contact in contacts:
        missing_conditions = []
        
        if 'email' in fields_to_check:
            # Check if email is missing
            is_missing_email = not contact.email or contact.email.strip() == ''
            missing_conditions.append(is_missing_email)
            
        if 'phone' in fields_to_check:
            # Check both phone and enriched_phone fields
            has_original_phone = contact.phone and contact.phone.strip() != ''
            has_enriched_phone = contact.enriched_phone and contact.enriched_phone.strip() != ''
            is_missing_phone = not has_original_phone and not has_enriched_phone
            missing_conditions.append(is_missing_phone)
        
        # Apply logic (OR vs AND)
        if logic == "and":
            # Include only if ALL specified fields are missing
            if all(missing_conditions):
                incomplete_contacts.append(contact)
        else:  # default "or" logic
            # Include if ANY specified field is missing
            if any(missing_conditions):
                incomplete_contacts.append(contact)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers - include both original and enriched fields
    headers = [
        'id', 'first_name', 'last_name', 'email', 'phone', 'enriched_phone',
        'company', 'enriched_company', 'title', 'enriched_title', 
        'neighborhood', 'state', 'geocoded_address'
    ]
    writer.writerow(headers)
    
    # Write data - ensure we export all available data
    for contact in incomplete_contacts:
        writer.writerow([
            contact.id,
            contact.first_name or '',
            contact.last_name or '',
            contact.email or '',  # This should export the email if it exists
            contact.phone or '',
            contact.enriched_phone or '',
            contact.company or '',
            contact.enriched_company or '',  # Also include enriched company
            contact.title or '',
            contact.enriched_title or '',  # Also include enriched title
            contact.neighborhood or '',
            contact.state or '',
            contact.geocoded_address or ''
        ])
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{campaign.name.replace(' ', '_')}_incomplete_contacts_{timestamp}.csv"
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/{campaign_id}/export-all")
async def export_all_contacts(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export all contacts as CSV"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Query all contacts for the campaign
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    ).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers - include all fields
    headers = [
        'id', 'first_name', 'last_name', 'email', 'phone', 
        'company', 'title', 'neighborhood', 'state', 'geocoded_address',
        'enriched_company', 'enriched_title', 'enriched_phone', 
        'enriched_linkedin', 'enriched_website', 'enriched_industry',
        'enriched_company_size', 'enriched_location', 'enrichment_status',
        'excluded', 'is_rsvp', 'rsvp_status'
    ]
    writer.writerow(headers)
    
    # Write data
    for contact in contacts:
        writer.writerow([
            contact.id,
            contact.first_name or '',
            contact.last_name or '',
            contact.email or '',
            contact.phone or '',
            contact.company or '',
            contact.title or '',
            contact.neighborhood or '',
            contact.state or '',
            contact.geocoded_address or '',
            contact.enriched_company or '',
            contact.enriched_title or '',
            contact.enriched_phone or '',
            contact.enriched_linkedin or '',
            contact.enriched_website or '',
            contact.enriched_industry or '',
            contact.enriched_company_size or '',
            contact.enriched_location or '',
            contact.enrichment_status or '',
            'Yes' if contact.excluded else 'No',
            'Yes' if contact.is_rsvp else 'No',
            contact.rsvp_status or ''
        ])
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{campaign.name.replace(' ', '_')}_all_contacts_{timestamp}.csv"
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/{campaign_id}/reimport-contacts")
async def reimport_enriched_contacts(
    campaign_id: str,
    file: UploadFile = File(...),
    merge_strategy: str = "update",  # "update" or "replace"
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Re-import enriched contacts, matching by ID and updating specified fields"""
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
        
        updated_count = 0
        not_found_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, 1):
            try:
                # Get contact ID
                contact_id = row.get('id', '').strip()
                if not contact_id:
                    error_count += 1
                    errors.append(f"Row {row_num}: Missing contact ID")
                    continue
                
                # Find existing contact
                contact = db.query(CampaignContact).filter(
                    CampaignContact.id == contact_id,
                    CampaignContact.campaign_id == campaign_id
                ).first()
                
                if not contact:
                    not_found_count += 1
                    errors.append(f"Row {row_num}: Contact ID {contact_id} not found in campaign")
                    continue
                
                # Update fields based on merge strategy
                if merge_strategy == "replace":
                    # Replace all provided fields
                    for field in ['first_name', 'last_name', 'email', 'phone', 
                                 'company', 'title', 'neighborhood', 'state', 'geocoded_address']:
                        if field in row:
                            setattr(contact, field, row[field].strip() if row[field] else None)
                else:  # "update" - only update empty fields
                    for field in ['first_name', 'last_name', 'email', 'phone', 
                                 'company', 'title', 'neighborhood', 'state', 'geocoded_address']:
                        if field in row and row[field] and row[field].strip():
                            current_value = getattr(contact, field)
                            if not current_value or current_value.strip() == '':
                                setattr(contact, field, row[field].strip())
                
                contact.updated_at = datetime.utcnow()
                updated_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
        
        # Commit all changes
        db.commit()
        
        # Update campaign analytics
        total_contacts = db.query(func.count(CampaignContact.id)).filter(
            CampaignContact.campaign_id == campaign_id
        ).scalar()
        
        contacts_with_email = db.query(func.count(CampaignContact.id)).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.email != None,
            CampaignContact.email != ''
        ).scalar()
        
        contacts_with_phone = db.query(func.count(CampaignContact.id)).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.phone != None,
            CampaignContact.phone != ''
        ).scalar()
        
        campaign.total_contacts = total_contacts
        db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "not_found_count": not_found_count,
            "error_count": error_count,
            "errors": errors[:10],  # Return first 10 errors
            "total_contacts": total_contacts,
            "contacts_with_email": contacts_with_email,
            "contacts_with_phone": contacts_with_phone
        }
        
    except Exception as e:
        logger.error(f"Failed to reimport contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.get("/{campaign_id}/contacts/stats")
async def get_contact_stats(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics about campaign contacts"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    total_contacts = db.query(func.count(CampaignContact.id)).filter(
        CampaignContact.campaign_id == campaign_id
    ).scalar()
    
    contacts_with_email = db.query(func.count(CampaignContact.id)).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.email != None,
        CampaignContact.email != ''
    ).scalar()
    
    contacts_with_phone = db.query(func.count(CampaignContact.id)).filter(
        CampaignContact.campaign_id == campaign_id,
        ((CampaignContact.phone != None) & (CampaignContact.phone != '')) |
        ((CampaignContact.enriched_phone != None) & (CampaignContact.enriched_phone != ''))
    ).scalar()
    
    contacts_missing_both = db.query(func.count(CampaignContact.id)).filter(
        CampaignContact.campaign_id == campaign_id,
        (CampaignContact.email == None) | (CampaignContact.email == ''),
        ((CampaignContact.phone == None) | (CampaignContact.phone == '')) &
        ((CampaignContact.enriched_phone == None) | (CampaignContact.enriched_phone == ''))
    ).scalar()
    
    contacts_missing_email = db.query(func.count(CampaignContact.id)).filter(
        CampaignContact.campaign_id == campaign_id,
        (CampaignContact.email == None) | (CampaignContact.email == '')
    ).scalar()
    
    contacts_missing_phone = db.query(func.count(CampaignContact.id)).filter(
        CampaignContact.campaign_id == campaign_id,
        ((CampaignContact.phone == None) | (CampaignContact.phone == '')) &
        ((CampaignContact.enriched_phone == None) | (CampaignContact.enriched_phone == ''))
    ).scalar()
    
    return {
        "total_contacts": total_contacts,
        "contacts_with_email": contacts_with_email,
        "contacts_with_phone": contacts_with_phone,
        "contacts_missing_both": contacts_missing_both,
        "contacts_missing_email": contacts_missing_email,
        "contacts_missing_phone": contacts_missing_phone,
        "email_coverage_percentage": round((contacts_with_email / total_contacts * 100) if total_contacts > 0 else 0, 1),
        "phone_coverage_percentage": round((contacts_with_phone / total_contacts * 100) if total_contacts > 0 else 0, 1)
    }

@router.get("/{campaign_id}/contacts/diagnostic")
async def get_contact_diagnostic(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed diagnostic information about contacts"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get all contacts
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id
    ).all()
    
    # Analyze each contact
    diagnostic_data = []
    for contact in contacts[:10]:  # Sample first 10 for diagnostics
        has_email = bool(contact.email and contact.email.strip())
        has_phone = bool(contact.phone and contact.phone.strip())
        has_enriched_phone = bool(contact.enriched_phone and contact.enriched_phone.strip())
        
        diagnostic_data.append({
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "has_email": has_email,
            "phone": contact.phone,
            "has_phone": has_phone,
            "enriched_phone": contact.enriched_phone,
            "has_enriched_phone": has_enriched_phone,
            "has_any_phone": has_phone or has_enriched_phone,
            "missing_email": not has_email,
            "missing_any_phone": not (has_phone or has_enriched_phone),
            "missing_both": not has_email and not (has_phone or has_enriched_phone)
        })
    
    # Count statistics
    total = len(contacts)
    with_email = sum(1 for c in contacts if c.email and c.email.strip())
    with_original_phone = sum(1 for c in contacts if c.phone and c.phone.strip())
    with_enriched_phone = sum(1 for c in contacts if c.enriched_phone and c.enriched_phone.strip())
    with_any_phone = sum(1 for c in contacts if (c.phone and c.phone.strip()) or (c.enriched_phone and c.enriched_phone.strip()))
    missing_email = total - with_email
    missing_any_phone = total - with_any_phone
    missing_both = sum(1 for c in contacts if not (c.email and c.email.strip()) and not ((c.phone and c.phone.strip()) or (c.enriched_phone and c.enriched_phone.strip())))
    missing_either = sum(1 for c in contacts if not (c.email and c.email.strip()) or not ((c.phone and c.phone.strip()) or (c.enriched_phone and c.enriched_phone.strip())))
    
    return {
        "summary": {
            "total_contacts": total,
            "with_email": with_email,
            "with_original_phone": with_original_phone,
            "with_enriched_phone": with_enriched_phone,
            "with_any_phone": with_any_phone,
            "missing_email": missing_email,
            "missing_any_phone": missing_any_phone,
            "missing_both_email_and_phone": missing_both,
            "missing_either_email_or_phone": missing_either,
            "email_coverage_percentage": round((with_email / total * 100) if total > 0 else 0, 1),
            "phone_coverage_percentage": round((with_any_phone / total * 100) if total > 0 else 0, 1)
        },
        "sample_contacts": diagnostic_data
    }

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
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async enrichment
        try:
            enriched_count, failed_count = loop.run_until_complete(
                enrich_contacts_concurrently(
                    contacts, campaign_id, enricher, db, SessionLocal
                )
            )
        finally:
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

async def enrich_contacts_concurrently(contacts, campaign_id, enricher, db, SessionLocal):
    """
    Enrich multiple contacts concurrently with rate limiting.
    Process up to 20 contacts at once - database pool now supports 50 connections.
    SERP API supports 300 queries/second, so API is not the bottleneck.
    """
    import asyncio
    
    # Now we can safely process 20 concurrent with our increased database pool
    # Database pool: 20 permanent + 30 overflow = 50 total connections
    # We use 20 concurrent to leave room for other operations
    MAX_CONCURRENT = 20  # Increased from 5 after expanding database pool
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    enriched_count = 0
    failed_count = 0
    total_contacts = len(contacts)
    
    async def process_single_contact(contact, index):
        """Process a single contact with rate limiting"""
        async with semaphore:
            # Use a separate session for each contact to avoid conflicts
            contact_db = SessionLocal()
            try:
                # Get fresh contact from database
                fresh_contact = contact_db.query(CampaignContact).filter(
                    CampaignContact.id == contact.id
                ).first()
                
                if not fresh_contact:
                    logger.error(f"Contact {contact.id} not found")
                    return 0, 1
                
                # Check if campaign still exists (only check every 50 contacts)
                if index % 50 == 0:
                    campaign_check = contact_db.query(Campaign).filter(
                        Campaign.id == campaign_id
                    ).first()
                    if not campaign_check:
                        logger.warning(f"Campaign {campaign_id} no longer exists, stopping enrichment")
                        return 0, 0
                
                # Check if this contact has been cancelled
                if fresh_contact.enrichment_status == 'cancelled':
                    logger.info(f"Contact {fresh_contact.id} cancelled, skipping")
                    return 0, 0
                
                # Log progress every 10 contacts
                if index % 10 == 0 or index < 5:
                    logger.info(f"Processing contact {index+1}/{total_contacts} ({(index+1)/total_contacts*100:.1f}%)")
                
                logger.debug(f"Enriching: {fresh_contact.first_name} {fresh_contact.last_name} at {fresh_contact.company}")
                fresh_contact.enrichment_status = 'processing'
                contact_db.commit()

                # Prepare data for enrichment
                state = fresh_contact.state or 'Alabama'
                contact_data = {
                    'Name': f"{fresh_contact.first_name} {fresh_contact.last_name}".strip(),
                    'Company': fresh_contact.company or '',
                    'Email': fresh_contact.email or '',
                    'Phone': fresh_contact.phone or '',
                    'City': fresh_contact.neighborhood or '',
                    'State': state
                }
                
                # Enrich contact
                enriched_data = await enricher.enrich_contact(contact_data)
                
                # Process enrichment results
                success = False
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
                        
                        if best_email and not fresh_contact.email:
                            fresh_contact.email = best_email
                        
                        # Extract best phone
                        best_phone = None
                        best_phone_confidence = 0
                        for phone_data in google_data.get('phones', []):
                            if phone_data.get('confidence', 0) > best_phone_confidence:
                                best_phone = phone_data['phone']
                                best_phone_confidence = phone_data.get('confidence', 0)
                        
                        if best_phone:
                            fresh_contact.enriched_phone = best_phone
                        
                        # Extract LinkedIn
                        for source in google_data.get('sources', []):
                            if 'linkedin.com' in source.lower():
                                fresh_contact.enriched_linkedin = source
                                break
                    
                    # Process website scraping results
                    if 'website' in results:
                        website_data = results['website']
                        
                        website_emails = website_data.get('emails', [])
                        if website_emails and not fresh_contact.email:
                            fresh_contact.email = website_emails[0]
                        
                        website_phones = website_data.get('phones', [])
                        if website_phones and not fresh_contact.enriched_phone:
                            fresh_contact.enriched_phone = website_phones[0]
                        
                        fresh_contact.enriched_company = website_data.get('company_name') or fresh_contact.company
                        fresh_contact.enriched_location = website_data.get('location') or fresh_contact.enriched_location
                        fresh_contact.enriched_industry = website_data.get('industry')
                        fresh_contact.enriched_website = website_data.get('website')
                    
                    # Process Facebook results
                    if 'facebook' in results:
                        facebook_data = results['facebook']
                        fb_emails = facebook_data.get('emails', [])
                        if fb_emails and not fresh_contact.email:
                            fresh_contact.email = fb_emails[0]
                        
                        fb_phones = facebook_data.get('phones', [])
                        if fb_phones and not fresh_contact.enriched_phone:
                            fresh_contact.enriched_phone = fb_phones[0]
                    
                    # Use original values as fallback
                    fresh_contact.enriched_company = fresh_contact.enriched_company or fresh_contact.company
                    fresh_contact.enriched_title = fresh_contact.enriched_title or fresh_contact.title
                    
                    fresh_contact.enrichment_status = 'success'
                    success = True
                    logger.info(f"Successfully enriched contact {index+1}/{total_contacts}")
                    
                    # Update progress counter for successful enrichments
                    # processed_count += 1 # This variable is not defined in this scope
                    if index % 25 == 0:  # Log every 25 contacts processed
                        elapsed_time = (datetime.utcnow() - datetime.utcnow()).total_seconds()  # You'd need to track start time
                        logger.info(f"Progress: {index+1}/{total_contacts} contacts enriched ({((index+1)/total_contacts)*100:.1f}%)")
                else:
                    fresh_contact.enrichment_status = 'failed'
                    fresh_contact.enrichment_error = 'No enrichment data found'
                    logger.warning(f"No enrichment data found for contact {index+1}/{total_contacts}")
                    # processed_count += 1 # This variable is not defined in this scope
                
                fresh_contact.updated_at = datetime.utcnow()
                contact_db.commit()
                
                return (1 if success else 0), (0 if success else 1)
                
            except Exception as e:
                logger.error(f"Error enriching contact {index+1}/{total_contacts}: {str(e)}")
                return 0, 1
            finally:
                # CRITICAL: Always close the database session to return connection to pool
                contact_db.close()
    
    # Log initial status
    logger.info(f"Starting concurrent enrichment of {total_contacts} contacts with {MAX_CONCURRENT} workers")
    
    # Process all contacts concurrently
    tasks = [process_single_contact(contact, i) for i, contact in enumerate(contacts)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successes and failures
    for i, result in enumerate(results):
        if isinstance(result, tuple):
            enriched_count += result[0]
            failed_count += result[1]
        elif isinstance(result, Exception):
            # Exception occurred
            failed_count += 1
            logger.error(f"Task {i+1} exception: {result}")
    
    # Log final results
    logger.info(f"Enrichment complete: {enriched_count} successful, {failed_count} failed out of {total_contacts} total")
    
    return enriched_count, failed_count

def generate_campaign_emails(campaign_id: str, user_id: str):
    """Background task to generate emails using mail merge only (no AI personalization)"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return
        
        # Record start time
        analytics = None
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
            db.rollback()
        
        # Ensure we have a clean session state
        db.commit()
        
        # Get contacts to generate emails for
        contacts = db.query(CampaignContact).filter(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.enrichment_status == 'success',
            CampaignContact.excluded == False,
            CampaignContact.email_status == 'pending'
        ).all()
        
        generated_count = 0
        
        for contact in contacts:
            try:
                # Simple mail merge - no AI personalization
                email_body = campaign.email_template or ''
                email_subject = campaign.email_subject or ''
                
                # Parse event times into Date1/Time1, Date2/Time2, Date3/Time3
                date1 = date2 = date3 = ""
                time1 = time2 = time3 = ""
                
                if campaign.event_times and len(campaign.event_times) > 0:
                    date1 = campaign.event_date.strftime('%A, %B %d')
                    time1 = campaign.event_times[0] if campaign.event_times[0] else ''
                if campaign.event_times and len(campaign.event_times) > 1:
                    date2 = campaign.event_date.strftime('%A, %B %d')
                    time2 = campaign.event_times[1]
                if campaign.event_times and len(campaign.event_times) > 2:
                    date3 = campaign.event_date.strftime('%A, %B %d')
                    time3 = campaign.event_times[2]
                
                # Extract city and state from target_cities
                city = ''
                state = ''
                if campaign.target_cities:
                    # Assuming format like "Chicago, Illinois" or just "Chicago"
                    parts = campaign.target_cities.split(',')
                    city = parts[0].strip() if parts else ''
                    state = parts[1].strip() if len(parts) > 1 else ''
                
                # Campaign-level replacements (double square brackets)
                campaign_replacements = {
                    '[[VIDEO-LINK]]': getattr(campaign, 'video_link', 'https://vimeo.com/adtv-intro'),
                    '[[City]]': city,
                    '[[State]]': state,
                    '[[Event-Link]]': getattr(campaign, 'event_link', campaign.calendly_link or ''),
                    '[[Date1]]': date1,
                    '[[Time1]]': time1,
                    '[[Date2]]': date2,
                    '[[Time2]]': time2,
                    '[[Date3]]': date3,
                    '[[Time3]]': time3,
                    '[[Hotel Name]]': campaign.hotel_name or '',
                    '[[Hotel Address]]': campaign.hotel_address or '',
                    '[[Associate Name]]': campaign.owner_name,
                    '[[Associate email]]': campaign.owner_email,
                    '[[Associate Phone]]': getattr(campaign, 'owner_phone', ''),
                    '[[Calendly Link]]': campaign.calendly_link or '',
                    # Legacy field names for backward compatibility
                    '[[HotelName]]': campaign.hotel_name or '',
                    '[[HotelAddress]]': campaign.hotel_address or '',
                    '[[AssociateName]]': campaign.owner_name,
                    '[[AssociatePhone]]': getattr(campaign, 'owner_phone', ''),
                }
                
                # Contact-level replacements (double curly braces)
                contact_replacements = {
                    '{{FirstName}}': contact.first_name or '',
                    '{{LastName}}': contact.last_name or '',
                    '{{Neighborhood_1}}': contact.neighborhood or '',
                    '{{Email}}': contact.email or '',
                    '{{Company}}': contact.enriched_company or contact.company or '',
                    '{{Title}}': contact.enriched_title or contact.title or '',
                    '{{Phone}}': contact.enriched_phone or contact.phone or '',
                    # Legacy field names for backward compatibility
                    '{{first_name}}': contact.first_name or '',
                    '{{last_name}}': contact.last_name or '',
                    '{{neighborhood}}': contact.neighborhood or '',
                    '{{email}}': contact.email or '',
                    '{{company}}': contact.enriched_company or contact.company or '',
                    '{{title}}': contact.enriched_title or contact.title or '',
                    '{{phone}}': contact.enriched_phone or contact.phone or '',
                }
                
                # Apply all replacements
                for key, value in campaign_replacements.items():
                    email_body = email_body.replace(key, value)
                    email_subject = email_subject.replace(key, value)
                
                for key, value in contact_replacements.items():
                    email_body = email_body.replace(key, value)
                    email_subject = email_subject.replace(key, value)
                
                # Store the mail-merged email
                contact.personalized_email = email_body
                contact.personalized_subject = email_subject
                contact.email_status = 'generated'
                generated_count += 1
                
            except Exception as e:
                contact.email_status = 'failed'
                logger.error(f"Error generating email for contact {contact.id}: {e}")
            
            contact.updated_at = datetime.utcnow()
            db.commit()
        
        # Update campaign stats
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
            if analytics:
                analytics.email_generation_end_time = datetime.utcnow()
                analytics.emails_generated = generated_count
                db.commit()
        except Exception as e:
            logger.warning(f"Could not update analytics end time: {e}")
            db.rollback()
        
    except Exception as e:
        logger.error(f"Error generating emails: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        db.close()

# Email Template Management Endpoints
@router.get("/{campaign_id}/email-templates")
def get_campaign_email_templates(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all email templates for a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    templates = db.query(CampaignEmailTemplate).filter(
        CampaignEmailTemplate.campaign_id == campaign_id
    ).all()
    
    return templates

@router.post("/{campaign_id}/email-templates")
def create_campaign_email_template(
    campaign_id: str,
    template: EmailTemplateCreate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new email template for a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db_template = CampaignEmailTemplate(
        campaign_id=campaign_id,
        name=template.name,
        subject=template.subject,
        body=template.body,
        template_type=template.template_type
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template

@router.put("/{campaign_id}/email-templates/{template_id}")
def update_campaign_email_template(
    campaign_id: str,
    template_id: str,
    template_update: EmailTemplateUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an email template"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db_template = db.query(CampaignEmailTemplate).filter(
        CampaignEmailTemplate.id == template_id,
        CampaignEmailTemplate.campaign_id == campaign_id
    ).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(db_template, field, value)
    
    db_template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_template)
    
    return db_template

@router.delete("/{campaign_id}/email-templates/{template_id}")
def delete_campaign_email_template(
    campaign_id: str,
    template_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an email template"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db_template = db.query(CampaignEmailTemplate).filter(
        CampaignEmailTemplate.id == template_id,
        CampaignEmailTemplate.campaign_id == campaign_id
    ).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    
    return {"message": "Template deleted successfully"}

# RSVP Management Endpoints
@router.post("/{campaign_id}/contacts/rsvp")
def update_contacts_rsvp(
    campaign_id: str,
    rsvp_update: BulkRSVPUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark contacts as RSVP"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.id.in_(rsvp_update.contact_ids)
    ).all()
    
    for contact in contacts:
        contact.is_rsvp = rsvp_update.is_rsvp
        if rsvp_update.is_rsvp:
            contact.rsvp_date = datetime.utcnow()
            if rsvp_update.rsvp_status:
                contact.rsvp_status = rsvp_update.rsvp_status
        else:
            contact.rsvp_date = None
            contact.rsvp_status = None
    
    db.commit()
    
    return {"message": f"Updated {len(contacts)} contacts"}

@router.put("/{campaign_id}/contacts/{contact_id}/rsvp-status")
def update_contact_rsvp_status(
    campaign_id: str,
    contact_id: str,
    status_update: RSVPStatusUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update RSVP status for a contact"""
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
    
    contact.rsvp_status = status_update.rsvp_status
    contact.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contact)
    
    return contact

@router.get("/{campaign_id}/contacts/rsvp")
def get_rsvp_contacts(
    campaign_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all RSVP contacts for a campaign"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    contacts = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.is_rsvp == True
    ).all()
    
    return contacts

@router.post("/{campaign_id}/send-communication")
async def send_communication_to_rsvps(
    campaign_id: str,
    communication: SendCommunication,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send email communication to RSVP contacts"""
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get the template
    template = db.query(CampaignEmailTemplate).filter(
        CampaignEmailTemplate.id == communication.template_id,
        CampaignEmailTemplate.campaign_id == campaign_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get contacts to send to
    query = db.query(CampaignContact).filter(
        CampaignContact.campaign_id == campaign_id,
        CampaignContact.is_rsvp == True,
        CampaignContact.email.isnot(None)
    )
    
    if communication.contact_ids:
        query = query.filter(CampaignContact.id.in_(communication.contact_ids))
    
    contacts = query.all()
    
    if not contacts:
        raise HTTPException(status_code=400, detail="No RSVP contacts with email addresses found")
    
    # Process emails in background
    background_tasks.add_task(
        send_rsvp_emails_task,
        campaign_id,
        template.id,
        [c.id for c in contacts]
    )
    
    return {
        "message": f"Sending emails to {len(contacts)} RSVP contacts",
        "template": template.name,
        "recipient_count": len(contacts)
    }

def send_rsvp_emails_task(campaign_id: str, template_id: str, contact_ids: List[str]):
    """Background task to send RSVP emails"""
    from sqlalchemy.orm import sessionmaker
    import asyncio
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        template = db.query(CampaignEmailTemplate).filter(
            CampaignEmailTemplate.id == template_id
        ).first()
        
        if not template:
            logger.error(f"Template {template_id} not found")
            return
        
        contacts = db.query(CampaignContact).filter(
            CampaignContact.id.in_(contact_ids)
        ).all()
        
        sent_count = 0
        for contact in contacts:
            try:
                # Replace placeholders in template
                subject = template.subject
                body = template.body
                
                # Simple mail merge - replace {{field_name}} with contact data
                replacements = {
                    'first_name': contact.first_name or '',
                    'last_name': contact.last_name or '',
                    'email': contact.email or '',
                    'company': contact.company or '',
                    'title': contact.title or '',
                    'phone': contact.phone or '',
                    'neighborhood': contact.neighborhood or '',
                    'state': contact.state or ''
                }
                
                for field, value in replacements.items():
                    subject = subject.replace(f'{{{{{field}}}}}', value)
                    body = body.replace(f'{{{{{field}}}}}', value)
                
                # Here you would integrate with your email sending service
                # For now, we'll just mark it as sent
                contact.email_status = 'sent'
                contact.email_sent_at = datetime.utcnow()
                sent_count += 1
                
                logger.info(f"Sent email to {contact.email}")
                
            except Exception as e:
                logger.error(f"Error sending email to contact {contact.id}: {e}")
                contact.email_status = 'failed'
        
        db.commit()
        logger.info(f"Successfully sent {sent_count} emails for campaign {campaign_id}")
        
    except Exception as e:
        logger.error(f"Error in send_rsvp_emails_task: {e}")
        db.rollback()
        raise 