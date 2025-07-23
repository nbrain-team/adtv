#!/usr/bin/env python3
"""
Local test script for Homes.com scraper
Tests scraping https://www.homes.com/real-estate-agents/huntsville-al/
"""
import os
import sys
import asyncio
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the scrapers
from realtor_importer.brightdata_scraper import scrape_homes_brightdata
from realtor_importer.web_unlocker_scraper import scrape_with_web_unlocker
from realtor_importer.proxy_scraper import scrape_with_proxy
from realtor_importer.playwright_scraper import scrape_with_playwright

def print_agent_info(agent):
    """Pretty print agent information"""
    print("\n" + "="*60)
    print(f"Name: {agent.get('name', 'N/A')}")
    print(f"Company: {agent.get('company', 'N/A')}")
    print(f"Location: {agent.get('location', 'N/A')}")
    print(f"Phone: {agent.get('phone', 'N/A')}")
    print(f"Profile URL: {agent.get('profile_url', 'N/A')}")
    if agent.get('specialties'):
        print(f"Specialties: {', '.join(agent['specialties'])}")
    print("="*60)

async def test_brightdata_scraper():
    """Test Bright Data scraper"""
    print("\n🔍 Testing Bright Data Scraper...")
    
    # Check for API key
    if not os.getenv('BRIGHTDATA_BROWSER_URL'):
        print("❌ BRIGHTDATA_BROWSER_URL not set in environment")
        print("Set it with: export BRIGHTDATA_BROWSER_URL='wss://...'")
        return None
    
    try:
        url = "https://www.homes.com/real-estate-agents/huntsville-al/"
        print(f"Scraping: {url}")
        
        agents = await scrape_homes_brightdata(url, page_limit=1)
        
        if agents:
            print(f"\n✅ Successfully scraped {len(agents)} agents!")
            for i, agent in enumerate(agents[:5]):  # Show first 5
                print_agent_info(agent)
        else:
            print("❌ No agents found")
            
        return agents
    except Exception as e:
        print(f"❌ Bright Data scraper failed: {str(e)}")
        return None

def test_web_unlocker_scraper():
    """Test Web Unlocker scraper"""
    print("\n🔍 Testing Web Unlocker Scraper...")
    
    # Check for API token
    if not os.getenv('BRIGHTDATA_API_TOKEN'):
        print("❌ BRIGHTDATA_API_TOKEN not set in environment")
        print("Set it with: export BRIGHTDATA_API_TOKEN='your_token'")
        return None
    
    try:
        url = "https://www.homes.com/real-estate-agents/huntsville-al/"
        print(f"Scraping: {url}")
        
        agents = scrape_with_web_unlocker(url, page_limit=1)
        
        if agents:
            print(f"\n✅ Successfully scraped {len(agents)} agents!")
            for i, agent in enumerate(agents[:5]):  # Show first 5
                print_agent_info(agent)
        else:
            print("❌ No agents found")
            
        return agents
    except Exception as e:
        print(f"❌ Web Unlocker scraper failed: {str(e)}")
        return None

def test_playwright_scraper():
    """Test Playwright scraper (no proxy)"""
    print("\n🔍 Testing Playwright Scraper (local)...")
    
    try:
        url = "https://www.homes.com/real-estate-agents/huntsville-al/"
        print(f"Scraping: {url}")
        
        agents = scrape_with_playwright(url, max_profiles=20)  # Get first 20 agents
        
        if agents:
            print(f"\n✅ Successfully scraped {len(agents)} agents!")
            for i, agent in enumerate(agents[:5]):  # Show first 5
                print_agent_info(agent)
        else:
            print("❌ No agents found")
            
        return agents
    except Exception as e:
        print(f"❌ Playwright scraper failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_results(agents, scraper_name):
    """Save scraping results to a JSON file"""
    if agents:
        filename = f"homes_scrape_{scraper_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(agents, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")

async def main():
    """Run all tests"""
    print("🏠 Homes.com Local Scraper Test")
    print("================================")
    print(f"Target URL: https://www.homes.com/real-estate-agents/huntsville-al/")
    print(f"Expected: ~689 agents")
    
    # Check which environment variables are set
    print("\n📋 Environment Check:")
    print(f"BRIGHTDATA_API_TOKEN: {'✅ Set' if os.getenv('BRIGHTDATA_API_TOKEN') else '❌ Not set'}")
    print(f"BRIGHTDATA_BROWSER_URL: {'✅ Set' if os.getenv('BRIGHTDATA_BROWSER_URL') else '❌ Not set'}")
    
    # Test each scraper method
    results = {}
    
    # 1. Try Bright Data Browser API (most reliable)
    if os.getenv('BRIGHTDATA_BROWSER_URL'):
        agents = await test_brightdata_scraper()
        if agents:
            results['brightdata'] = agents
            save_results(agents, 'brightdata')
    
    # 2. Try Web Unlocker API
    if os.getenv('BRIGHTDATA_API_TOKEN'):
        agents = test_web_unlocker_scraper()
        if agents:
            results['web_unlocker'] = agents
            save_results(agents, 'web_unlocker')
    
    # 3. Try local Playwright (likely to be blocked)
    print("\n⚠️  Note: Local Playwright is likely to be blocked by Homes.com")
    agents = test_playwright_scraper()
    if agents:
        results['playwright'] = agents
        save_results(agents, 'playwright')
    
    # Summary
    print("\n📊 Summary:")
    for scraper, agents in results.items():
        print(f"  - {scraper}: {len(agents)} agents scraped")
    
    if not results:
        print("\n❌ All scrapers failed. Please check:")
        print("1. Set BRIGHTDATA_API_TOKEN or BRIGHTDATA_BROWSER_URL")
        print("2. Ensure you have valid Bright Data credentials")
        print("3. Check your internet connection")
        print("\nTo set environment variables:")
        print("export BRIGHTDATA_API_TOKEN='your_api_token'")
        print("export BRIGHTDATA_BROWSER_URL='wss://your_browser_url'")

if __name__ == "__main__":
    asyncio.run(main()) 