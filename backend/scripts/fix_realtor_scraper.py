#!/usr/bin/env python3
"""
Fix the realtor scraper to continue scraping after saving URLs
"""
import os
import sys

def fix_scraper():
    """Fix the brightdata_scraper.py to not return early after saving URLs"""
    
    scraper_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'realtor_importer',
        'brightdata_scraper.py'
    )
    
    print(f"Fixing scraper at: {scraper_path}")
    
    # Read the file
    with open(scraper_path, 'r') as f:
        content = f.read()
    
    # Find and replace the problematic return statement
    old_code = '''        logger.info(f"✓ All {len(profile_urls)} profile URLs saved to database")
        logger.info("Profiles will be enriched with details in a future run")
        return []  # Return empty since we saved via callback'''
    
    new_code = '''        logger.info(f"✓ All {len(profile_urls)} profile URLs saved to database")
        logger.info("Now continuing to scrape full profile details...")
        # Don't return here - continue to Phase 2!'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        # Write the fixed content back
        with open(scraper_path, 'w') as f:
            f.write(content)
        
        print("✅ Fixed! The scraper will now:")
        print("   1. Save profile URLs immediately (to prevent data loss)")
        print("   2. Continue to scrape full profile details")
        print("   3. Update the saved profiles with complete information")
    else:
        print("❌ Could not find the problematic code to fix")
        print("   The file may have already been fixed or modified")

if __name__ == "__main__":
    fix_scraper() 