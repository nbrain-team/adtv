#!/usr/bin/env python3
"""
Script to re-enable owner_phone after migration has run
Run this after the database has been updated
"""

print("""
TO RE-ENABLE owner_phone AFTER MIGRATION:

1. In backend/core/database.py:
   - Uncomment line: owner_phone = Column(String, nullable=True)

2. In backend/core/campaign_routes.py:
   - In CampaignResponse, uncomment: owner_phone: Optional[str]
   - In create_campaign, change:
     **campaign_data.dict(exclude={'owner_phone'})
     to:
     **campaign_data.dict()
   - In update_campaign, remove exclude={'owner_phone'}
   - In email generation, change phone numbers back to:
     '[[Campaign Owner Phone]]': getattr(campaign, 'owner_phone', '') or '',
     '[[AssociatePhone]]': getattr(campaign, 'owner_phone', '(619) 374-7405') or '(619) 374-7405'

3. In frontend/src/pages/CampaignsPage.tsx:
   - Uncomment: owner_phone: selectedOwner.phone,

4. In frontend/src/pages/CampaignDetailPage.tsx:
   - Make sure owner_phone?: string; is in Campaign interface

Then commit and push the changes.
""") 