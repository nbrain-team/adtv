#!/usr/bin/env python3
"""Test the realtor scraper locally to identify issues"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from realtor_importer.scraper import scrape_realtor_list_with_playwright

def test_batch_callback(batch_data):
    """Test callback that just prints the batch data"""
    print(f"\n[BATCH CALLBACK] Received {len(batch_data)} profiles:")
    for i, profile in enumerate(batch_data[:3]):  # Show first 3
        print(f"  {i+1}. {profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')} - {profile.get('profile_url', 'N/A')}")
    if len(batch_data) > 3:
        print(f"  ... and {len(batch_data) - 3} more")
    print()

def main():
    # Test URL
    test_url = "https://www.homes.com/real-estate-agents/rockford-il/"
    
    print(f"Testing scraper with URL: {test_url}")
    print("Max profiles: 10")
    print("-" * 80)
    
    try:
        results = scrape_realtor_list_with_playwright(
            test_url, 
            max_profiles=10,
            batch_callback=test_batch_callback
        )
        
        print(f"\nFinal results: {len(results)} profiles scraped")
        
        if results:
            print("\nSample results:")
            for i, profile in enumerate(results[:5]):
                print(f"{i+1}. {profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')}")
                print(f"   Company: {profile.get('company', 'N/A')}")
                print(f"   Location: {profile.get('city', 'N/A')}, {profile.get('state', 'N/A')}")
                print(f"   URL: {profile.get('profile_url', 'N/A')}")
                print()
        else:
            print("\nNo profiles scraped - checking environment:")
            print(f"BRIGHTDATA_BROWSER_URL: {'Set' if os.getenv('BRIGHTDATA_BROWSER_URL') else 'NOT SET'}")
            print(f"BRIGHTDATA_API_TOKEN: {'Set' if os.getenv('BRIGHTDATA_API_TOKEN') else 'NOT SET'}")
            print(f"RESIDENTIAL_PROXY_URL: {'Set' if os.getenv('RESIDENTIAL_PROXY_URL') else 'NOT SET'}")
            
    except Exception as e:
        print(f"\nError during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 