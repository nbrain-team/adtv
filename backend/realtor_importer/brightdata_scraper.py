import asyncio
import os
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
import random

class BrightDataScraper:
    """
    Scraper that uses Bright Data's Browser API for maximum success
    """
    
    def __init__(self):
        # Get Bright Data credentials from environment
        self.ws_endpoint = os.getenv('BRIGHTDATA_BROWSER_URL', 
            'wss://brd-customer-hl_6f2331cd-zone-homes_come_scraper:j510f1n5xwty@brd.superproxy.io:9222')
        
    async def connect_to_brightdata(self):
        """Connect to Bright Data's managed browser"""
        playwright = await async_playwright().start()
        
        print("Connecting to Bright Data Browser API...")
        # Connect to the remote browser instance
        browser = await playwright.chromium.connect_over_cdp(self.ws_endpoint)
        
        # Get the existing context (Bright Data manages this)
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = await browser.new_context()
        
        # Get or create a page
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()
            
        return browser, page
    
    async def human_delay(self, min_ms=500, max_ms=2000):
        """Add random human-like delays"""
        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)
    
    async def scrape_homes_list(self, list_url: str) -> List[str]:
        """Scrape homes.com list page using Bright Data browser"""
        browser = None
        try:
            browser, page = await self.connect_to_brightdata()
            
            print(f"Navigating to: {list_url}")
            # Use domcontentloaded instead of networkidle for better reliability
            await page.goto(list_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for agent cards to appear
            print("Waiting for page to load...")
            try:
                await page.wait_for_selector('.agent-card, .realtor-card, a[href*="/real-estate-agents/"]', timeout=10000)
            except:
                print("Warning: Could not find expected agent selectors, continuing anyway...")
            
            await self.human_delay(2000, 4000)
            
            # Scroll to load more results
            print("Scrolling to load more results...")
            for i in range(3):
                await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4})")
                await self.human_delay(1000, 2000)
            
            # Debug: Print page title and URL
            title = await page.title()
            current_url = page.url
            print(f"Page loaded - Title: {title}, URL: {current_url}")
            
            # Extract agent profile links
            profile_links = set()
            selectors = [
                'a[href*="/real-estate-agents/"]',
                '.agent-card a[href*="/profile/"]',
                '.agent-list-item a[href*="/real-estate-agents/"]',
                'a.agent-name',
                '.realtor-card a',
                '[class*="agent"] a[href*="/"]',  # More generic selector
                'div[class*="card"] a[href*="/real-estate-agents/"]'
            ]
            
            for selector in selectors:
                try:
                    elements = await page.locator(selector).all()
                    print(f"Checking selector '{selector}': found {len(elements)} elements")
                    for element in elements:
                        try:
                            href = await element.get_attribute('href')
                            if href and ('/real-estate-agents/' in href or '/profile/' in href):
                                if not href.startswith('http'):
                                    href = f"https://www.homes.com{href}"
                                # Filter out non-profile URLs
                                if not any(skip in href for skip in ['/search/', '/office/', '/company/', '/listings/']):
                                    profile_links.add(href)
                        except:
                            continue
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
            
            print(f"Found {len(profile_links)} agent profiles")
            if len(profile_links) == 0:
                # Debug: Try to print page content
                page_text = await page.content()
                print(f"Page content length: {len(page_text)} characters")
                # Check if we got a captcha or different page
                if "captcha" in page_text.lower():
                    print("WARNING: Captcha detected!")
                elif "access denied" in page_text.lower():
                    print("WARNING: Access denied!")
            
            return list(profile_links)
            
        except Exception as e:
            print(f"Error during list scraping: {e}")
            return []
        finally:
            if browser:
                await browser.close()
    
    async def scrape_homes_list_with_pagination(self, list_url: str, max_profiles: int = 700) -> List[str]:
        """Scrape homes.com list pages with pagination support"""
        all_profile_links = []
        current_url = list_url
        page_num = 1
        
        while len(all_profile_links) < max_profiles:
            print(f"\nScraping page {page_num}: {current_url}")
            browser = None
            
            try:
                browser, page = await self.connect_to_brightdata()
                
                print(f"Navigating to: {current_url}")
                await page.goto(current_url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for agent cards to appear
                print("Waiting for page to load...")
                try:
                    await page.wait_for_selector('.agent-card, .realtor-card, a[href*="/real-estate-agents/"]', timeout=10000)
                except:
                    print("Warning: Could not find expected agent selectors, continuing anyway...")
                
                await self.human_delay(2000, 4000)
                
                # Scroll to load more results
                print("Scrolling to load more results...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4})")
                    await self.human_delay(1000, 2000)
                
                # Extract agent profile links
                profile_links = set()
                selectors = [
                    'a[href*="/real-estate-agents/"]',
                    '.agent-card a[href*="/profile/"]',
                    '.agent-list-item a[href*="/real-estate-agents/"]',
                    'a.agent-name',
                    '.realtor-card a',
                    '[class*="agent"] a[href*="/"]',
                    'div[class*="card"] a[href*="/real-estate-agents/"]'
                ]
                
                for selector in selectors:
                    try:
                        elements = await page.locator(selector).all()
                        for element in elements:
                            try:
                                href = await element.get_attribute('href')
                                if href and ('/real-estate-agents/' in href or '/profile/' in href):
                                    if not href.startswith('http'):
                                        href = f"https://www.homes.com{href}"
                                    if not any(skip in href for skip in ['/search/', '/office/', '/company/', '/listings/']):
                                        profile_links.add(href)
                            except:
                                continue
                    except Exception as e:
                        print(f"Error with selector {selector}: {e}")
                        continue
                
                page_profile_links = list(profile_links)
                print(f"Found {len(page_profile_links)} agent profiles on page {page_num}")
                
                if not page_profile_links:
                    print("No profiles found on this page, stopping pagination")
                    break
                
                all_profile_links.extend(page_profile_links)
                
                # Check if we have enough profiles
                if len(all_profile_links) >= max_profiles:
                    all_profile_links = all_profile_links[:max_profiles]
                    break
                
                # Look for next page link
                next_page_url = None
                pagination_selectors = [
                    'a[aria-label="Next page"]',
                    'a.next-page',
                    'a[rel="next"]',
                    '.pagination a:has-text("Next")',
                    '.pagination a:has-text(">")',
                    'a[title="Next"]',
                    'nav[aria-label="pagination"] a[aria-label*="next"]',
                    '.page-numbers a.next',
                    'a:has-text("Next")',
                    '[class*="pagination"] a[href*="page="]'
                ]
                
                for selector in pagination_selectors:
                    try:
                        next_elem = await page.locator(selector).first
                        if await next_elem.count() > 0:
                            href = await next_elem.get_attribute('href')
                            if href:
                                if not href.startswith('http'):
                                    # Make absolute URL
                                    base_url = page.url.split('?')[0].rsplit('/', 1)[0]
                                    next_page_url = f"{base_url}/{href}" if not href.startswith('/') else f"https://www.homes.com{href}"
                                else:
                                    next_page_url = href
                                break
                    except:
                        continue
                
                if next_page_url and next_page_url != current_url:
                    current_url = next_page_url
                    page_num += 1
                else:
                    print("No next page found or same URL, stopping pagination")
                    break
                    
            except Exception as e:
                print(f"Error during list scraping: {e}")
                break
            finally:
                if browser:
                    await browser.close()
            
            # Small delay between pages
            if len(all_profile_links) < max_profiles:
                await asyncio.sleep(2)
        
        print(f"\nTotal profiles found across all pages: {len(all_profile_links)}")
        return all_profile_links
    
    async def scrape_agent_profile(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual agent profile"""
        browser = None
        try:
            browser, page = await self.connect_to_brightdata()
            
            print(f"Scraping profile: {profile_url}")
            await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            await self.human_delay(1000, 2000)
            
            data = {"profile_url": profile_url, "source": "homes.com"}
            
            # Extract name
            name_selectors = ['h1.agent-name', 'h1[data-testid="agent-name"]', '.agent-detail-name h1', 'h1']
            for selector in name_selectors:
                try:
                    elem = await page.locator(selector).first
                    if await elem.count() > 0:
                        full_name = await elem.inner_text()
                        parts = full_name.strip().split(' ', 1)
                        data['first_name'] = parts[0] if parts else None
                        data['last_name'] = parts[1] if len(parts) > 1 else None
                        break
                except:
                    continue
            
            # Extract company
            company_selectors = ['.brokerage-name', '[data-testid="agent-brokerage"]', '.agent-company']
            for selector in company_selectors:
                try:
                    elem = await page.locator(selector).first
                    if await elem.count() > 0:
                        data['company'] = (await elem.inner_text()).strip()
                        break
                except:
                    continue
            
            # Extract location
            location_selectors = ['.agent-location', '[data-testid="agent-location"]', '.agent-address']
            for selector in location_selectors:
                try:
                    elem = await page.locator(selector).first
                    if await elem.count() > 0:
                        location_text = (await elem.inner_text()).strip()
                        parts = location_text.split(',')
                        data['city'] = parts[0].strip() if parts else None
                        data['state'] = parts[1].strip() if len(parts) > 1 else None
                        break
                except:
                    continue
            
            # Extract phone (might need to click to reveal)
            phone_selectors = ['a[href^="tel:"]', 'button:has-text("Call")', '[data-testid*="phone"]']
            for selector in phone_selectors:
                try:
                    elem = await page.locator(selector).first
                    if await elem.count() > 0:
                        # Try to click if it's a button
                        if 'button' in selector:
                            await elem.click()
                            await self.human_delay(500, 1000)
                            # Look for revealed phone
                            phone_elem = await page.locator('a[href^="tel:"]').first
                            if await phone_elem.count() > 0:
                                href = await phone_elem.get_attribute('href')
                                data['cell_phone'] = href.replace('tel:', '') if href else None
                        else:
                            href = await elem.get_attribute('href')
                            if href and href.startswith('tel:'):
                                data['cell_phone'] = href.replace('tel:', '')
                            else:
                                data['cell_phone'] = (await elem.inner_text()).strip()
                        break
                except:
                    continue
            
            # Extract email
            try:
                email_elem = await page.locator('a[href^="mailto:"]').first
                if await email_elem.count() > 0:
                    href = await email_elem.get_attribute('href')
                    data['email'] = href.replace('mailto:', '') if href else None
            except:
                pass
            
            # Extract experience years
            exp_selectors = [':has-text("Years Experience")', ':has-text("years of experience")']
            for selector in exp_selectors:
                try:
                    elem = await page.locator(selector).first
                    if await elem.count() > 0:
                        text = await elem.inner_text()
                        import re
                        years = re.search(r'(\d+)', text)
                        if years:
                            data['years_exp'] = int(years.group(1))
                        break
                except:
                    continue
            
            # Set defaults
            data.setdefault('dma', None)
            data.setdefault('fb_or_website', profile_url)
            
            return data
            
        except Exception as e:
            print(f"Error scraping profile {profile_url}: {e}")
            return None
        finally:
            if browser:
                await browser.close()


async def scrape_with_brightdata(list_url: str, max_profiles: int = 10, batch_callback=None) -> List[Dict[str, Any]]:
    """Main entry point for Bright Data scraping with pagination and batch support"""
    scraper = BrightDataScraper()
    
    # Get profile URLs from all pages
    profile_urls = await scraper.scrape_homes_list_with_pagination(list_url, max_profiles)
    
    if not profile_urls:
        print("No profiles found on list page")
        return []
    
    # Scrape individual profiles
    results = []
    batch_data = []
    BATCH_SIZE = 50
    
    for i, url in enumerate(profile_urls):
        print(f"\nScraping profile {i+1}/{len(profile_urls)}")
        profile_data = await scraper.scrape_agent_profile(url)
        if profile_data:
            results.append(profile_data)
            batch_data.append(profile_data)
            
            # Call batch callback when we have BATCH_SIZE profiles
            if batch_callback and len(batch_data) >= BATCH_SIZE:
                batch_callback(batch_data)
                batch_data = []
                print(f"  ✓ Batch of {BATCH_SIZE} profiles saved")
        
        # Add delay between profiles
        if i < len(profile_urls) - 1:
            await asyncio.sleep(random.uniform(2, 4))
    
    # Don't forget remaining batch data
    if batch_callback and batch_data:
        batch_callback(batch_data)
        print(f"  ✓ Final batch of {len(batch_data)} profiles saved")
    
    return results


# Synchronous wrapper
def scrape_homes_brightdata(list_url: str, max_profiles: int = 10, batch_callback=None) -> List[Dict[str, Any]]:
    """Synchronous wrapper for Bright Data scraping"""
    return asyncio.run(scrape_with_brightdata(list_url, max_profiles, batch_callback))


if __name__ == "__main__":
    # Test the scraper
    url = "https://www.homes.com/real-estate-agents/pittsburgh-pa/"
    results = scrape_homes_brightdata(url, max_profiles=5)
    print(f"\n=== Scraped {len(results)} profiles ===")
    for r in results:
        print(f"- {r.get('first_name')} {r.get('last_name')} at {r.get('company')} ({r.get('city')}, {r.get('state')})") 