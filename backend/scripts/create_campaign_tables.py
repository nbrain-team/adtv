#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database import engine, Base, Campaign, CampaignContact, CampaignTemplate, CampaignAnalytics

def create_campaign_tables():
    """Create campaign-related tables"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine, tables=[
            Campaign.__table__,
            CampaignContact.__table__,
            CampaignTemplate.__table__,
            CampaignAnalytics.__table__
        ])
        
        print("✅ Campaign tables created successfully:")
        print("   - campaigns")
        print("   - campaign_contacts")
        print("   - campaign_templates")
        print("   - campaign_analytics")
        
    except Exception as e:
        print(f"❌ Error creating campaign tables: {e}")
        raise

if __name__ == "__main__":
    create_campaign_tables() 