import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.realtor_importer.brightdata_scraper import BrightDataScraper
import logging

logging.basicConfig(level=logging.INFO)

async def test_profile():
    """Test scraping a specific agent profile"""
    scraper = BrightDataScraper()
    
    # Test with a real agent URL from the test output
    test_url = "https://www.homes.com/real-estate-agents/elissa-jarke/egrrtjm/"
    
    print(f"\nTesting profile scrape for: {test_url}")
    result = await scraper.scrape_agent_profile(test_url)
    
    if result:
        print("\n✓ Successfully scraped profile:")
        for key, value in result.items():
            if value and key != 'profile_url':
                print(f"  {key}: {value}")
    else:
        print("\n✗ Failed to scrape profile")

if __name__ == "__main__":
    asyncio.run(test_profile()) 