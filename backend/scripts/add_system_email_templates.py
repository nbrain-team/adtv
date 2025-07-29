#!/usr/bin/env python3
"""
Add system email templates to the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import DATABASE_URL, EmailTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System templates
SYSTEM_TEMPLATES = [
    {
        "name": "Roadshow 1 - Marketing Campaign Ramp Up",
        "subject": "Marketing Campaign Coordination",
        "body": """Hi {{MM}},

{{City}} is in [[DaysUntilEvent]] days, and we are ramping up to begin our marketing campaign! As soon as you secure a friendly (Existing cast member/Realtor, Mortgage) please add them to the bottom of the {{City}} tab and highlight them in yellow. I will include them in the confirmation email and texts.

Thank you,
[[YourName]]""",
        "category": "Event",
        "is_system": True
    },
    {
        "name": "Roadshow 2 - Initial Outreach (Long)",
        "subject": "Exclusive Invitation - HGTV Show Opportunity",
        "body": """Hey {{FirstName}},
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
Just a casual meeting, and conversation to explain, answer all of your questions, and see if its a good fit.  If not, no worries.

Let me know, and I'll get it set up.
Thanks for your time, and I look forward to hearing from you.

[[YourName]]""",
        "category": "Event",
        "is_system": True
    },
    {
        "name": "Roadshow 3 - Short Follow-up",
        "subject": "Quick Follow-up - HGTV Opportunity",
        "body": """Hey {{FirstName}},

I wanted to follow up on my previous email about the HGTV show opportunity in {{State}}.

Our CEO Craig Sewing will be in [[DestinationCity]] next week for private meetings with select real estate professionals. Given your reputation in the {{City}} market, we'd love to include you.

The meeting is casual - just a conversation about the show concept and how it could benefit your business. No obligations.

Interested in grabbing coffee? I have a few time slots available:
[[TimeSlots]]

Let me know what works for you!

Best,
[[YourName]]""",
        "category": "Event",
        "is_system": True
    },
    {
        "name": "Personalized Introduction",
        "subject": "Connecting about {{City}} Real Estate",
        "body": """Hi {{FirstName}},

I noticed you're based in {{City}} - such a beautiful area this time of year! I'm reaching out because we're looking for top real estate professionals who really understand their local market.

Your work at {{Company}} caught our attention, particularly your expertise in the {{City}} area. We're launching an exciting project that showcases the best of local real estate, and I'd love to share more details with you.

Would you be open to a brief conversation next week? I promise it'll be worth your time, especially given your position in the market.

Best regards,
[[YourName]]""",
        "category": "Event",
        "is_system": True
    }
]

def add_system_templates():
    """Add system templates to the database"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        added_count = 0
        updated_count = 0
        
        for template_data in SYSTEM_TEMPLATES:
            # Check if template already exists
            existing = db.query(EmailTemplate).filter(
                EmailTemplate.name == template_data["name"]
            ).first()
            
            if existing:
                # Update existing template
                existing.subject = template_data["subject"]
                existing.body = template_data["body"]
                existing.category = template_data["category"]
                existing.is_system = template_data["is_system"]
                updated_count += 1
                logger.info(f"Updated template: {template_data['name']}")
            else:
                # Create new template
                template = EmailTemplate(
                    name=template_data["name"],
                    subject=template_data["subject"],
                    body=template_data["body"],
                    category=template_data["category"],
                    is_system=template_data["is_system"],
                    is_active=True
                )
                db.add(template)
                added_count += 1
                logger.info(f"Added template: {template_data['name']}")
        
        db.commit()
        logger.info(f"Successfully added {added_count} templates and updated {updated_count} templates")
        
    except Exception as e:
        logger.error(f"Error adding templates: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_system_templates()
    print("✅ System email templates added successfully!") 