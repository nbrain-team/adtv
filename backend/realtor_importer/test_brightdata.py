import asyncio
from playwright.async_api import async_playwright
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_brightdata_connection():
    """Test Bright Data connection and see what we're actually getting"""
    
    # The Bright Data endpoint
    ws_endpoint = os.getenv('BRIGHTDATA_BROWSER_URL', 
        'wss://brd-customer-hl_6f2331cd-zone-scraping_browser1:e8rrfhil917u@brd.superproxy.io:9222')
    
    logger.info(f"Testing connection to: {ws_endpoint[:50]}...")
    
    browser = None
    try:
        playwright = await async_playwright().start()
        
        # Connect to Bright Data
        logger.info("Connecting to Bright Data Browser API...")
        browser = await playwright.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
        logger.info("✓ Connected successfully!")
        
        # Create a new page
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()
        logger.info("✓ Created new page")
        
        # Test URL
        test_url = "https://www.homes.com/real-estate-agents/rockford-il/"
        logger.info(f"\nNavigating to: {test_url}")
        
        # Navigate to the page
        await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
        logger.info("✓ Page loaded")
        
        # Get page title
        title = await page.title()
        logger.info(f"Page title: {title}")
        
        # Get current URL (might be different if redirected)
        current_url = page.url
        logger.info(f"Current URL: {current_url}")
        
        # Check for common issues
        page_text = await page.inner_text('body')
        page_text_lower = page_text.lower()
        
        if 'captcha' in page_text_lower:
            logger.error("❌ CAPTCHA detected!")
        elif 'access denied' in page_text_lower or '403' in page_text_lower:
            logger.error("❌ Access denied!")
        elif 'not found' in page_text_lower or '404' in page_text_lower:
            logger.error("❌ Page not found!")
        else:
            logger.info("✓ No obvious errors detected")
        
        # Try to find agent elements
        logger.info("\nSearching for agent elements...")
        
        # Check for agent cards
        selectors_to_test = [
            'a[href*="/real-estate-agents/"]',
            '.agent-card',
            '[class*="agent"]',
            '[class*="realtor"]',
            'a[href*="/profile/"]',
            '[data-testid*="agent"]'
        ]
        
        for selector in selectors_to_test:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.info(f"✓ Found {count} elements with selector: {selector}")
                    # Get first few examples
                    if count > 0:
                        first_elem = await page.locator(selector).first
                        text = await first_elem.inner_text() if await first_elem.count() > 0 else "N/A"
                        logger.info(f"  Example text: {text[:50]}...")
            except:
                pass
        
        # Get all links on the page that might be agent profiles
        agent_links = await page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a').forEach(a => {
                    const href = a.href;
                    if (href && (href.includes('/real-estate-agents/') || href.includes('/agent/') || href.includes('/profile/'))) {
                        links.push({
                            href: href,
                            text: a.innerText.substring(0, 30)
                        });
                    }
                });
                return links.slice(0, 5); // First 5 links
            }
        """)
        
        logger.info(f"\nFound {len(agent_links)} potential agent links:")
        for link in agent_links:
            logger.info(f"  - {link['text']} -> {link['href']}")
        
        # Take a screenshot for debugging
        screenshot_path = "/tmp/brightdata_test.png"
        await page.screenshot(path=screenshot_path)
        logger.info(f"\n✓ Screenshot saved to: {screenshot_path}")
        
        # Get page HTML structure
        html_structure = await page.evaluate("""
            () => {
                const structure = {
                    title: document.title,
                    h1Count: document.querySelectorAll('h1').length,
                    h1Texts: Array.from(document.querySelectorAll('h1')).map(h => h.innerText.substring(0, 50)),
                    mainTags: Array.from(document.querySelectorAll('main, .main, #main')).length,
                    totalLinks: document.querySelectorAll('a').length,
                    agentRelatedElements: document.querySelectorAll('[class*="agent"], [class*="realtor"]').length
                };
                return structure;
            }
        """)
        
        logger.info("\nPage structure analysis:")
        logger.info(f"  Title: {html_structure['title']}")
        logger.info(f"  H1 tags: {html_structure['h1Count']}")
        logger.info(f"  H1 texts: {html_structure['h1Texts']}")
        logger.info(f"  Main sections: {html_structure['mainTags']}")
        logger.info(f"  Total links: {html_structure['totalLinks']}")
        logger.info(f"  Agent-related elements: {html_structure['agentRelatedElements']}")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if browser:
            await browser.close()
        logger.info("\n✓ Test completed")

if __name__ == "__main__":
    asyncio.run(test_brightdata_connection()) 