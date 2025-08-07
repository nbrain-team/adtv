# Cursor AI Prompt: Implement E-Signature Agreement System

## System Overview
I need you to implement a complete e-signature agreement system similar to DocuSign. This system will allow administrators to send digital agreements to recipients, who can then view and electronically sign them. The system should generate PDFs with embedded signatures and maintain a complete audit trail.

## Core Requirements

### 1. Database Schema
Create the following database structure:

```sql
-- Main agreements table
agreements:
  - id (UUID/String, Primary Key)
  - recipient_id (Foreign Key to your users/contacts table)
  - recipient_name (String)
  - recipient_email (String)
  - company (String, Optional)
  - agreement_date (Date)
  - amount (Float) // Or your specific fields
  - terms (Text) // Agreement terms
  - status (String: 'pending', 'viewed', 'signed', 'expired')
  - signature (Text) // Store the signature
  - signature_type (String: 'typed', 'drawn')
  - signed_date (String)
  - signed_at (Timestamp)
  - viewed_at (Timestamp)
  - created_at (Timestamp)
  - updated_at (Timestamp)
  - pdf_data (Text/Blob) // Store generated PDF as base64
  - agreement_url (String) // The unique URL

-- Add tracking fields to your existing contacts/users table:
  - agreement_status (String)
  - agreement_sent_at (Timestamp)
  - agreement_signed_at (Timestamp)
  - agreement_data (JSON/Text) // Store agreement metadata
```

### 2. Backend API Implementation

#### 2.1 Agreement Model
Create a database model for agreements with all necessary fields. Use SQLAlchemy or your preferred ORM.

#### 2.2 API Endpoints
Implement these REST endpoints:

**Send Agreements**
```python
POST /api/agreements/send
Body: {
  recipient_ids: string[],
  agreement_data: {
    date: string,
    amount: number,
    terms: string,
    // Your custom fields
  }
}
```

**Get Agreement**
```python
GET /api/agreements/{agreement_id}
Response: Agreement details for signing page
```

**Mark as Viewed**
```python
POST /api/agreements/{agreement_id}/view
Updates status to 'viewed' with timestamp
```

**Sign Agreement**
```python
POST /api/agreements/{agreement_id}/sign
Body: {
  signature: string,
  signature_type: 'typed' | 'drawn',
  signed_date: string
}
```

**Get PDF**
```python
GET /api/agreements/{agreement_id}/pdf
Returns: PDF file (application/pdf)
```

#### 2.3 Processing Logic
```python
def process_agreements(recipient_ids, agreement_data):
    for recipient_id in recipient_ids:
        # 1. Create agreement record
        agreement = Agreement(
            id=generate_uuid(),
            recipient_id=recipient_id,
            ...agreement_data,
            status='pending'
        )
        
        # 2. Save to database IMMEDIATELY
        db.add(agreement)
        db.commit()  # Important: Commit each agreement individually
        
        # 3. Generate URL
        agreement_url = f"{BASE_URL}/agreement/{agreement.id}"
        
        # 4. Optional: Send email
        if email_configured:
            send_agreement_email(recipient.email, agreement_url)
        
        # 5. Update recipient tracking fields
        recipient.agreement_status = 'sent'
        recipient.agreement_sent_at = now()
        db.commit()
```

### 3. Frontend Implementation

#### 3.1 Agreement Sending Modal
Create a modal component for sending agreements:

```tsx
// Key features:
- Select recipients (checkbox list or multi-select)
- Configure agreement details (date, amount, terms)
- Preview the agreement
- Send button with loading state
- Success/error handling
```

#### 3.2 Agreement Signing Page
Create a standalone page for signing (no authentication required):

```tsx
// Route: /agreement/:agreementId
// Features:
- Fetch agreement details on load
- Display agreement content nicely formatted
- Show recipient info
- Terms & conditions section (scrollable)
- Signature input (text field styled as cursive)
- "I agree" checkbox
- Sign button
- Auto-download PDF after signing
- Success confirmation screen
```

#### 3.3 Status Display Component
Create a component to show agreement status in tables:

```tsx
// Clickable badge that shows:
- 📧 Sent (orange)
- 👁 Viewed (blue)  
- ✓ Signed (green)
- ❌ Failed (red)
// Clicking opens agreement in new tab
```

### 4. PDF Generation

Implement PDF generation using ReportLab (Python) or similar:

