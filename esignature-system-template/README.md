# E-Signature Agreement System Template

## Overview
This is a complete e-signature agreement system that can be integrated into any web application. It provides a DocuSign-like experience for sending, viewing, and signing agreements digitally.

## Features
- 📝 **Digital Agreement Creation**: Generate personalized agreements from templates
- 🔗 **Unique Agreement URLs**: Each agreement gets a unique, secure URL
- ✍️ **Electronic Signatures**: Recipients can sign agreements digitally
- 📄 **PDF Generation**: Automatic PDF creation with embedded signatures
- 📧 **Email Notifications**: Optional email sending with agreement links
- 📊 **Status Tracking**: Track agreement lifecycle (sent, viewed, signed)
- 🔒 **Secure & Legal**: Audit trail with timestamps for compliance

## System Architecture

### Components
1. **Backend API** (Python/FastAPI)
   - Agreement management endpoints
   - PDF generation service
   - Email service (optional)
   - Database models

2. **Frontend UI** (React/TypeScript)
   - Agreement sending modal
   - Agreement signing page
   - Status tracking in tables

3. **Database Schema**
   - Agreements table
   - Contact tracking fields

## Quick Start Guide

### 1. Database Setup
```sql
-- Create agreements table
CREATE TABLE agreements (
    id VARCHAR PRIMARY KEY,
    campaign_id VARCHAR NOT NULL,
    contact_id VARCHAR NOT NULL,
    contact_name VARCHAR NOT NULL,
    contact_email VARCHAR NOT NULL,
    company VARCHAR,
    start_date VARCHAR NOT NULL,
    setup_fee FLOAT NOT NULL,
    monthly_fee FLOAT NOT NULL,
    campaign_name VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    signature TEXT,
    signature_type VARCHAR,
    signed_date VARCHAR,
    signed_at TIMESTAMP,
    viewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_data TEXT,
    agreement_url VARCHAR
);

-- Add tracking fields to contacts/users table
ALTER TABLE contacts ADD COLUMN agreement_status VARCHAR(50);
ALTER TABLE contacts ADD COLUMN agreement_sent_at TIMESTAMP;
ALTER TABLE contacts ADD COLUMN agreement_signed_at TIMESTAMP;
ALTER TABLE contacts ADD COLUMN agreement_data TEXT;
```

### 2. Backend Installation
```bash
pip install fastapi sqlalchemy reportlab
```

### 3. Frontend Installation
```bash
npm install @radix-ui/themes axios react-router-dom
```

## File Structure
```
esignature-system-template/
├── README.md
├── CURSOR_PROMPT.md           # AI prompt for implementation
├── backend/
│   ├── agreements.py          # Core agreement API
│   ├── email_service.py       # Email sending service
│   ├── models.py              # Database models
│   └── pdf_generator.py       # PDF generation
├── frontend/
│   ├── AgreementSigningPage.tsx    # Signing page component
│   ├── RSVPAgreementModal.tsx      # Sending modal component
│   └── AgreementStatusColumn.tsx   # Table column component
├── database/
│   └── schema.sql             # Database schema
└── docs/
    ├── API.md                 # API documentation
    ├── INTEGRATION.md         # Integration guide
    └── CUSTOMIZATION.md       # Customization guide
```

## Core Functionality

### Agreement Lifecycle
1. **Creation**: Admin selects recipients and configures agreement details
2. **Sending**: System generates unique URLs and optionally sends emails
3. **Viewing**: Recipient opens agreement link, status updates to "viewed"
4. **Signing**: Recipient provides signature, agreement marked as "signed"
5. **PDF Generation**: Signed PDF created and stored
6. **Completion**: All parties receive confirmation

### API Endpoints
- `POST /agreements/send` - Send agreements to recipients
- `GET /agreements/{id}` - Get agreement details
- `POST /agreements/{id}/view` - Mark as viewed
- `POST /agreements/{id}/sign` - Sign agreement
- `GET /agreements/{id}/pdf` - Download PDF
- `GET /agreements/status` - Get agreement statistics

### Security Features
- Unique UUID for each agreement
- Timestamp tracking for audit trail
- Optional authentication for viewing
- Signature validation
- PDF tamper protection

## Integration Steps

### 1. Adapt Database Models
Modify the agreement fields to match your business needs:
- Change fee structure fields
- Add custom fields for your agreements
- Adjust status values

### 2. Customize Agreement Template
Edit the agreement content in:
- PDF template (backend/pdf_generator.py)
- HTML display (frontend/AgreementSigningPage.tsx)

### 3. Connect to Your CRM
Replace the contact/campaign references with your system's entities:
- Update foreign key relationships
- Adjust data fetching logic
- Modify status tracking

### 4. Configure Email Service
Either use the provided email service or integrate your own:
- SMTP configuration
- Email template customization
- Delivery tracking

## Testing

### Manual Testing
1. Create test contacts
2. Send test agreements
3. Open agreement URLs
4. Sign agreements
5. Verify PDF generation

### Automated Testing
```python
# Test agreement creation
def test_create_agreement():
    agreement = create_agreement(contact_id="test", ...)
    assert agreement.id is not None
    assert agreement.status == "pending"

# Test signature
def test_sign_agreement():
    result = sign_agreement(agreement_id, signature="John Doe")
    assert result.status == "signed"
    assert result.pdf_data is not None
```

## Troubleshooting

### Common Issues
1. **Agreement Not Found**: Check if agreements table exists
2. **PDF Generation Fails**: Verify reportlab is installed
3. **Email Not Sending**: Check SMTP credentials
4. **Signature Not Saving**: Verify database permissions

### Debug Scripts
- `check_agreements_table.py` - Verify table exists
- `create_agreements_table.py` - Create table manually
- `test_agreement_flow.py` - Test complete flow

## Customization Options

### Agreement Fields
Easily add custom fields:
```python
# In models.py
class Agreement:
    # Add your custom fields
    custom_field_1: str
    custom_field_2: float
    custom_terms: dict
```

### Status Workflow
Customize the status progression:
```python
AGREEMENT_STATUSES = [
    'draft',
    'pending',
    'viewed', 
    'signed',
    'completed',
    'expired'
]
```

### PDF Template
Modify the PDF layout in `pdf_generator.py`:
- Add company logo
- Change colors and fonts
- Add custom sections
- Include terms & conditions

## License & Legal
This template provides the technical implementation of an e-signature system. 
Ensure compliance with:
- ESIGN Act (US)
- eIDAS (EU)
- Local electronic signature laws
- Industry regulations (HIPAA, SOC2, etc.)

## Support & Contributing
This is a template system. Customize it to fit your needs.
For the original implementation, see the ADTV project.

## Credits
Built with:
- FastAPI for backend API
- React for frontend UI
- ReportLab for PDF generation
- PostgreSQL for database 