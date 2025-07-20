from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from .database import get_db, User
from . import auth

router = APIRouter()

# Pydantic models
class EmailTemplateCreate(BaseModel):
    name: str
    content: str
    goal: str

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    goal: Optional[str] = None

class EmailTemplateResponse(BaseModel):
    id: str
    name: str
    content: str
    goal: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_system: bool

# In-memory storage for now (you can migrate to database later)
email_templates_storage = {}

# System templates (pre-populated)
SYSTEM_TEMPLATES = {
    "roadshow1": {
        "id": "sys-roadshow1",
        "name": "Roadshow 1 - Marketing Campaign Ramp Up",
        "content": """Hi {{MM}},

{{City}} is in [[DaysUntilEvent]] days, and we are ramping up to begin our marketing campaign! As soon as you secure a friendly (Existing cast member/Realtor, Mortgage) please add them to the bottom of the {{City}} tab and highlight them in yellow. I will include them in the confirmation email and texts.

Thank you,
[[YourName]]""",
        "goal": "Simple internal communication for marketing campaign coordination.",
        "is_system": True
    },
    "roadshow2": {
        "id": "sys-roadshow2",
        "name": "Roadshow 2 - Initial Outreach (Long)",
        "content": """Hey {{FirstName}},
I've been asked to reach out to you, on behalf of my CEO and Executive Show Producer Craig Sewing.  
I'll keep this email short and sweet, as I know you're busy (just in case, please know this is a very real email here).
Craig did create a personal video message for you below that elaborates a bit:
[[VideoLink]]

After watching that, let me get you few more details…
You might know Craig, as he speaks at National real estate events, and was an Inman News Nominee for Most Influential in Real Estate, etc, etc. 
We've have a team that does some market research and outreach (me:), and you were referred to us as being reputable in real estate we should invite to learn about this.

My hope here is to set you up with an exploratory conversation about a new show coming into {{State}}, airing on HGTV and other major networks. 
A REAL show (not some reality TV drama thing), specifically about real estate and lifestyles, showing us the neighborhoods you sell real estate.

I do intend to call and text you as well, but figured an email makes it easier to explain, and get a reply on what you think. 
Specifically, Craig is flying into [[DestinationCity]] next week and I am responsible for coordinating some private meetings.   
He could do this with you on zoom, but he wants to meet with you if you're up for it.   
You were referred to us as someone that we should try to connect with (fyi, I have a short list of others I am reaching out to as well).

As for me, I am the associate producer for the New TV Show that will be featured on HGTV and the Travel Channel called, "Selling {{State}}"
A real show, not some reality TV thing, and honestly its a media model developed by some of the leaders in the real estate industry.  A really cool show, and concept.

It will air on TV, and showcase the cool real estate, neighborhoods, and lifestyles of {{State}} and the surrounding markets, through the lens of real estate professionals.
We've done previous shows and models in {{State}}, but NOT this.  
This is brand new to your market, and a really cool show concept we'd love to explore with you. 

We just aligned with HGTV and are looking for experts in the different micro markets of {{State}} and ALL the surrounding areas ([[ExampleCities]] to name a few NOT limited to these markets)

The show is a 2x EMMY Nominated 12x Telly Award Winning production, that garners millions of views.  
Again, A REAL show, with REAL professionals (not some drama filled reality TV.)
 
We are opening conversations with potential real estate professionals to be featured as "THE VOICE" for why people love where you live.  Pretty fun show and concept! And if it matters, the agents who get chosen tend to get a lot of referrals. 
To add some color, here is a RECENT PROMO of the show featuring real estate industry leaders, and another PROMO that features some of our real estate experts in other cities.  
Some of your industry leaders who've been on the show:  Tom Ferry, Mike Ferry, Robert Reffkin, Grant & Elena Cardone, Shannon Gillette, Ryan Serhant, to name a few…

For further validation if needed, here is the Facebook and Instagram page for the 2xEMMY nominated media network that will be producing the show.  
Click here for Instagram
Click here for Facebook

As I mentioned, our CEO Craig Sewing is holding meetings for some reputable agents, and would like to have a conversation with you.
No strings attached.
Just a casual meeting, and conversation to explain, answer all of your questions, and see if its a good fit.  If not, no worries.""",
        "goal": "Comprehensive initial outreach explaining the show opportunity, establishing credibility, and requesting a meeting. AI should adapt regional references, timing mentions, and industry context based on recipient's location and background.",
        "is_system": True
    },
    "roadshow3": {
        "id": "sys-roadshow3",
        "name": "Roadshow 3 - SMS/Short Follow-up",
        "content": """Hi {{FirstName}}, this is [[YourName]] from ADTV. I sent you an email about featuring top {{City}} agents on our HGTV show. Craig, our CEO, is in town next week and would love to meet. Quick coffee to discuss? The show highlights why people love living in your area - perfect for someone with your local expertise.""",
        "goal": "Brief SMS or short email follow-up. AI should adapt the local area reference and timing based on recipient's actual location.",
        "is_system": True
    },
    "roadshow4": {
        "id": "sys-roadshow4",
        "name": "Roadshow 4 - Meeting Scheduling",
        "content": """Hi {{FirstName}},

Great connecting with you! As discussed, Craig Sewing, our CEO and Executive Producer, would love to meet with you while he's in {{City}} next week.

He has availability on:
[[MeetingOptions]]

The meeting will be about 30-45 minutes, very casual - just a conversation about the show and how we showcase real estate professionals and the communities they serve. We can meet at your office, a local coffee shop, or wherever is convenient for you.

Craig is excited to learn about your market and share how "Selling {{State}}" will highlight the unique aspects of your area.

Which time works best for you? Also, let me know your preferred meeting location.

Looking forward to connecting!

Best,
[[YourName]]""",
        "goal": "Schedule a meeting with specific options. AI should personalize based on local area knowledge, appropriate meeting venues for their location, and professional context.",
        "is_system": True
    },
    "roadshow5": {
        "id": "sys-roadshow5",
        "name": "Roadshow 5 - Pre-Meeting Confirmation",
        "content": """Hi {{FirstName}},

Just confirming our meeting tomorrow at [[MeetingTime]] at [[MeetingLocation]].

Craig is looking forward to discussing how "Selling {{State}}" can showcase what makes {{City}} special through the eyes of local real estate experts like yourself.

A few things Craig will cover:
• How the show works and what filming involves
• The exposure and benefits for featured agents
• Your unique perspective on the {{City}} market
• Timeline and next steps if there's mutual interest

The meeting is very relaxed - just a conversation between real estate professionals. No preparation needed, just bring yourself!

See you tomorrow! If anything changes, please let me know.

Best,
[[YourName]]
[[YourPhone]]""",
        "goal": "Confirm meeting details and set expectations. AI should adapt local market references and any regional-specific considerations.",
        "is_system": True
    },
    "personalized_intro": {
        "id": "sys-personalized-intro",
        "name": "Personalized Introduction",
        "content": """Hi {{FirstName}},

I noticed you're based in {{City}} - such a beautiful area this time of year! I'm reaching out because we're looking for top real estate professionals who really understand their local market.

Your work at {{Company}} caught our attention, particularly your expertise in the {{City}} area. We're launching an exciting project that showcases the best of local real estate, and I'd love to share more details with you.

Would you be open to a brief conversation next week? I promise it'll be worth your time, especially given your position in the market.

Best regards,
[[YourName]]""",
        "goal": "Initial outreach that feels highly personalized. AI should heavily adapt based on location (weather, local events, market conditions), company type, and role to make it feel like it was written specifically for them.",
        "is_system": True
    }
}

