#!/usr/bin/env python3
"""Add default email template for testing mail merge"""

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

def add_default_template(campaign_id: str = None):
    """Add the ADTV Referral Outreach template"""
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
        
        # Check if template already exists
        existing = db.query(CampaignEmailTemplate).filter(
            CampaignEmailTemplate.campaign_id == campaign_id,
            CampaignEmailTemplate.name == "ADTV Referral Outreach"
        ).first()
        
        if existing:
            logger.info("Template already exists, updating it...")
            existing.subject = "Hey {{FirstName}}, You were referred to us"
            existing.body = """Hey {{FirstName}},

You were personally referred to me by someone in your market who said you would be a great fit for our team.

I'm [[Associate Name]], and I'm the Associate Producer for ADTV. We are the authority site for [[City]], [[State]], real estate and all the great things happening here.

I am looking for an agent to be our host for a new show we are launching. The show is designed to educate buyers and sellers on everything they need to know about real estate and all the great things happening in [[City]]. Think of it as your own show where you are the local expert!

Here's a quick video that explains it all: [[VIDEO-LINK]]

This is designed to make you the most well-known agent in [[City]], and it comes at NO COST to you.

We have event slots available:
- [[Date1]] at [[Time1]]{{#if [[Calendly Link 1]]}} - Book here: [[Calendly Link 1]]{{/if}}
{{#if [[Date2]]}}- [[Date2]] at [[Time2]]{{#if [[Calendly Link 2]]}} - Book here: [[Calendly Link 2]]{{/if}}{{/if}}
{{#if [[Date3]]}}- [[Date3]] at [[Time3]]{{#if [[Calendly Link 3]]}} - Book here: [[Calendly Link 3]]{{/if}}{{/if}}

{{#if [[Hotel Name]]}}Location: [[Hotel Name]], [[Hotel Address]]{{/if}}

I'd love to show you exactly how this works and see if you'd be interested.

Best regards,
[[Associate Name]]
[[Associate email]]
{{#if [[Associate Phone]]}}[[Associate Phone]]{{/if}}

P.S. You can also learn more and register at: [[Event-Link]]"""
            db.commit()
            logger.info("Template updated successfully")
        else:
            template = CampaignEmailTemplate(
                campaign_id=campaign_id,
                name="ADTV Referral Outreach",
                subject="Hey {{FirstName}}, You were referred to us",
                body="""Hey {{FirstName}},

You were personally referred to me by someone in your market who said you would be a great fit for our team.

I'm [[Associate Name]], and I'm the Associate Producer for ADTV. We are the authority site for [[City]], [[State]], real estate and all the great things happening here.

I am looking for an agent to be our host for a new show we are launching. The show is designed to educate buyers and sellers on everything they need to know about real estate and all the great things happening in [[City]]. Think of it as your own show where you are the local expert!

Here's a quick video that explains it all: [[VIDEO-LINK]]

This is designed to make you the most well-known agent in [[City]], and it comes at NO COST to you.

We have event slots available:
- [[Date1]] at [[Time1]]{{#if [[Calendly Link 1]]}} - Book here: [[Calendly Link 1]]{{/if}}
{{#if [[Date2]]}}- [[Date2]] at [[Time2]]{{#if [[Calendly Link 2]]}} - Book here: [[Calendly Link 2]]{{/if}}{{/if}}
{{#if [[Date3]]}}- [[Date3]] at [[Time3]]{{#if [[Calendly Link 3]]}} - Book here: [[Calendly Link 3]]{{/if}}{{/if}}

{{#if [[Hotel Name]]}}Location: [[Hotel Name]], [[Hotel Address]]{{/if}}

I'd love to show you exactly how this works and see if you'd be interested.

Best regards,
[[Associate Name]]
[[Associate email]]
{{#if [[Associate Phone]]}}[[Associate Phone]]{{/if}}

P.S. You can also learn more and register at: [[Event-Link]]""",
                template_type='invitation'
            )
            db.add(template)
            db.commit()
            logger.info(f"Template 'ADTV Referral Outreach' added successfully to campaign {campaign_id}")
        
    except Exception as e:
        logger.error(f"Error adding template: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # You can pass a campaign_id as argument or it will use the first campaign
    import sys
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else None
    add_default_template(campaign_id) 