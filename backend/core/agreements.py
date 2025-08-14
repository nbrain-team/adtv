from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional
import hashlib
import json
import uuid
from pydantic import BaseModel, EmailStr
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import base64

from .database import get_db, Base, engine

# Define router without a prefix; the app includes it with "/api/agreements"
router = APIRouter(tags=["agreements"])

# Database Model
class Agreement(Base):
    __tablename__ = "agreements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, nullable=False)
    contact_id = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    company = Column(String)
    start_date = Column(String, nullable=False)
    setup_fee = Column(Float, nullable=False)
    monthly_fee = Column(Float, nullable=False)
    campaign_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, viewed, signed
    signature = Column(Text)
    signature_type = Column(String)  # typed, drawn
    signed_date = Column(String)
    signed_at = Column(DateTime)
    viewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pdf_data = Column(Text)  # Store generated PDF as base64
    agreement_url = Column(String)

# Create table if it doesn't exist
Base.metadata.create_all(bind=engine)

# Pydantic Models
class AgreementResponse(BaseModel):
    id: str
    contact_name: str
    contact_email: str
    company: Optional[str]
    start_date: str
    setup_fee: float
    monthly_fee: float
    campaign_name: str
    status: str
    signed_at: Optional[datetime]
    signature: Optional[str]

class SignAgreementRequest(BaseModel):
    signature: str
    signature_type: str = "typed"
    signed_date: str

# Endpoints
@router.get("/{agreement_id}")
async def get_agreement(
    agreement_id: str,
    db: Session = Depends(get_db)
):
    """Get agreement details for signing page"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    return AgreementResponse(
        id=agreement.id,
        contact_name=agreement.contact_name,
        contact_email=agreement.contact_email,
        company=agreement.company,
        start_date=agreement.start_date,
        setup_fee=agreement.setup_fee,
        monthly_fee=agreement.monthly_fee,
        campaign_name=agreement.campaign_name,
        status=agreement.status,
        signed_at=agreement.signed_at,
        signature=agreement.signature
    )

@router.post("/{agreement_id}/view")
async def mark_agreement_viewed(
    agreement_id: str,
    db: Session = Depends(get_db)
):
    """Mark agreement as viewed"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status == "pending":
        agreement.status = "viewed"
        agreement.viewed_at = datetime.utcnow()
        
        # Update related campaign contact if available
        try:
            from .database import CampaignContact
            contact = db.query(CampaignContact).filter(CampaignContact.id == agreement.contact_id).first()
            if contact and getattr(contact, 'agreement_status', None) is not None:
                contact.agreement_status = 'viewed'
        except Exception:
            pass
        
        db.commit()
    
    return {"status": "viewed"}

@router.post("/{agreement_id}/sign")
async def sign_agreement(
    agreement_id: str,
    sign_request: SignAgreementRequest,
    db: Session = Depends(get_db)
):
    """Sign the agreement"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status == "signed":
        raise HTTPException(status_code=400, detail="Agreement already signed")
    
    # Update agreement with signature
    agreement.signature = sign_request.signature
    agreement.signature_type = sign_request.signature_type
    agreement.signed_date = sign_request.signed_date
    agreement.signed_at = datetime.utcnow()
    agreement.status = "signed"
    
    # Generate PDF
    pdf_buffer = generate_agreement_pdf(agreement)
    agreement.pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    
    # Update related campaign contact if available
    try:
        from .database import CampaignContact
        contact = db.query(CampaignContact).filter(CampaignContact.id == agreement.contact_id).first()
        if contact and getattr(contact, 'agreement_status', None) is not None:
            contact.agreement_status = 'signed'
            if hasattr(contact, 'agreement_signed_at'):
                contact.agreement_signed_at = agreement.signed_at
    except Exception:
        pass
    
    db.commit()
    
    # Here you would send confirmation email with PDF attachment
    # send_confirmation_email(agreement)
    
    return {
        "status": "signed",
        "signed_at": agreement.signed_at,
        "pdf_available": True
    }

@router.get("/{agreement_id}/pdf")
async def get_agreement_pdf(
    agreement_id: str,
    db: Session = Depends(get_db)
):
    """Download signed agreement PDF"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status != "signed":
        # Generate preview PDF for unsigned agreements
        pdf_buffer = generate_agreement_pdf(agreement)
        pdf_data = pdf_buffer.getvalue()
    else:
        # Use stored PDF for signed agreements
        if agreement.pdf_data:
            pdf_data = base64.b64decode(agreement.pdf_data)
        else:
            # Generate if not stored
            pdf_buffer = generate_agreement_pdf(agreement)
            pdf_data = pdf_buffer.getvalue()
    
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=agreement_{agreement_id}.pdf"
        }
    )

def generate_agreement_pdf(agreement: Agreement) -> io.BytesIO:
    """Generate PDF version of the agreement"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5282'),
        spaceBefore=20,
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Title
    elements.append(Paragraph("SERVICE AGREEMENT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Agreement ID and Date
    info_data = [
        ['Agreement ID:', agreement.id[:8]],
        ['Date:', agreement.start_date],
        ['Campaign:', agreement.campaign_name]
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Parties
    elements.append(Paragraph("PARTIES", heading_style))
    party_data = [
        ['Service Provider:', 'ADTV Corporation'],
        ['Client Name:', agreement.contact_name],
        ['Client Email:', agreement.contact_email],
        ['Company:', agreement.company or 'N/A']
    ]
    party_table = Table(party_data, colWidths=[2*inch, 4*inch])
    party_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(party_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Investment
    elements.append(Paragraph("INVESTMENT", heading_style))
    investment_data = [
        ['One-time Setup Fee:', f'${agreement.setup_fee:,.2f}'],
        ['Monthly Service Fee:', f'${agreement.monthly_fee:,.2f}'],
        ['Service Start Date:', agreement.start_date]
    ]
    investment_table = Table(investment_data, colWidths=[2*inch, 4*inch])
    investment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e6f3ff')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(investment_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Terms (simplified)
    elements.append(Paragraph("TERMS & CONDITIONS", heading_style))
    terms = """
    1. <b>Services:</b> ADTV Corporation agrees to provide marketing and advertising services.<br/>
    2. <b>Payment:</b> Setup fee due upon signing, monthly fee recurring.<br/>
    3. <b>Term:</b> Month-to-month, 30 days notice for cancellation.<br/>
    4. <b>Confidentiality:</b> Both parties agree to maintain confidentiality.<br/>
    5. <b>Governing Law:</b> Subject to applicable state laws.
    """
    elements.append(Paragraph(terms, normal_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Signature Section
    if agreement.status == "signed":
        elements.append(Paragraph("ELECTRONIC SIGNATURE", heading_style))
        sig_data = [
            ['Signed By:', agreement.signature or ''],
            ['Date:', agreement.signed_date or ''],
            ['Timestamp:', agreement.signed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if agreement.signed_at else '']
        ]
        sig_table = Table(sig_data, colWidths=[2*inch, 4*inch])
        sig_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
            ('FONT', (1, 0), (1, 0), 'Helvetica-Oblique', 14),  # Signature in italic
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d4f4dd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(sig_table)
    else:
        elements.append(Paragraph("UNSIGNED AGREEMENT - PREVIEW ONLY", heading_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer 