import asyncio
import os
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
import random
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BrightDataScraperFixed:
    """
    Fixed scraper that saves profiles immediately as they're found
    """
    
    def __init__(self):
        self.ws_endpoint = os.getenv('BRIGHTDATA_BROWSER_URL', 
            'wss://brd-customer-hl_6f2331cd-zone-homes_scraper:o47ipk4as8nq@brd.superproxy.io:9222')
        logger.info(f"Initialized BrightDataScraperFixed with endpoint: {self.ws_endpoint[:50]}...")
        
    async def connect_to_brightdata(self):
        """Connect to Bright Data browser instance"""
        try:
            playwright = await async_playwright().start()
            logger.info("[BRIGHTDATA CONNECTION] Playwright started successfully")
            
            browser = await playwright.chromium.connect_over_cdp(
                self.ws_endpoint,
                timeout=60000
            )
            
            logger.info("[BRIGHTDATA CONNECTION] ✓ Successfully connected to Bright Data browser")
            
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = await browser.new_context()
            
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
                
            return browser, page
            
        except Exception as e:
            logger.error(f"[BRIGHTDATA CONNECTION] Failed: {str(e)}")
            raise

    async def scrape_and_save_profiles(self, list_url: str, max_profiles: int = 700, batch_callback=None) -> int:
        """
        Scrape profiles and save them immediately as we find them
        Returns the total number of profiles saved
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"BRIGHT DATA SCRAPER FIXED - IMMEDIATE SAVE MODE")
        logger.info(f"Target URL: {list_url}")
        logger.info(f"Max profiles: {max_profiles}")
        logger.info(f"Batch callback: {'Yes' if batch_callback else 'No'}")
        logger.info(f"{'='*80}\n")
        
        total_saved = 0
        batch_data = []
        BATCH_SIZE = 20
        
        # Parse URL for pagination
        import re
        from urllib.parse import urlparse, parse_qs
        
        parsed_url = urlparse(list_url)
        page_match = re.search(r'/p(\d+)/', list_url)
        start_page = int(page_match.group(1)) if page_match else 1
        
        MAX_PAGES = 13
        
        for page_num in range(start_page, start_page + MAX_PAGES):
            if total_saved >= max_profiles:
                logger.info(f"Reached max profiles limit ({max_profiles}), stopping")
                break
                
            # Construct page URL
            if page_num == 1 and start_page == 1:
                current_url = list_url
            else:
                if '/p' in parsed_url.path:
                    new_path = re.sub(r'/p\d+/', f'/p{page_num}/', parsed_url.path)
                else:
                    path_parts = parsed_url.path.rstrip('/').split('/')
                    path_parts.append(f'p{page_num}')
                    new_path = '/'.join(path_parts) + '/'
                
                from urllib.parse import urlunparse
                current_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    new_path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment
                ))
            
            logger.info(f"\n{'='*80}")
            logger.info(f"SCRAPING PAGE {page_num}")
            logger.info(f"URL: {current_url}")
            logger.info(f"Profiles saved so far: {total_saved}")
            logger.info(f"{'='*80}")
            
            browser = None
            
            try:
                browser, page = await self.connect_to_brightdata()
                
                logger.info(f"[Page {page_num}] Navigating to URL...")
                await page.goto(current_url, wait_until='domcontentloaded', timeout=60000)
                
                await page.wait_for_selector('.agent-card, .realtor-card, a[href*="/real-estate-agents/"]', timeout=15000)
                
                # Human-like delay
                await asyncio.sleep(random.uniform(2, 4))
                
                # Scroll to load content
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4})")
                    await asyncio.sleep(random.uniform(1, 2))
                
                title = await page.title()
                logger.info(f"[Page {page_num}] Page loaded - Title: {title}")
                
                # Extract basic profile data directly from the list page
                profiles = await page.evaluate("""
                    () => {
                        const profiles = [];
                        
                        // Find all agent cards/links
                        const agentElements = document.querySelectorAll('.agent-card, .realtor-card, [class*="agent-list-item"]');
                        
                        agentElements.forEach(elem => {
                            const profile = {};
                            
                            // Get profile URL
                            const linkElem = elem.querySelector('a[href*="/real-estate-agents/"]') || elem.querySelector('a');
                            if (linkElem) {
                                const href = linkElem.getAttribute('href');
                                profile.profile_url = href.startsWith('http') ? href : 'https://www.homes.com' + href;
                            }
                            
                            // Get name
                            const nameElem = elem.querySelector('h2, h3, .agent-name, [class*="name"]');
                            if (nameElem) {
                                const fullName = nameElem.innerText.trim();
                                const parts = fullName.split(' ');
                                profile.first_name = parts[0] || '';
                                profile.last_name = parts.slice(1).join(' ') || '';
                            }
                            
                            // Get company
                            const companyElem = elem.querySelector('.agency-name, .brokerage-name, [class*="company"], [class*="brokerage"]');
                            if (companyElem) {
                                profile.company = companyElem.innerText.trim();
                            }
                            
                            // Get location
                            const locationElem = elem.querySelector('.location, [class*="location"], .agent-location');
                            if (locationElem) {
                                const locationText = locationElem.innerText.trim();
                                const match = locationText.match(/([^,]+),\\s*([A-Z]{2})/);
                                if (match) {
                                    profile.city = match[1].trim();
                                    profile.state = match[2].trim();
                                }
                            }
                            
                            // Get phone
                            const phoneElem = elem.querySelector('a[href^="tel:"], [class*="phone"]');
                            if (phoneElem) {
                                const phoneHref = phoneElem.getAttribute('href');
                                if (phoneHref && phoneHref.startsWith('tel:')) {
                                    profile.cell_phone = phoneHref.replace('tel:', '');
                                } else {
                                    const phoneText = phoneElem.innerText;
                                    const phoneMatch = phoneText.match(/\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}/);
                                    if (phoneMatch) {
                                        profile.cell_phone = phoneMatch[0];
                                    }
                                }
                            }
                            
                            // Only add if we have at least a profile URL
                            if (profile.profile_url) {
                                profile.source = 'homes.com';
                                profiles.push(profile);
                            }
                        });
                        
                        return profiles;
                    }
                """)
                
                logger.info(f"[Page {page_num}] Found {len(profiles)} agent profiles")
                
                # Add profiles to batch
                for profile in profiles:
                    if total_saved >= max_profiles:
                        break
                        
                    batch_data.append(profile)
                    total_saved += 1
                    
                    # Save batch when we reach BATCH_SIZE
                    if batch_callback and len(batch_data) >= BATCH_SIZE:
                        logger.info(f"\n[BATCH] Saving batch of {len(batch_data)} profiles...")
                        logger.info(f"[BATCH] Total saved so far: {total_saved}")
                        try:
                            batch_callback(batch_data)
                            logger.info(f"[BATCH] ✓ Batch saved successfully")
                        except Exception as e:
                            logger.error(f"[BATCH] ✗ Error saving batch: {str(e)}")
                        batch_data = []
                
                if not profiles:
                    logger.warning(f"[Page {page_num}] No profiles found, stopping pagination")
                    break
                    
            except Exception as e:
                logger.error(f"[Page {page_num}] ERROR: {str(e)}")
                
            finally:
                if browser:
                    await browser.close()
            
            # Wait between pages
            if page_num < start_page + MAX_PAGES - 1 and total_saved < max_profiles:
                wait_time = 20
                logger.info(f"\n[PAGINATION] Waiting {wait_time} seconds before next page...")
                await asyncio.sleep(wait_time)
        
        # Save any remaining profiles
        if batch_callback and batch_data:
            logger.info(f"\n[BATCH] Saving final batch of {len(batch_data)} profiles...")
            try:
                batch_callback(batch_data)
                logger.info(f"[BATCH] ✓ Final batch saved successfully")
            except Exception as e:
                logger.error(f"[BATCH] ✗ Error saving final batch: {str(e)}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"SCRAPING COMPLETE")
        logger.info(f"Total profiles saved: {total_saved}")
        logger.info(f"{'='*80}\n")
        
        return total_saved


# Main entry point
async def scrape_with_immediate_save(list_url: str, max_profiles: int = 700, batch_callback=None) -> int:
    """Scrape and save profiles immediately"""
    scraper = BrightDataScraperFixed()
    return await scraper.scrape_and_save_profiles(list_url, max_profiles, batch_callback)


def scrape_homes_brightdata_fixed(list_url: str, max_profiles: int = 700, batch_callback=None) -> List[Dict[str, Any]]:
    """
    Fixed synchronous wrapper that saves profiles immediately
    Returns empty list but saves profiles via callback
    """
    total_saved = asyncio.run(scrape_with_immediate_save(list_url, max_profiles, batch_callback))
    logger.info(f"Scraping complete. Total profiles saved: {total_saved}")
    return []  # Return empty list since profiles are saved via callback 