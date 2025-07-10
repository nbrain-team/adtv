import asyncio
import os
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
import random
import requests
from bs4 import BeautifulSoup

class ProxyRealtorScraper:
    """
    Scraper that uses residential proxies to avoid blocks
    """
    
    def __init__(self):
        # Get proxy settings from environment variables
        self.proxy_url = os.getenv('RESIDENTIAL_PROXY_URL')  # e.g., http://username:password@proxy.provider.com:port
        self.browser: Optional[Browser] = None
        
        if not self.proxy_url:
            print("WARNING: No RESIDENTIAL_PROXY_URL set. Scraping may be blocked.")
    
    async def setup_browser_with_proxy(self, headless=True):
        """Initialize browser with proxy settings"""
        playwright = await async_playwright().start()
        
        # Parse proxy URL
        if self.proxy_url:
            # Extract components from proxy URL
            # Format: http://username:password@host:port
            import urllib.parse
            parsed = urllib.parse.urlparse(self.proxy_url)
            
            proxy_config = {
                "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                "username": parsed.username,
                "password": parsed.password
            }
        else:
            proxy_config = None
        
        # Launch browser with proxy
        self.browser = await playwright.chromium.launch(
            headless=headless,
            proxy=proxy_config,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        return await context.new_page()
    
    def scrape_with_requests_proxy(self, url: str) -> Optional[BeautifulSoup]:
        """Fallback scraping with requests + proxy"""
        if not self.proxy_url:
            print("No proxy configured for requests")
            return None
        
        proxies = {
            'http': self.proxy_url,
            'https': self.proxy_url
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"Request failed with status: {response.status_code}")
                return None
        except Exception as e:
            print(f"Proxy request failed: {e}")
            return None
    
    async def scrape_list_page_with_proxy(self, list_url: str) -> List[str]:
        """Scrape homes.com list page using proxy"""
        print(f"Scraping with proxy: {list_url}")
        
        # Try Playwright first
        try:
            page = await self.setup_browser_with_proxy()
            await page.goto(list_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Extract agent profile links
            profile_links = set()
            selectors = [
                'a[href*="/real-estate-agents/"]',
                '.agent-card a[href*="/real-estate-agents/"]',
                'a.agent-name'
            ]
            
            for selector in selectors:
                elements = await page.locator(selector).all()
                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        if href and '/real-estate-agents/' in href:
                            if not href.startswith('http'):
                                href = f"https://www.homes.com{href}"
                            profile_links.add(href)
                    except:
                        continue
            
            print(f"Found {len(profile_links)} profiles with Playwright + proxy")
            return list(profile_links)
            
        except Exception as e:
            print(f"Playwright proxy scraping failed: {e}")
            
            # Fallback to requests + proxy
            soup = self.scrape_with_requests_proxy(list_url)
            if soup:
                profile_links = set()
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/real-estate-agents/' in href:
                        if not href.startswith('http'):
                            href = f"https://www.homes.com{href}"
                        profile_links.add(href)
                
                print(f"Found {len(profile_links)} profiles with requests + proxy")
                return list(profile_links)
            
            return []
        finally:
            if self.browser:
                await self.browser.close()
    
    async def scrape_profile_with_proxy(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual profile using proxy"""
        soup = self.scrape_with_requests_proxy(profile_url)
        if not soup:
            return None
        
        data = {"profile_url": profile_url, "source": "homes.com"}
        
        # Extract name
        name_elem = soup.find('h1', class_='agent-name') or soup.find('h1')
        if name_elem:
            full_name = name_elem.get_text().strip()
            parts = full_name.split(' ', 1)
            data['first_name'] = parts[0] if parts else None
            data['last_name'] = parts[1] if len(parts) > 1 else None
        
        # Extract company
        company_elem = soup.find(class_='brokerage-name') or soup.find('div', {'data-testid': 'agent-brokerage'})
        if company_elem:
            data['company'] = company_elem.get_text().strip()
        
        # Extract location
        location_elem = soup.find(class_='agent-location') or soup.find('div', {'data-testid': 'agent-location'})
        if location_elem:
            location_text = location_elem.get_text().strip()
            parts = location_text.split(',')
            data['city'] = parts[0].strip() if parts else None
            data['state'] = parts[1].strip() if len(parts) > 1 else None
        
        # Extract phone
        phone_elem = soup.find('a', href=lambda x: x and x.startswith('tel:'))
        if phone_elem:
            data['cell_phone'] = phone_elem['href'].replace('tel:', '')
        
        # Extract email
        email_elem = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
        if email_elem:
            data['email'] = email_elem['href'].replace('mailto:', '')
        
        return data


async def scrape_with_proxy(list_url: str, max_profiles: int = 10, batch_callback=None) -> List[Dict[str, Any]]:
    """Main entry point for proxy scraping with batch callback support"""
    scraper = ProxyRealtorScraper()
    
    # Get profile URLs
    profile_urls = await scraper.scrape_list_page_with_proxy(list_url)
    
    if not profile_urls:
        print("No profiles found")
        return []
    
    # Scrape individual profiles
    results = []
    batch_data = []
    BATCH_SIZE = 50
    
    for i, url in enumerate(profile_urls[:max_profiles]):
        print(f"Scraping profile {i+1}/{min(len(profile_urls), max_profiles)}: {url}")
        profile_data = await scraper.scrape_profile_with_proxy(url)
        if profile_data:
            results.append(profile_data)
            batch_data.append(profile_data)
            
            # Call batch callback when we have BATCH_SIZE profiles
            if batch_callback and len(batch_data) >= BATCH_SIZE:
                batch_callback(batch_data)
                batch_data = []
                print(f"  ✓ Batch of {BATCH_SIZE} profiles saved")
        
        # Add delay between requests
        if i < len(profile_urls) - 1:
            await asyncio.sleep(random.uniform(2, 4))
    
    # Don't forget remaining batch data
    if batch_callback and batch_data:
        batch_callback(batch_data)
        print(f"  ✓ Final batch of {len(batch_data)} profiles saved")
    
    return results


# For testing
if __name__ == "__main__":
    # Test with a proxy
    # Set environment variable first: export RESIDENTIAL_PROXY_URL="http://username:password@proxy.provider.com:port"
    url = "https://www.homes.com/real-estate-agents/pittsburgh-pa/"
    results = asyncio.run(scrape_with_proxy(url, max_profiles=5))
    print(f"\nScraped {len(results)} profiles:")
    for r in results:
        print(f"- {r.get('first_name')} {r.get('last_name')} at {r.get('company')}") 