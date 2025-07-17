import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Force the new zone
os.environ['BRIGHTDATA_BROWSER_URL'] = 'wss://brd-customer-hl_6f2331cd-zone-homes_scraper:o47ipk4as8nq@brd.superproxy.io:9222'

import logging
logging.basicConfig(level=logging.DEBUG)

from backend.realtor_importer.brightdata_scraper import BrightDataScraper

async def test_full_extraction():
    """Test full extraction with detailed logging"""
    scraper = BrightDataScraper()
    
    test_url = "https://www.homes.com/real-estate-agents/angel-huang/t03jjcb/"
    print(f"\nTesting full extraction for: {test_url}")
    print("="*80)
    
    result = await scraper.scrape_agent_profile(test_url)
    
    print("\n" + "="*80)
    print("EXTRACTION RESULTS:")
    print("="*80)
    
    if result:
        for key, value in result.items():
            status = "✓" if value else "✗"
            print(f"{status} {key}: {value}")
    else:
        print("✗ Failed to extract any data")
    
    print("\nNow testing the list page to see if it finds agent URLs correctly...")
    print("="*80)
    
    list_url = "https://www.homes.com/real-estate-agents/sacramento-ca/"
    profile_urls = await scraper.scrape_homes_list_with_pagination(list_url, max_profiles=5)
    
    print(f"\nFound {len(profile_urls)} agent profile URLs:")
    for i, url in enumerate(profile_urls[:5]):
        print(f"{i+1}. {url}")
    
    # Test one of the found profiles
    if profile_urls and len(profile_urls) > 1:
        print(f"\nTesting extraction on found profile: {profile_urls[1]}")
        print("="*80)
        
        result2 = await scraper.scrape_agent_profile(profile_urls[1])
        if result2:
            print("\nEXTRACTION RESULTS:")
            for key, value in result2.items():
                status = "✓" if value else "✗"
                print(f"{status} {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_full_extraction()) 