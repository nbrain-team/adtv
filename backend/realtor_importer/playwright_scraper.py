import asyncio
import json
import re
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
import random

class RealtorPlaywrightScraper:
    """
    Enhanced scraper using Playwright with better bot detection evasion
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.data: List[Dict[str, Any]] = []
        
    async def setup_browser(self, headless=True):
        """Initialize browser with anti-detection settings"""
        playwright = await async_playwright().start()
        
        # Use chromium with specific launch options
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Create context with realistic viewport and user agent
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Add extra headers to appear more human
        await context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        
        return await context.new_page()
    
    async def human_like_delay(self, min_ms=500, max_ms=2000):
        """Add random human-like delays"""
        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)
    
    async def type_with_delays(self, page: Page, selector: str, text: str):
        """Type text with human-like delays between keystrokes"""
        element = page.locator(selector)
        await element.click()
        await element.type(text, delay=random.randint(50, 150))
    
    async def scrape_realtor_list_page(self, page: Page, list_url: str) -> List[str]:
        """Scrape a homes.com list page for profile links"""
        print(f"Navigating to list page: {list_url}")
        
        # Navigate with timeout and wait strategies
        await page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for the page to be fully loaded
        await page.wait_for_load_state("networkidle")
        await self.human_like_delay()
        
        # Scroll to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await self.human_like_delay()
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.human_like_delay()
        
        profile_links = set()
        
        # Try multiple selectors for agent cards on homes.com
        selectors = [
            'a[href*="/real-estate-agents/"]',
            'a[href*="/agent/"]',
            '.agent-card a',
            '.agent-list-card a',
            'div[data-testid*="agent"] a',
            'a.agent-name',
            '.agent-card-details-container a'
        ]
        
        for selector in selectors:
            elements = await page.locator(selector).all()
            for element in elements:
                try:
                    href = await element.get_attribute('href')
                    if href and ('/real-estate-agents/' in href or '/agent/' in href):
                        # Ensure absolute URL
                        if not href.startswith('http'):
                            href = f"https://www.homes.com{href}"
                        profile_links.add(href)
                except:
                    continue
        
        print(f"Found {len(profile_links)} profile links")
        return list(profile_links)
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and strip text content"""
        return text.strip() if text else None
    
    def parse_numeric(self, text: Optional[str]) -> Optional[int]:
        """Parse numeric values from text"""
        if not text:
            return None
        cleaned = re.sub(r'[^\d]', '', text)
        return int(cleaned) if cleaned else None
    
    async def scrape_realtor_profile_page(self, page: Page, profile_url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual realtor profile with enhanced techniques"""
        print(f"Scraping profile: {profile_url}")
        
        try:
            # Navigate to profile with retry logic
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_load_state("networkidle")
            await self.human_like_delay()
            
            data = {"profile_url": profile_url}
            
            # Wait for key elements to ensure page is loaded
            try:
                await page.wait_for_selector('h1', timeout=10000)
            except:
                print(f"Failed to load profile page: {profile_url}")
                return None
            
            # Extract name - homes.com specific selectors
            name_selectors = [
                'h1[data-testid="agent-name"]',
                'h1.agent-name',
                'h1[class*="agent-name"]',
                '.agent-detail-name h1',
                'h1'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = await page.locator(selector).first
                    if await name_element.count() > 0:
                        full_name = await name_element.inner_text()
                        parts = full_name.strip().split(' ', 1)
                        data['first_name'] = parts[0] if parts else None
                        data['last_name'] = parts[1] if len(parts) > 1 else None
                        break
                except:
                    continue
            
            # Extract company
            company_selectors = [
                '[data-testid="agent-brokerage"]',
                '.brokerage-name',
                '.agent-broker-info',
                'div[class*="brokerage"]',
                '.agent-company'
            ]
            
            for selector in company_selectors:
                try:
                    element = await page.locator(selector).first
                    if await element.count() > 0:
                        data['company'] = self.clean_text(await element.inner_text())
                        break
                except:
                    continue
            
            # Extract location
            location_selectors = [
                '[data-testid="agent-location"]',
                '.agent-location',
                '.agent-address',
                'div[class*="location"]',
                '.agent-city-state'
            ]
            
            for selector in location_selectors:
                try:
                    element = await page.locator(selector).first
                    if await element.count() > 0:
                        location_text = await element.inner_text()
                        parts = location_text.split(',')
                        data['city'] = self.clean_text(parts[0]) if parts else None
                        data['state'] = self.clean_text(parts[1]) if len(parts) > 1 else None
                        break
                except:
                    continue
            
            # Extract phone number (often requires interaction)
            phone_selectors = [
                'a[href^="tel:"]',
                'button:has-text("Call")',
                '[data-testid*="phone"]',
                '.agent-phone'
            ]
            
            for selector in phone_selectors:
                try:
                    element = await page.locator(selector).first
                    if await element.count() > 0:
                        # Hover to reveal if needed
                        await element.hover()
                        await self.human_like_delay(200, 500)
                        
                        # Try to get href or text
                        href = await element.get_attribute('href')
                        if href and href.startswith('tel:'):
                            data['cell_phone'] = href.replace('tel:', '')
                        else:
                            data['cell_phone'] = self.clean_text(await element.inner_text())
                        break
                except:
                    continue
            
            # Extract email
            email_element = await page.locator('a[href^="mailto:"]').first
            if await email_element.count() > 0:
                href = await email_element.get_attribute('href')
                data['email'] = href.replace('mailto:', '') if href else None
            
            # Extract sales data with scroll and wait
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await self.human_like_delay()
            
            # Look for stats sections
            stats_selectors = [
                '.agent-stats',
                '[data-testid*="stats"]',
                '.performance-data',
                'div[class*="statistics"]',
                '.agent-metrics'
            ]
            
            for selector in stats_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        # Extract various metrics
                        metrics_text = await page.locator(selector).inner_text()
                        
                        # Parse total deals
                        deals_match = re.search(r'(\d+)\s*(?:total\s*)?deals?', metrics_text, re.I)
                        if deals_match:
                            data['seller_deals_total_deals'] = int(deals_match.group(1))
                        
                        # Parse total value
                        value_match = re.search(r'\$([0-9,]+(?:\.\d+)?)[KMB]?', metrics_text)
                        if value_match:
                            value_str = value_match.group(1).replace(',', '')
                            data['seller_deals_total_value'] = int(float(value_str))
                        
                        # Parse average price
                        avg_match = re.search(r'avg.*?\$([0-9,]+)', metrics_text, re.I)
                        if avg_match:
                            avg_str = avg_match.group(1).replace(',', '')
                            data['seller_deals_avg_price'] = int(avg_str)
                except:
                    continue
            
            # Set default values for missing fields
            data.setdefault('dma', None)
            data.setdefault('source', 'homes.com')
            data.setdefault('years_exp', None)
            data.setdefault('fb_or_website', profile_url)
            
            return data
            
        except Exception as e:
            print(f"Error scraping profile {profile_url}: {str(e)}")
            return None
    
    async def scrape_profiles(self, profile_urls: List[str], max_profiles: int = 10):
        """Scrape multiple profiles with rate limiting"""
        page = await self.setup_browser(headless=True)
        scraped_data = []
        
        try:
            for i, url in enumerate(profile_urls[:max_profiles]):
                print(f"\nScraping profile {i+1}/{min(len(profile_urls), max_profiles)}")
                
                profile_data = await self.scrape_realtor_profile_page(page, url)
                if profile_data:
                    scraped_data.append(profile_data)
                
                # Random delay between profiles
                if i < len(profile_urls) - 1:
                    await self.human_like_delay(2000, 5000)
        
        finally:
            if self.browser:
                await self.browser.close()
        
        return scraped_data
    
    async def scrape_from_list_url(self, list_url: str, max_profiles: int = 10, batch_callback=None):
        """Complete scraping flow from list URL with batch callback support"""
        page = await self.setup_browser(headless=True)
        
        try:
            # Get profile links
            profile_links = await self.scrape_realtor_list_page(page, list_url)
            
            if not profile_links:
                print("No profile links found")
                return []
            
            # Scrape individual profiles
            scraped_data = []
            batch_data = []
            BATCH_SIZE = 50
            
            for i, profile_url in enumerate(profile_links[:max_profiles]):
                print(f"\nScraping profile {i+1}/{min(len(profile_links), max_profiles)}")
                
                # Navigate to profile in same page
                profile_data = await self.scrape_realtor_profile_page(page, profile_url)
                if profile_data:
                    scraped_data.append(profile_data)
                    batch_data.append(profile_data)
                    
                    # Call batch callback when we have BATCH_SIZE profiles
                    if batch_callback and len(batch_data) >= BATCH_SIZE:
                        batch_callback(batch_data)
                        batch_data = []
                        print(f"  ✓ Batch of {BATCH_SIZE} profiles saved")
                
                # Random delay between profiles
                if i < len(profile_links) - 1:
                    await self.human_like_delay(2000, 5000)
            
            # Don't forget remaining batch data
            if batch_callback and batch_data:
                batch_callback(batch_data)
                print(f"  ✓ Final batch of {len(batch_data)} profiles saved")
            
            return scraped_data
            
        finally:
            if self.browser:
                await self.browser.close()


def scrape_with_playwright(list_url: str, max_profiles: int = 10, batch_callback=None):
    """Wrapper function to run async scraper with batch callback support"""
    scraper = RealtorPlaywrightScraper()
    return asyncio.run(scraper.scrape_from_list_url(list_url, max_profiles, batch_callback)) 