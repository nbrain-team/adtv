import asyncio
import re
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
import random
import time

class IndirectNavigationScraper:
    """
    Scraper that navigates indirectly from homepage to avoid bot detection
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    async def setup_browser(self, headless=True):
        """Initialize browser with anti-detection settings"""
        playwright = await async_playwright().start()
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized'
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060}  # NYC
        )
        
        # Set realistic headers
        await context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        page = await context.new_page()
        
        # Remove webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return page
    
    async def human_delay(self, min_ms=500, max_ms=2000):
        """Add random human-like delays"""
        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)
    
    async def mouse_hover_and_click(self, page: Page, selector: str):
        """Hover over element before clicking like a human would"""
        element = page.locator(selector).first
        if await element.count() > 0:
            await element.hover()
            await self.human_delay(200, 500)
            await element.click()
            return True
        return False
    
    async def navigate_to_agent_search(self, page: Page, location: str) -> bool:
        """Navigate from homepage to agent search naturally"""
        print("Starting indirect navigation from homepage...")
        
        # Go to homepage
        await page.goto('https://www.homes.com', wait_until='domcontentloaded', timeout=60000)
        await self.human_delay(2000, 4000)
        
        # Look for "Find an Agent" or similar link
        agent_link_selectors = [
            'a:has-text("Find an Agent")',
            'a:has-text("Find Agents")',
            'a:has-text("Real Estate Agents")',
            'a[href*="/real-estate-agents"]',
            'nav a:has-text("Agents")',
            '.nav-link:has-text("Agents")'
        ]
        
        clicked = False
        for selector in agent_link_selectors:
            if await self.mouse_hover_and_click(page, selector):
                clicked = True
                break
        
        if not clicked:
            print("Could not find agent link, trying menu...")
            # Try to open menu first
            menu_selectors = ['button[aria-label*="menu"]', '.menu-button', '#menu-toggle']
            for selector in menu_selectors:
                if await self.mouse_hover_and_click(page, selector):
                    await self.human_delay(1000, 2000)
                    # Try agent links again
                    for agent_selector in agent_link_selectors:
                        if await self.mouse_hover_and_click(page, agent_selector):
                            clicked = True
                            break
                    if clicked:
                        break
        
        if not clicked:
            print("Could not find agent navigation link")
            return False
        
        # Wait for navigation
        await self.human_delay(2000, 4000)
        await page.wait_for_load_state('networkidle')
        
        # Now search for location
        search_selectors = [
            'input[placeholder*="city"]',
            'input[placeholder*="location"]',
            'input[placeholder*="where"]',
            'input[type="search"]',
            '#location-search',
            '.search-input'
        ]
        
        for selector in search_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    await element.click()
                    await self.human_delay(500, 1000)
                    
                    # Clear existing text
                    await element.fill('')
                    await self.human_delay(300, 600)
                    
                    # Type location with human-like delays
                    for char in location:
                        await element.type(char, delay=random.randint(50, 150))
                    
                    await self.human_delay(1000, 2000)
                    
                    # Press Enter or click search
                    await page.keyboard.press('Enter')
                    await self.human_delay(3000, 5000)
                    
                    return True
            except:
                continue
        
        return False
    
    async def scrape_agent_list(self, page: Page) -> List[str]:
        """Scrape agent profile links from the list page"""
        print("Scraping agent list...")
        
        # Wait for agents to load
        await page.wait_for_load_state('networkidle')
        
        # Scroll to load more agents
        for i in range(3):
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4})")
            await self.human_delay(1000, 2000)
        
        profile_links = set()
        
        # Try multiple selectors
        selectors = [
            'a[href*="/real-estate-agents/"]',
            'a[href*="/agent/"]',
            '.agent-card a[href*="/real-estate-agents/"]',
            '.agent-list-item a',
            'div[class*="agent"] a[href*="/real-estate-agents/"]'
        ]
        
        for selector in selectors:
            elements = await page.locator(selector).all()
            for element in elements:
                try:
                    href = await element.get_attribute('href')
                    if href and ('/real-estate-agents/' in href or '/agent/' in href):
                        if not href.startswith('http'):
                            href = f"https://www.homes.com{href}"
                        profile_links.add(href)
                except:
                    continue
        
        print(f"Found {len(profile_links)} agent profiles")
        return list(profile_links)
    
    async def scrape_with_indirect_navigation(self, location: str, max_profiles: int = 10):
        """Main scraping method using indirect navigation"""
        page = await self.setup_browser(headless=True)
        
        try:
            # Navigate indirectly
            if not await self.navigate_to_agent_search(page, location):
                print("Failed to navigate to agent search")
                return []
            
            # Get profile links
            profile_links = await self.scrape_agent_list(page)
            
            if not profile_links:
                print("No profile links found")
                return []
            
            # For now, just return the profile links
            # Profile scraping would be implemented similarly
            return [{"profile_url": url, "source": "homes.com"} for url in profile_links[:max_profiles]]
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return []
        finally:
            if self.browser:
                await self.browser.close()


def scrape_indirect(location: str, max_profiles: int = 10) -> List[Dict[str, Any]]:
    """Synchronous wrapper for indirect navigation scraper"""
    scraper = IndirectNavigationScraper()
    
    # Extract city from the URL if a full URL is provided
    if location.startswith('http'):
        # Extract city from URL like /real-estate-agents/pittsburgh-pa/
        match = re.search(r'/real-estate-agents/([^/]+)', location)
        if match:
            location = match.group(1).replace('-', ' ')
        else:
            location = "Pittsburgh PA"  # Default
    
    return asyncio.run(scraper.scrape_with_indirect_navigation(location, max_profiles)) 