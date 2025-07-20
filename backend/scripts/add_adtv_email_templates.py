#!/usr/bin/env python3
"""Add ADTV email templates to the database"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, EmailTemplate

def add_adtv_templates():
    """Add ADTV email templates"""
    db = SessionLocal()
    
    templates = [
        {
            "name": "ADTV Round 1 Email",
            "subject": "Exclusive Opportunity: Feature in Selling {{City}} on HGTV",
            "body": """Hey {{FirstName}},

I'll keep this short and sweet, since I know your time is valuable — and yes, this is a real email, not a blast.

I'm also planning to text and call you directly, but I wanted to start here.

I'm an Associate Producer for a 2x Emmy-nominated national television series focused on real estate, lifestyle, and local communities. I've been asked to reach out to you personally to explore the opportunity to connect with our CEO, Craig Sewing — Inman News Nominee for Most Influential in Real Estate and the creative force behind the show.

Here's a short video from Craig that explains the concept in his own words:
[[VideoLink]]

We're currently casting for our upcoming series, Selling {{City}} — airing on HGTV and other major networks. The show highlights the communities, culture, and lifestyle that make {{City}} a world-class place to live, with a special focus on hyperlocal markets like [[Markets]].

As someone who's clearly a respected presence in {{Market}} real estate — with a strong digital footprint and community involvement — your name came up as someone Craig should speak with directly about potentially being featured in our next episode.

This isn't a pitch — it's an exploratory conversation. The goal is to introduce you to the show's format, how agents are featured as trusted community experts, and how that naturally results in increased exposure, inbound referrals, and storytelling that goes beyond the transaction.

If you'd like a sneak peek before we talk:
Here's a preliminary info page Craig will walk through with you during the meeting: [[InfoLink]]

Meeting Details (Virtual or In-Person in {{City}}):

Date / Time:
- [[Date1]]
- [[Date2]]

Location:
[[HotelName]]
[[HotelAddress]]

If this sounds exciting, just reply to this email with your preferred day, and I'll confirm your RSVP. Again, it's purely a discovery conversation to see if there's a fit — no obligations, just an opportunity.

And if it's not for you, just let me know — no pressure at all.

Wishing you continued success with your work in {{Market}}, and I hope to connect soon.

Warm regards,
[[AssociateName]]
Associate Producer
American Dream TV""",
            "category": "ADTV Outreach",
            "is_active": True
        },
        {
            "name": "ADTV Round 2 Email",
            "subject": "Quick Follow-up: Selling {{City}} Feature Opportunity",
            "body": """Hi {{FirstName}},

Hope you had a great weekend! Just following up on my email from a couple days ago — wanted to quickly circle back in case you missed it.

I'm an Associate Producer with the ADTV Network, home to 2x Emmy-nominated national television series about real estate and lifestyle. We're gearing up to film our new season right here in {{City}}, and we're opening up one-on-one conversations with standout local agents to be potentially featured as the voice of their community.

We've been especially focused on {{Market}}, and your presence caught our attention — we'd love to explore featuring you as a hyperlocal expert in this iconic coastal market.

Here's a short video to warm you up to what we're building with Selling {{City}}:
[[VideoLink]]

If you're interested in chatting with Craig Sewing (our CEO and host of the show), just reply to this email with a preferred time and I'll lock you in.

Availability:
- [[Date1]]
- [[Date2]]

Location:
[[HotelName]]
[[HotelAddress]]

Let me know if one of those times works for you — would love to connect you and Craig.

Warm regards,
[[AssociateName]]
Associate Producer, ADTV Network
[[ContactInfo]]""",
            "category": "ADTV Outreach",
            "is_active": True
        },
        {
            "name": "ADTV SMS Template",
            "subject": "SMS: ADTV Feature Opportunity",
            "body": """Hi {{FirstName}}, [[AssociateName]] here with ADTV Network. I sent you an email a couple days ago about the launch of our new Selling {{City}} season. We're opening up convos with top local agents to be featured as "The Voice" for areas like {{Market}}. Craig will be in {{City}} holding meetings at the [[HotelName]] on [[Date1]] or [[Date2]]. If either works, let me know and I'll get you scheduled! Didn't see the email? Just reply with the best address and I'll resend it.""",
            "category": "ADTV Outreach",
            "is_active": True
        },
        {
            "name": "ADTV Voicemail Script",
            "subject": "Voicemail: ADTV Feature Opportunity",
            "body": """Hi {{FirstName}}, this is [[AssociateName]] with ADTV Network. I sent you an email and just wanted to make sure you received it. We're launching our show here in {{City}}, highlighting real estate, lifestyle, and the incredible communities like {{Market}}, and we'd love for you to be part of it. We're coming to town next week and would really like to meet with you. All the details are in the email — please check your spam folder if you didn't see it. And if you'd like me to resend it, just text your best email address to [[AssociatePhone]] and I'll get that over to you. Thanks so much, and enjoy your day!""",
            "category": "ADTV Outreach",
            "is_active": True
        }
    ]
    
    try:
        for template_data in templates:
            # Check if template already exists
            existing = db.query(EmailTemplate).filter_by(name=template_data["name"]).first()
            if existing:
                print(f"Template '{template_data['name']}' already exists, updating...")
                for key, value in template_data.items():
                    setattr(existing, key, value)
            else:
                print(f"Creating template '{template_data['name']}'...")
                template = EmailTemplate(**template_data)
                db.add(template)
        
        db.commit()
        print("\n✅ Successfully added/updated all ADTV templates!")
        
        # List all templates
        print("\nAvailable placeholders:")
        print("From CRM (use {{}}): FirstName, Market, City")
        print("Campaign-specific (use [[]]): VideoLink, InfoLink, Date1, Date2, HotelName, HotelAddress, Markets, AssociateName, ContactInfo, AssociatePhone")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_adtv_templates() 