#!/usr/bin/env python3
"""Add all email templates for campaigns"""

import sys
import os
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import CampaignEmailTemplate, SessionLocal, Campaign

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_templates(campaign_id: str = None):
    """Add all email templates"""
    db = SessionLocal()
    
    try:
        # If no campaign_id provided, find the first campaign
        if not campaign_id:
            campaign = db.query(Campaign).first()
            if campaign:
                campaign_id = campaign.id
                logger.info(f"Using campaign {campaign.name} (ID: {campaign_id})")
            else:
                logger.error("No campaigns found in database")
                return
        
        # Define all templates
        templates = [
            {
                "name": "Email - In Person Outbound #1",
                "subject": "Hey {{FirstName}}, You were referred to us",
                "body": """Hey {{FirstName}},

I'll keep short and sweet, as I know you're very busy (very real email here by the way). 
I also intend to text and call you.

I'm an Associate Producer for a 2x Emmy Nominated National TV series, about real estate and lifestyles. I've been asked to set up a personal meeting with you and our CEO, Craig Sewing (also, Inman News Nominee for Most Influential in Real Estate).  

Here is a personal video from Craig explaining in more detail:
[[VIDEO-LINK]]
{{IMAGE1.gif))

Reason for the outreach, we are launching a series called Selling [[State]]…
Positive stories, highlighting the different areas and neighborhoods of [[State]].

Will be airing on HGTV, and other major networks.  

The show touches on real estate, but dives deep into the communities, culture, and lifestyle that make places like Illinois and the micro markets…ie- {{Neighborhood_1}} etc in addition to plenty of other areas around there I'm not mentioning, that are great places to live. We are looking for real estate experts from all areas to share the stories.
Through a little bit of research, you were referred to us as someone he should connect with about possibly being on the show as a community expert. My intention is to connect you for an exploratory conversation in person next week.

If you'd like to warm up to the show/media model: [[Event-Link]], provides some preliminary info, Craig will talk through with you. I'm sure you have questions, Craig has set aside these days/times next week to connect with you and a handful of others I'm reaching out to.  
He'd love to meet with you. Just an exploratory conversation, to share the show and concept.

Quick note, the agents we align into the show tend to get listing referrals from consumers.
Craig can explain how that all works in conversation with you.

The meeting times available are listed below. If you are interested and would like to attend, please email me back with which day works best and I will add you to the RSVP list.
Dates/Times:
[[Date1]] [[Time1]]
[[Date2]] [[Time2]]

Location: 
[[Hotel Name]]
[[Hotel Address]]


Thanks!
[[Associate Name]]
Associate Director
[[Associate email]]
[[Associate Phone]]""",
                "template_type": "invitation"
            },
            {
                "name": "EMAIL - CZ Outbound #1",
                "subject": "Hey {{FirstName}}, You were referred to us",
                "body": """Hey {{FirstName}},

I'll keep short and sweet, as I know you're very busy (very real email here by the way). 
I also intend to text and call you.

I'm an Associate Producer for a 2x Emmy Nominated National TV series, about real estate and lifestyles. I've been asked to set up a personal meeting with you and our CEO, Craig Sewing (also, Inman News Nominee for Most Influential in Real Estate).  

Here is a personal video from Craig explaining in more detail:
[[VIDEO-LINK]]
{{IMAGE1.gif))


Reason for the outreach, we are launching a series called Selling [[State]]…
Positive stories, highlighting the different areas and neighborhoods of [[State]].

Will be airing on HGTV, and other major networks.  

The show touches on real estate, but dives deep into the communities, culture, and lifestyle that make places like Illinois and the micro markets…ie- {{Neighborhood_1}} etc in addition to plenty of other areas around there I'm not mentioning, that are great places to live. We are looking for real estate experts from all areas to share the stories.

Through a little bit of research, you were referred to us as someone he should connect with about possibly being on the show as a community expert. My intention is to connect you for an exploratory conversation on zoom next week.

If you'd like to warm up to the show/media model: [[Event-Link]], provides some preliminary info, Craig will talk through with you. I'm sure you have questions, Craig has set aside these days/times next week to connect with you and a handful of others I'm reaching out to.  
He'd love to meet with you. Just an exploratory conversation, to share the show and concept.

Quick note, the agents we align into the show tend to get listing referrals from consumers.
Craig can explain how that all works in conversation with you.

The zoom meeting information is below. If you are interested and would like to attend, you can self-register or respond to this email with which date works best for you and I will add you to the RSVP list and send a confirmation email.


Dates/Times:
[[Date1]] [[Time1]] [[Calendly Link 1]]
[[Date2]] [[Time2]] [[Calendly Link 2]]
[[Date3]] [[Time3]] [[Calendly Link 3]]


Thanks!

[[Associate Name]]
Associate Producer
[[Associate email]]
[[Associate Phone]]""",
                "template_type": "invitation"
            },
            {
                "name": "SMS - Text #1 - Monday before roadshow",
                "subject": "Important invitation for {{FirstName}}",
                "body": """Hello {{FirstName}}, I wanted to make sure I had the correct email address for you because I'm about to send you an important invitation to have a conversation with our Executive Producer next week. Please let me know if you didn't get the note or text me back if there's a better email address than the one I sent it to {{Email}} Thanks, [[Associate Name]].""",
                "template_type": "sms"
            },
            {
                "name": "Email #2 In Person",
                "subject": "Following up on my previous email, {{FirstName}}",
                "body": """Hi {{FirstName}},

I just wanted to check in as I sent you an email earlier this week and wanted to make sure you received it.

I'm a producer for The American Dream, an EMMY nominated and TELLY award winning national TV show centered around real estate and lifestyle. We are in the process of launching our shows Selling [[State]] and would like to meet with you to discuss potentially being considered as a market expert to host in your city and surrounding markets. The email I sent outlines all the details, so I'll keep this note short in case you did see it and maybe wrote it off as spam. Let me know if you didn't receive it and I am happy to send it again if needed.

Our CEO Craig Sewing will be flying into town next week to meet with agents we feel would be a good fit and would like to meet with you if available. He created a personalized message explaining further so you can see the sincerity of this correspondence.

Watch Craig's Video Message [[VIDEO-LINK]]

The meeting times available are listed below. If you are interested and would like to attend, please email me back with which day works best and I will add you to the RSVP list.

Dates/Times:
[[Date1]] [[Time1]]
[[Date2]] [[Time2]]

Location: 
[[Hotel Name]]
[[Hotel Address]]


Please respond to this email, and let me know if you're able to attend so I can add you to the RSVP list. If it's not for you, no worries - just let me know so I can reach out to others more interested. 

Thank you so much, and have a wonderful rest of your day!

[[Associate Name]]
Associate Producer
[[Associate email]]
[[Associate Phone]]""",
                "template_type": "follow_up"
            }
        ]
        
        # Add each template
        templates_added = 0
        templates_updated = 0
        
        for template_data in templates:
            # Check if template already exists
            existing = db.query(CampaignEmailTemplate).filter(
                CampaignEmailTemplate.campaign_id == campaign_id,
                CampaignEmailTemplate.name == template_data["name"]
            ).first()
            
            if existing:
                # Update existing template
                existing.subject = template_data["subject"]
                existing.body = template_data["body"]
                existing.template_type = template_data["template_type"]
                templates_updated += 1
                logger.info(f"Updated template: {template_data['name']}")
            else:
                # Create new template
                template = CampaignEmailTemplate(
                    campaign_id=campaign_id,
                    name=template_data["name"],
                    subject=template_data["subject"],
                    body=template_data["body"],
                    template_type=template_data["template_type"]
                )
                db.add(template)
                templates_added += 1
                logger.info(f"Added new template: {template_data['name']}")
        
        db.commit()
        logger.info(f"Successfully processed {len(templates)} templates:")
        logger.info(f"  - {templates_added} new templates added")
        logger.info(f"  - {templates_updated} existing templates updated")
        
    except Exception as e:
        logger.error(f"Error adding templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # You can pass a campaign_id as argument or it will use the first campaign
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else None
    add_templates(campaign_id) 