```python
def generate_agreement_pdf(agreement):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    
    # Add title
    elements.append(Paragraph("SERVICE AGREEMENT", title_style))
    
    # Add agreement details
    elements.append(Paragraph(f"Date: {agreement.date}"))
    elements.append(Paragraph(f"Recipient: {agreement.recipient_name}"))
    
    # Add terms
    elements.append(Paragraph(agreement.terms))
    
    # If signed, add signature section
    if agreement.status == 'signed':
        elements.append(Paragraph("ELECTRONIC SIGNATURE"))
        elements.append(Paragraph(f"Signed by: {agreement.signature}"))
        elements.append(Paragraph(f"Date: {agreement.signed_date}"))
    
    doc.build(elements)
    return buffer.getvalue()
```

### 5. Email Service (Optional)

If you want email notifications:

```python
class EmailService:
    def send_agreement_email(self, to_email, agreement_url):
        subject = "Your Agreement is Ready to Sign"
        html_body = f"""
        <h1>Agreement Ready</h1>
        <p>Please review and sign your agreement:</p>
        <a href="{agreement_url}">Sign Agreement</a>
        """
        # Use your email service (SMTP, SendGrid, etc.)
        send_email(to_email, subject, html_body)
```

### 6. Security Considerations

1. **Unique IDs**: Use UUIDs for agreement IDs
2. **No Authentication for Signing**: Agreement URLs should work without login
3. **Audit Trail**: Track all actions with timestamps
4. **PDF Storage**: Store signed PDFs for legal record
5. **URL Expiration**: Optional - expire URLs after X days

### 7. UI/UX Requirements

#### Signing Page Layout:
```
┌─────────────────────────────────────┐
│         SERVICE AGREEMENT           │
│         [Company Name]               │
├─────────────────────────────────────┤
│ Agreement Between:                   │
│ • Service Provider: [Your Company]  │
│ • Client: [Recipient Name]          │
│ • Email: [Recipient Email]          │
├─────────────────────────────────────┤
│ Terms & Conditions:                 │
│ [Scrollable terms text]             │
│                                     │
├─────────────────────────────────────┤
│ Electronic Signature:               │
│ ┌─────────────────────────────┐    │
│ │ Type your full name         │    │
│ └─────────────────────────────┘    │
│ ☐ I agree to the terms             │
│                                     │
│ [Sign Agreement] [Print]           │
└─────────────────────────────────────┘
```

### 8. Testing Requirements

Test these scenarios:
1. Send agreement to single recipient
2. Send agreements to multiple recipients  
3. Open agreement URL (should work without login)
4. View agreement (status updates)
5. Sign agreement
6. PDF downloads after signing
7. Agreement not found (invalid ID)
8. Already signed agreement

### 9. Error Handling

Handle these cases:
- Database connection errors
- Email sending failures (don't block agreement creation)
- Invalid agreement IDs
- Missing required fields
- PDF generation errors

### 10. Implementation Steps

1. **Phase 1**: Database setup
   - Create agreements table
   - Add tracking fields to contacts

2. **Phase 2**: Backend API
   - Create models
   - Implement endpoints
   - Add PDF generation

3. **Phase 3**: Frontend components
   - Sending modal
   - Signing page
   - Status display

4. **Phase 4**: Integration
   - Connect to your existing system
   - Test end-to-end flow

5. **Phase 5**: Polish
   - Error handling
   - Loading states
   - Success messages

## Example Code References

Look at these files in the template for complete implementations:
- `backend/agreements.py` - Full API implementation
- `frontend/AgreementSigningPage.tsx` - Complete signing page
- `frontend/RSVPAgreementModal.tsx` - Sending modal
- `backend/pdf_generator.py` - PDF generation logic

## Success Criteria

The system is complete when:
✅ Admins can send agreements to multiple recipients
✅ Each agreement has a unique URL
✅ Recipients can view agreements without login
✅ Recipients can sign electronically
✅ PDFs are generated with signatures
✅ Status tracking works (sent → viewed → signed)
✅ All timestamps are recorded
✅ Agreement URLs work in production

## Notes for Implementation

- Start with the backend API first
- Test with hardcoded agreement data initially
- Add email sending last (it's optional)
- Use the same UI framework you're already using
- Adapt the field names to match your business model
- Consider adding expiration dates for agreements
- Add your company branding to PDFs and emails

This system provides a complete, professional e-signature solution that can replace DocuSign for basic agreement signing needs. 