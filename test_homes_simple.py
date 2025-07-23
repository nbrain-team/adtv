#!/usr/bin/env python3
"""
Simple synchronous test for Homes.com scraping
"""
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import playwright scraper components directly
from playwright.sync_api import sync_playwright
import time

def test_direct_playwright():
    """Test direct playwright without our wrapper"""
    print("🏠 Testing Direct Playwright Scrape of Homes.com")
    print("=" * 60)
    
    url = "https://www.homes.com/real-estate-agents/huntsville-al/"
    agents = []
    
    with sync_playwright() as p:
        # Launch browser
        print("🚀 Launching browser...")
        browser = p.chromium.launch(
            headless=False,  # Set to False to see what's happening
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
            ]
        )
        
        # Create context with anti-detection measures
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add extra headers
        context.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Create page
        page = context.new_page()
        
        # Remove automation indicators
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => {
                    return {
                        query: () => Promise.resolve({ state: 'granted' })
                    }
                }
            });
        """)
        
        try:
            print(f"📍 Navigating to: {url}")
            
            # Navigate with timeout
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            print(f"📡 Response status: {response.status if response else 'No response'}")
            
            # Wait a bit for dynamic content
            print("⏳ Waiting for content to load...")
            page.wait_for_timeout(3000)
            
            # Take screenshot for debugging
            page.screenshot(path="homes_page.png")
            print("📸 Screenshot saved as homes_page.png")
            
            # Check if we're blocked
            if "Access Denied" in page.content() or "blocked" in page.content().lower():
                print("❌ Detected blocking message")
                
            # Try to find agent cards
            print("🔍 Looking for agent cards...")
            
            # Multiple possible selectors
            selectors = [
                'div[data-testid="agent-list-card"]',
                'div.agent-card',
                'div.realtor-card',
                'div[class*="agent"]',
                'div[class*="realtor"]',
                'article[class*="agent"]',
                '.search-results-item',
                'div[class*="professional-card"]'
            ]
            
            agent_elements = None
            for selector in selectors:
                agent_elements = page.query_selector_all(selector)
                if agent_elements:
                    print(f"✅ Found {len(agent_elements)} elements with selector: {selector}")
                    break
            
            if not agent_elements:
                print("❌ No agent cards found with any selector")
                print("📄 Page title:", page.title())
                print("🔗 Current URL:", page.url)
                
                # Save page content for debugging
                with open("homes_content.html", "w") as f:
                    f.write(page.content())
                print("💾 Page content saved to homes_content.html")
                
            else:
                # Extract agent data
                print(f"📊 Extracting data from {len(agent_elements)} agents...")
                
                for i, element in enumerate(agent_elements[:20]):  # First 20
                    try:
                        agent = {}
                        
                        # Try to extract name
                        name_selectors = ['h2', 'h3', '.agent-name', '[class*="name"]']
                        for sel in name_selectors:
                            name_elem = element.query_selector(sel)
                            if name_elem:
                                agent['name'] = name_elem.inner_text().strip()
                                break
                        
                        # Try to extract other info
                        text_content = element.inner_text()
                        agent['text'] = text_content
                        
                        agents.append(agent)
                        print(f"  Agent {i+1}: {agent.get('name', 'Unknown')}")
                        
                    except Exception as e:
                        print(f"  Error extracting agent {i+1}: {e}")
                
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            browser.close()
    
    # Save results
    if agents:
        filename = f"homes_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(agents, f, indent=2)
        print(f"\n✅ Saved {len(agents)} agents to {filename}")
    else:
        print("\n❌ No agents found")
    
    return agents

if __name__ == "__main__":
    print("🧪 Homes.com Direct Scraping Test")
    print("This will open a browser window to show what's happening")
    print("-" * 60)
    
    agents = test_direct_playwright()
    
    print(f"\n📊 Final result: {len(agents) if agents else 0} agents scraped") 