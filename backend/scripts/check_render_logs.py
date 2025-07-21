#!/usr/bin/env python3
"""Instructions for checking Render logs for scraper activity"""

print("""
=== HOW TO CHECK RENDER LOGS FOR SCRAPER ACTIVITY ===

1. Go to your Render Dashboard
2. Click on your backend service (adtv-backend)
3. Click on "Logs" tab
4. Look for recent entries like:

   - "Found X agent profiles" 
   - "Added X NEW profiles"
   - "SCRAPING PAGE X of Y"
   - "Profiles collected so far: X"

5. If you see these messages continuing, the scraper is still working
   but waiting to hit batch size (50) before saving.

6. If logs stopped after page 1-2, the service might have restarted.

CURRENT ISSUE:
- Scraper found 48 profiles on page 1
- Waiting for 50 profiles before saving (old batch size)
- Need to redeploy to activate new batch size of 20

TO FIX:
1. Click "Manual Deploy" > "Deploy latest commit" 
2. This will restart with BATCH_SIZE = 20
3. Future saves will happen every 20 profiles
""") 