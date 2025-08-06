#!/usr/bin/env python3
"""
Add default email template for testing mail merge
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import CampaignEmailTemplate
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_default_template(campaign_id: str):
    """Add default mail merge template to a campaign"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Local development
        DATABASE_URL = "postgresql://adtv_user:SecureP@ss2024!@localhost/adtv_db"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if template already exists
        existing = db.query(CampaignEmailTemplate).filter(
            CampaignEmailTemplate.campaign_id == campaign_id,
            CampaignEmailTemplate.name == "ADTV Referral Outreach"
        ).first()
        
        if existing:
            logger.info("Template already exists, updating it...")
            existing.subject = "Hey {{FirstName}}, You were referred to us"
            existing.body = """Hey {{FirstName}},

I'll keep short and sweet, as I know you're very busy (very real email here by the way). 
I also intend to text and call you.

I'm an Associate Producer for a 2x Emmy Nominated National TV series, about real estate and lifestyles. I've been asked to set up a personal meeting with you and our CEO, Craig Sewing (also, Inman News Nominee for Most Influential in Real Estate).

Here is a personal video from Craig explaining in more detail:
[[VIDEO-LINK]]

Reason for the outreach, we are launching a series called Selling [[State]]...
Positive stories, highlighting the different areas and neighborhoods of [[State]].

Will be airing on HGTV, and other major networks.

The show touches on real estate, but dives deep into the communities, culture, and lifestyle that make places like [[State]] and the micro markets...ie- {{Neighborhood_1}} etc in addition to plenty of other areas around there I'm not mentioning, that are great places to live. We are looking for real estate experts from all areas to share the stories.

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
[[Associate Phone]]"""
            existing.updated_at = datetime.utcnow()
            db.commit()
            logger.info("Template updated successfully")
        else:
            # Create new template
            template = CampaignEmailTemplate(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                name="ADTV Referral Outreach",
                subject="Hey {{FirstName}}, You were referred to us",
                body="""Hey {{FirstName}},

I'll keep short and sweet, as I know you're very busy (very real email here by the way). 
I also intend to text and call you.

I'm an Associate Producer for a 2x Emmy Nominated National TV series, about real estate and lifestyles. I've been asked to set up a personal meeting with you and our CEO, Craig Sewing (also, Inman News Nominee for Most Influential in Real Estate).

Here is a personal video from Craig explaining in more detail:
[[VIDEO-LINK]]

Reason for the outreach, we are launching a series called Selling [[State]]...
Positive stories, highlighting the different areas and neighborhoods of [[State]].

Will be airing on HGTV, and other major networks.

The show touches on real estate, but dives deep into the communities, culture, and lifestyle that make places like [[State]] and the micro markets...ie- {{Neighborhood_1}} etc in addition to plenty of other areas around there I'm not mentioning, that are great places to live. We are looking for real estate experts from all areas to share the stories.

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
                template_type='invitation',
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(template)
            db.commit()
            logger.info("Template created successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error adding template: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python add_default_email_template.py <campaign_id>")
        sys.exit(1)
    
    campaign_id = sys.argv[1]
    if add_default_template(campaign_id):
        logger.info("Default template added successfully")
    else:
        logger.error("Failed to add default template") 