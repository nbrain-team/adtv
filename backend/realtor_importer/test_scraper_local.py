#!/usr/bin/env python3
"""
Test script to debug homes.com scraping locally
Run this on your local machine to test different approaches
"""

import asyncio
import requests
from playwright.async_api import async_playwright
import time
import random

async def test_indirect_navigation():
    """Test the indirect navigation approach"""
    print("\n=== Testing Indirect Navigation with Playwright ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser to see what's happening
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Start from homepage
            print("1. Going to homes.com homepage...")
            await page.goto('https://www.homes.com', wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Take screenshot
            await page.screenshot(path='step1_homepage.png')
            print("   Screenshot saved: step1_homepage.png")
            
            # Look for agents link
            print("2. Looking for 'Find an Agent' link...")
            agent_links = [
                'text=Find an Agent',
                'text=Find Agents', 
                'text=Real Estate Agents',
                'a[href*="/real-estate-agents"]'
            ]
            
            clicked = False
            for selector in agent_links:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        print(f"   Found: {selector}")
                        await element.click()
                        clicked = True
                        break
                except:
                    continue
            
            if clicked:
                await page.wait_for_timeout(3000)
                await page.screenshot(path='step2_after_click.png')
                print("   Screenshot saved: step2_after_click.png")
                
                # Try to search for Pittsburgh
                print("3. Searching for Pittsburgh...")
                search_input = page.locator('input[type="text"], input[type="search"]').first
                if await search_input.count() > 0:
                    await search_input.fill('Pittsburgh PA')
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(5000)
                    await page.screenshot(path='step3_search_results.png')
                    print("   Screenshot saved: step3_search_results.png")
                    
                    # Check if we have agent results
                    agent_cards = await page.locator('a[href*="/real-estate-agents/"]').all()
                    print(f"   Found {len(agent_cards)} agent links")
            else:
                print("   Could not find agent navigation link")
                
        except Exception as e:
            print(f"   Error: {e}")
        finally:
            await browser.close()

def test_direct_request():
    """Test direct HTTP request"""
    print("\n=== Testing Direct HTTP Request ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    url = 'https://www.homes.com/real-estate-agents/pittsburgh-pa/'
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 403:
            print("\n403 Forbidden - Site is blocking direct requests")
            print("Response preview:", response.text[:500])
        elif response.status_code == 200:
            print("\nSuccess! Response length:", len(response.text))
            # Save response for analysis
            with open('direct_response.html', 'w') as f:
                f.write(response.text)
            print("Response saved to direct_response.html")
    except Exception as e:
        print(f"Error: {e}")

async def test_with_cookies():
    """Test with cookie collection"""
    print("\n=== Testing with Cookie Collection ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # First visit homepage to get cookies
        print("1. Visiting homepage to collect cookies...")
        await page.goto('https://www.homes.com')
        await page.wait_for_timeout(3000)
        
        # Get cookies
        cookies = await context.cookies()
        print(f"   Collected {len(cookies)} cookies")
        
        # Now try direct navigation with cookies
        print("2. Trying direct navigation to agent page...")
        await page.goto('https://www.homes.com/real-estate-agents/pittsburgh-pa/')
        await page.wait_for_timeout(3000)
        
        # Check if we got blocked
        if "403" in await page.title() or "blocked" in await page.content().lower():
            print("   Still blocked even with cookies")
        else:
            print("   Success! Page loaded")
            await page.screenshot(path='with_cookies_result.png')
            
        await browser.close()

if __name__ == "__main__":
    print("Starting homes.com scraper tests...")
    print("This will help debug why the scraper is getting blocked\n")
    
    # Test 1: Direct request
    test_direct_request()
    
    # Test 2: Indirect navigation
    asyncio.run(test_indirect_navigation())
    
    # Test 3: With cookies
    asyncio.run(test_with_cookies())
    
    print("\nTests complete! Check the screenshots and output above.") 