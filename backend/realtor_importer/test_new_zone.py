import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Force use of the new zone
os.environ['BRIGHTDATA_BROWSER_URL'] = 'wss://brd-customer-hl_6f2331cd-zone-homes_scraper:o47ipk4as8nq@brd.superproxy.io:9222'

from backend.realtor_importer.brightdata_scraper import BrightDataScraper
import logging

logging.basicConfig(level=logging.INFO)

async def test_new_zone():
    """Test the new homes_scraper zone"""
    scraper = BrightDataScraper()
    
    print(f"\nTesting new zone...")
    print(f"Endpoint: {scraper.ws_endpoint[:80]}...")
    
    # Test list page
    test_list_url = "https://www.homes.com/real-estate-agents/san-diego-ca/"
    print(f"\n1. Testing list page: {test_list_url}")
    
    profile_urls = await scraper.scrape_homes_list_with_pagination(test_list_url, max_profiles=5)
    print(f"Found {len(profile_urls)} profile URLs")
    
    if profile_urls:
        print("\nSample URLs:")
        for url in profile_urls[:3]:
            print(f"  - {url}")
        
        # Test profile page
        print(f"\n2. Testing profile page...")
        test_profile_url = profile_urls[0]
        result = await scraper.scrape_agent_profile(test_profile_url)
        
        if result:
            print("\n✓ Successfully scraped profile:")
            for key, value in result.items():
                if value and key not in ['profile_url', 'source', 'dma']:
                    print(f"  {key}: {value}")
        else:
            print("\n✗ Failed to scrape profile")
    else:
        print("\n✗ No profile URLs found")

if __name__ == "__main__":
    asyncio.run(test_new_zone()) 