@router.get("/", response_model=List[EmailTemplateResponse])
async def get_email_templates(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all email templates (system + user-created)"""
    from .database import EmailTemplate
    
    # Get all templates from database
    db_templates = db.query(EmailTemplate).filter(
        EmailTemplate.is_active == True
    ).all()
    
    templates = []
    
    # Add database templates
    for template in db_templates:
        templates.append(EmailTemplateResponse(
            id=template.id,
            name=template.name,
            content=template.body,  # Note: database uses 'body' field
            goal=template.subject,  # Using subject as goal for now
            created_at=template.created_at,
            updated_at=template.updated_at,
            created_by=template.created_by or "system",
            is_system=template.is_system
        ))
    
    return templates

@router.post("/", response_model=EmailTemplateResponse)
async def create_email_template(
    template_data: EmailTemplateCreate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new email template"""
    from .database import EmailTemplate
    
    # Create in database
    db_template = EmailTemplate(
        name=template_data.name,
        subject=template_data.goal,  # Using goal as subject
        body=template_data.content,
        category="User Created",
        is_active=True,
        is_system=False,
        created_by=current_user.id
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # Return response
    return EmailTemplateResponse(
        id=db_template.id,
        name=db_template.name,
        content=db_template.body,
        goal=db_template.subject,
        created_at=db_template.created_at,
        updated_at=db_template.updated_at,
        created_by=db_template.created_by,
        is_system=db_template.is_system
    )

@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: str,
    template_data: EmailTemplateUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an email template"""
    from .database import EmailTemplate
    
    # Get template from database
    db_template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check ownership (only allow editing non-system templates by creator)
    if not db_template.is_system and db_template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this template")
    
    # Don't allow editing system templates
    if db_template.is_system:
        raise HTTPException(status_code=403, detail="Cannot edit system templates")
    
    # Update fields
    if template_data.name is not None:
        db_template.name = template_data.name
    if template_data.content is not None:
        db_template.body = template_data.content
    if template_data.goal is not None:
        db_template.subject = template_data.goal
    
    db_template.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_template)
    
    return EmailTemplateResponse(
        id=db_template.id,
        name=db_template.name,
        content=db_template.body,
        goal=db_template.subject,
        created_at=db_template.created_at,
        updated_at=db_template.updated_at,
        created_by=db_template.created_by,
        is_system=db_template.is_system
    )

@router.delete("/{template_id}")
async def delete_email_template(
    template_id: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an email template"""
    from .database import EmailTemplate
    
    # Get template from database
    db_template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check ownership (only allow deleting non-system templates by creator)
    if not db_template.is_system and db_template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this template")
    
    # Don't allow deleting system templates
    if db_template.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system templates")
    
    # Soft delete by setting is_active to False
    db_template.is_active = False
    db.commit()
    
    return {"message": "Template deleted successfully"} 