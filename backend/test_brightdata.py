import asyncio
import os
from playwright.async_api import async_playwright

async def test_brightdata():
    """Test Bright Data connection with different approaches"""
    
    ws_endpoint = os.getenv('BRIGHTDATA_BROWSER_URL', 
        'wss://brd-customer-hl_6f2331cd-zone-homes_come_scraper:j510f1n5xwty@brd.superproxy.io:9222')
    
    print(f"Testing Bright Data connection...")
    print(f"Endpoint: {ws_endpoint[:50]}...")
    
    playwright = await async_playwright().start()
    browser = None
    
    try:
        # Connect to Bright Data
        print("\n1. Connecting to Bright Data Browser API...")
        browser = await playwright.chromium.connect_over_cdp(ws_endpoint)
        print("✅ Connected successfully!")
        
        # Get or create context and page
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            print(f"✅ Using existing context with {len(context.pages)} pages")
        else:
            context = await browser.new_context()
            print("✅ Created new context")
        
        pages = context.pages
        if pages:
            page = pages[0]
            print("✅ Using existing page")
        else:
            page = await context.new_page()
            print("✅ Created new page")
        
        # Test 1: Simple navigation to Google
        print("\n2. Testing navigation to Google...")
        try:
            await page.goto('https://www.google.com', wait_until='domcontentloaded', timeout=15000)
            title = await page.title()
            print(f"✅ Google loaded successfully! Title: {title}")
        except Exception as e:
            print(f"❌ Failed to load Google: {e}")
        
        # Test 2: Navigate to homes.com homepage first
        print("\n3. Testing navigation to homes.com homepage...")
        try:
            await page.goto('https://www.homes.com', wait_until='domcontentloaded', timeout=15000)
            title = await page.title()
            url = page.url
            print(f"✅ Homes.com homepage loaded! Title: {title}")
            print(f"   Current URL: {url}")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Then navigate to agents page
            print("\n4. Navigating to agents page from homepage...")
            await page.goto('https://www.homes.com/real-estate-agents/carlsbad-ca/', wait_until='domcontentloaded', timeout=15000)
            title = await page.title()
            url = page.url
            print(f"✅ Agents page loaded! Title: {title}")
            print(f"   Current URL: {url}")
            
            # Check page content
            content = await page.content()
            print(f"   Page content length: {len(content)} characters")
            
            # Look for signs of blocking
            if "captcha" in content.lower():
                print("⚠️  WARNING: Captcha detected!")
            elif "access denied" in content.lower():
                print("⚠️  WARNING: Access denied detected!")
            elif "blocked" in content.lower():
                print("⚠️  WARNING: Blocked message detected!")
            else:
                # Try to find agent links
                agent_links = await page.locator('a[href*="/real-estate-agents/"]').count()
                print(f"   Found {agent_links} agent links on page")
                
        except Exception as e:
            print(f"❌ Failed to load homes.com: {e}")
            
            # Try alternative approach
            print("\n5. Trying alternative approach - evaluating JavaScript...")
            try:
                # Navigate to a simple page first
                await page.goto('about:blank')
                
                # Use JavaScript to navigate
                await page.evaluate('''
                    window.location.href = 'https://www.homes.com/real-estate-agents/carlsbad-ca/';
                ''')
                
                # Wait for navigation
                await page.wait_for_load_state('domcontentloaded', timeout=15000)
                
                title = await page.title()
                url = page.url
                print(f"✅ JavaScript navigation worked! Title: {title}")
                print(f"   Current URL: {url}")
                
            except Exception as e2:
                print(f"❌ JavaScript navigation also failed: {e2}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nPossible issues:")
        print("1. Check if BRIGHTDATA_BROWSER_URL environment variable is set correctly")
        print("2. Verify your Bright Data credentials and zone settings")
        print("3. Contact Bright Data support about HTTP2 protocol errors with homes.com")
        
    finally:
        if browser:
            await browser.close()
            print("\n✅ Browser closed")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_brightdata()) 