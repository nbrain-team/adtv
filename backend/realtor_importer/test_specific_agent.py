import asyncio
from playwright.async_api import async_playwright
import os

async def analyze_agent_page():
    """Analyze the specific agent page to understand its structure"""
    
    # Use the new zone
    ws_endpoint = 'wss://brd-customer-hl_6f2331cd-zone-homes_scraper:o47ipk4as8nq@brd.superproxy.io:9222'
    test_url = "https://www.homes.com/real-estate-agents/angel-huang/t03jjcb/"
    
    print(f"Analyzing: {test_url}")
    
    browser = None
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
        
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to page...")
        await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
        
        # Get page title
        title = await page.title()
        print(f"\nPage Title: {title}")
        
        # Analyze the HTML structure
        structure_info = await page.evaluate("""
            () => {
                const info = {
                    // Find all h1 elements
                    h1_elements: Array.from(document.querySelectorAll('h1')).map(h => ({
                        text: h.innerText,
                        className: h.className,
                        id: h.id
                    })),
                    
                    // Find elements that might contain the name
                    name_candidates: [],
                    
                    // Find elements that might contain company
                    company_candidates: [],
                    
                    // Find elements that might contain location
                    location_candidates: [],
                    
                    // Find phone/contact elements
                    phone_candidates: []
                };
                
                // Look for name in various places
                ['[class*="name"]', '[class*="agent"]', '[class*="profile"]', 'h1', 'h2'].forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        const text = el.innerText?.trim();
                        if (text && text.includes('Angel') || text.includes('Huang')) {
                            info.name_candidates.push({
                                selector: selector,
                                tag: el.tagName,
                                className: el.className,
                                text: text.substring(0, 100)
                            });
                        }
                    });
                });
                
                // Look for company
                ['[class*="broker"]', '[class*="company"]', '[class*="agency"]', '[class*="realty"]'].forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        const text = el.innerText?.trim();
                        if (text && text.length > 3 && text.length < 100) {
                            info.company_candidates.push({
                                selector: selector,
                                tag: el.tagName,
                                className: el.className,
                                text: text
                            });
                        }
                    });
                });
                
                // Look for location
                ['[class*="location"]', '[class*="address"]', '[class*="city"]', '[class*="state"]'].forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        const text = el.innerText?.trim();
                        if (text && text.length > 3 && text.length < 100) {
                            info.location_candidates.push({
                                selector: selector,
                                tag: el.tagName,
                                className: el.className,
                                text: text
                            });
                        }
                    });
                });
                
                // Look for phone
                document.querySelectorAll('a[href^="tel:"], [class*="phone"], button').forEach(el => {
                    const text = el.innerText?.trim() || '';
                    const href = el.getAttribute('href') || '';
                    if (href.startsWith('tel:') || text.includes('Call') || text.match(/\d{3}.*\d{3}.*\d{4}/)) {
                        info.phone_candidates.push({
                            tag: el.tagName,
                            className: el.className,
                            text: text,
                            href: href
                        });
                    }
                });
                
                return info;
            }
        """)
        
        # Print the findings
        print("\n=== H1 ELEMENTS ===")
        for h1 in structure_info['h1_elements']:
            print(f"H1: {h1['text']} (class: {h1['className']})")
        
        print("\n=== NAME CANDIDATES ===")
        for candidate in structure_info['name_candidates'][:5]:
            print(f"{candidate['tag']}.{candidate['className']}: {candidate['text']}")
        
        print("\n=== COMPANY CANDIDATES ===")
        for candidate in structure_info['company_candidates'][:5]:
            print(f"{candidate['tag']}.{candidate['className']}: {candidate['text']}")
        
        print("\n=== LOCATION CANDIDATES ===")
        for candidate in structure_info['location_candidates'][:5]:
            print(f"{candidate['tag']}.{candidate['className']}: {candidate['text']}")
        
        print("\n=== PHONE CANDIDATES ===")
        for candidate in structure_info['phone_candidates'][:5]:
            print(f"{candidate['tag']}.{candidate['className']}: {candidate['text']} (href: {candidate['href']})")
        
        # Take a screenshot
        await page.screenshot(path="/tmp/angel_huang_page.png")
        print("\nScreenshot saved to /tmp/angel_huang_page.png")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_agent_page()) 