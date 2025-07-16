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
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"\n[BRIGHTDATA CONNECTION] Starting connection process...")
            logger.info(f"[BRIGHTDATA CONNECTION] Endpoint: {self.ws_endpoint[:50]}...")
            
            playwright = await async_playwright().start()
            logger.info("[BRIGHTDATA CONNECTION] Playwright started successfully")
            
            logger.info(f"[BRIGHTDATA CONNECTION] Connecting to Bright Data Browser API...")
            print(f"[BRIGHTDATA CONNECTION] Connecting to: {self.ws_endpoint[:50]}...")
            
            # Connect to the remote browser instance with timeout
            browser = await playwright.chromium.connect_over_cdp(
                self.ws_endpoint,
                timeout=60000  # 60 second timeout
            )
            
            logger.info("[BRIGHTDATA CONNECTION] ✓ Successfully connected to Bright Data browser")
            print("[BRIGHTDATA CONNECTION] ✓ Successfully connected")
            
            # Get the existing context (Bright Data manages this)
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                logger.info(f"[BRIGHTDATA CONNECTION] Using existing context with {len(context.pages)} pages")
            else:
                context = await browser.new_context()
                logger.info("[BRIGHTDATA CONNECTION] Created new browser context")
            
            # Get or create a page
            pages = context.pages
            if pages:
                page = pages[0]
                logger.info("[BRIGHTDATA CONNECTION] Using existing page")
            else:
                page = await context.new_page()
                logger.info("[BRIGHTDATA CONNECTION] Created new page")
                
            logger.info("[BRIGHTDATA CONNECTION] ✓ Connection complete")
            return browser, page
            
        except Exception as e:
            logger.error(f"[BRIGHTDATA CONNECTION] ✗ Failed to connect: {str(e)}")
            logger.error(f"[BRIGHTDATA CONNECTION] Error type: {type(e).__name__}")
            logger.error(f"[BRIGHTDATA CONNECTION] Full endpoint: {self.ws_endpoint}")
            
            # Check if it's an authentication error
            if "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error("[BRIGHTDATA CONNECTION] Authentication failed - check credentials")
            elif "timeout" in str(e).lower():
                logger.error("[BRIGHTDATA CONNECTION] Connection timed out - check network/proxy")
            
            print(f"[BRIGHTDATA CONNECTION] ✗ Failed: {str(e)}")
            raise
    
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
        import logging
        logger = logging.getLogger(__name__)
        
        all_profile_urls = []
        current_url = list_url
        
        # Parse the starting URL to determine pagination pattern
        import re
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed_url = urlparse(list_url)
        query_params = parse_qs(parsed_url.query)
        
        # Check if URL already has page number (e.g., /p2/)
        page_match = re.search(r'/p(\d+)/', list_url)
        if page_match:
            start_page = int(page_match.group(1))
        else:
            start_page = 1
            
        logger.info(f"\n{'='*80}")
        logger.info(f"STARTING PAGINATION SCRAPER")
        logger.info(f"Initial URL: {list_url}")
        logger.info(f"Starting from page: {start_page}")
        logger.info(f"Max profiles to collect: {max_profiles}")
        logger.info(f"{'='*80}\n")
        
        # Scrape up to 13 pages
        MAX_PAGES = 13
        
        for page_num in range(start_page, start_page + MAX_PAGES):
            if len(all_profile_urls) >= max_profiles:
                logger.info(f"Reached max profiles limit ({max_profiles}), stopping pagination")
                break
                
            # Construct page URL
            if page_num == 1 and start_page == 1:
                # First page might not have /p1/
                current_url = list_url
            else:
                # Replace or add page number in URL
                if '/p' in parsed_url.path:
                    # Replace existing page number
                    new_path = re.sub(r'/p\d+/', f'/p{page_num}/', parsed_url.path)
                else:
                    # Add page number before query string
                    path_parts = parsed_url.path.rstrip('/').split('/')
                    path_parts.append(f'p{page_num}')
                    new_path = '/'.join(path_parts) + '/'
                
                # Reconstruct URL with new path
                current_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    new_path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment
                ))
            
            logger.info(f"\n{'='*80}")
            logger.info(f"SCRAPING PAGE {page_num} of {start_page + MAX_PAGES - 1}")
            logger.info(f"URL: {current_url}")
            logger.info(f"Profiles collected so far: {len(all_profile_urls)}")
            logger.info(f"{'='*80}")
            
            browser = None
            
            try:
                browser, page = await self.connect_to_brightdata()
                
                logger.info(f"[Page {page_num}] Navigating to URL...")
                await page.goto(current_url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for content
                logger.info(f"[Page {page_num}] Waiting for page to load...")
                try:
                    await page.wait_for_selector('.agent-card, .realtor-card, a[href*="/real-estate-agents/"]', timeout=15000)
                    logger.info(f"[Page {page_num}] Found agent elements")
                except:
                    logger.warning(f"[Page {page_num}] Could not find expected agent selectors, continuing anyway...")
                
                # Human-like delay
                delay = random.uniform(2, 4)
                logger.info(f"[Page {page_num}] Waiting {delay:.1f} seconds...")
                await asyncio.sleep(delay)
                
                # Scroll to load all content
                logger.info(f"[Page {page_num}] Scrolling to load more results...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4})")
                    await asyncio.sleep(random.uniform(1, 2))
                
                # Debug info
                title = await page.title()
                final_url = page.url
                logger.info(f"[Page {page_num}] Page loaded - Title: {title}")
                logger.info(f"[Page {page_num}] Final URL: {final_url}")
                
                # Extract agent profile links with extensive logging
                page_profile_links = await page.evaluate("""
                    () => {
                        const links = [];
                        const debugInfo = {found: 0, checked: 0};
                        
                        // Try multiple selectors
                        const selectors = [
                            'a[href*="/real-estate-agents/"]',
                            'a[href*="/agent/"]',
                            '.agent-card a',
                            '.realtor-card a',
                            'a.agent-name',
                            '[class*="agent"] a'
                        ];
                        
                        selectors.forEach(selector => {
                            const elements = document.querySelectorAll(selector);
                            debugInfo.checked += elements.length;
                            
                            elements.forEach(link => {
                                const href = link.href || link.getAttribute('href');
                                if (href && (href.includes('/real-estate-agents/') || href.includes('/agent/'))) {
                                    // Skip non-profile URLs
                                    if (!href.includes('/search/') && !href.includes('/office/') && 
                                        !href.includes('/company/') && !href.includes('/listings/')) {
                                        const fullUrl = href.startsWith('http') ? href : 'https://www.homes.com' + href;
                                        links.push(fullUrl);
                                        debugInfo.found++;
                                    }
                                }
                            });
                        });
                        
                        console.log('Debug info:', debugInfo);
                        return [...new Set(links)];
                    }
                """)
                
                logger.info(f"[Page {page_num}] Found {len(page_profile_links)} agent profiles")
                
                if not page_profile_links:
                    logger.warning(f"[Page {page_num}] NO PROFILES found on this page!")
                    
                    # Check for captcha or access issues
                    page_content = await page.content()
                    if "captcha" in page_content.lower():
                        logger.error(f"[Page {page_num}] CAPTCHA detected!")
                    elif "access denied" in page_content.lower():
                        logger.error(f"[Page {page_num}] ACCESS DENIED!")
                    
                    # Log a snippet of the page content for debugging
                    logger.debug(f"[Page {page_num}] Page content snippet: {page_content[:500]}...")
                
                # Filter out duplicates and add to collection
                new_profiles = [url for url in page_profile_links if url not in all_profile_urls]
                all_profile_urls.extend(new_profiles)
                
                logger.info(f"[Page {page_num}] Added {len(new_profiles)} NEW profiles")
                logger.info(f"[Page {page_num}] Total unique profiles: {len(all_profile_urls)}")
                
                # Log some sample URLs for verification
                if new_profiles:
                    logger.info(f"[Page {page_num}] Sample profile URLs:")
                    for i, url in enumerate(new_profiles[:3]):
                        logger.info(f"  {i+1}. {url}")
                
            except Exception as e:
                logger.error(f"[Page {page_num}] ERROR during scraping: {str(e)}")
                logger.error(f"[Page {page_num}] Error type: {type(e).__name__}")
                import traceback
                logger.error(f"[Page {page_num}] Traceback: {traceback.format_exc()}")
                
                # Continue to next page even if this one failed
                if page_num < start_page + MAX_PAGES - 1:
                    logger.info(f"[Page {page_num}] Continuing to next page despite error...")
                
            finally:
                if browser:
                    await browser.close()
            
            # Wait 20 seconds between pages as requested
            if page_num < start_page + MAX_PAGES - 1 and len(all_profile_urls) < max_profiles:
                wait_time = 20
                logger.info(f"\n[PAGINATION] Waiting {wait_time} seconds before next page...")
                logger.info(f"[PAGINATION] Next page will be: {page_num + 1}")
                await asyncio.sleep(wait_time)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"PAGINATION COMPLETE")
        logger.info(f"Total pages scraped: {page_num - start_page + 1}")
        logger.info(f"Total profiles found: {len(all_profile_urls)}")
        logger.info(f"{'='*80}\n")
        
        return all_profile_urls[:max_profiles]  # Ensure we don't exceed max
    
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
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"BRIGHT DATA SCRAPER STARTED")
    logger.info(f"Target URL: {list_url}")
    logger.info(f"Max profiles: {max_profiles}")
    logger.info(f"Batch callback: {'Yes' if batch_callback else 'No'}")
    logger.info(f"{'='*80}\n")
    
    scraper = BrightDataScraper()
    
    # Get profile URLs from all pages
    logger.info("PHASE 1: Collecting profile URLs from list pages...")
    profile_urls = await scraper.scrape_homes_list_with_pagination(list_url, max_profiles)
    
    if not profile_urls:
        logger.error("No profiles found on list pages!")
        return []
    
    logger.info(f"\nPHASE 2: Scraping individual profiles...")
    logger.info(f"Total profiles to scrape: {len(profile_urls)}")
    
    # Scrape individual profiles
    results = []
    batch_data = []
    BATCH_SIZE = 50
    
    for i, url in enumerate(profile_urls):
        logger.info(f"\n{'='*60}")
        logger.info(f"PROFILE {i+1} of {len(profile_urls)}")
        logger.info(f"URL: {url}")
        logger.info(f"Progress: {((i+1)/len(profile_urls)*100):.1f}%")
        logger.info(f"{'='*60}")
        
        try:
            profile_data = await scraper.scrape_agent_profile(url)
            if profile_data:
                logger.info(f"✓ Successfully scraped profile:")
                logger.info(f"  Name: {profile_data.get('first_name', 'Unknown')} {profile_data.get('last_name', 'Unknown')}")
                logger.info(f"  Company: {profile_data.get('company', 'N/A')}")
                logger.info(f"  Location: {profile_data.get('city', 'N/A')}, {profile_data.get('state', 'N/A')}")
                logger.info(f"  Phone: {profile_data.get('cell_phone', 'N/A')}")
                
                results.append(profile_data)
                batch_data.append(profile_data)
                
                # Call batch callback when we have BATCH_SIZE profiles
                if batch_callback and len(batch_data) >= BATCH_SIZE:
                    logger.info(f"\n[BATCH] Saving batch of {BATCH_SIZE} profiles...")
                    try:
                        batch_callback(batch_data)
                        logger.info(f"[BATCH] ✓ Batch saved successfully")
                    except Exception as e:
                        logger.error(f"[BATCH] ✗ Error saving batch: {str(e)}")
                    batch_data = []
            else:
                logger.warning(f"✗ Failed to extract data from profile")
        except Exception as e:
            logger.error(f"✗ ERROR scraping profile: {str(e)}")
            logger.error(f"  Error type: {type(e).__name__}")
            import traceback
            logger.error(f"  Traceback: {traceback.format_exc()}")
            continue
        
        # Wait 10 seconds between profiles as requested
        if i < len(profile_urls) - 1:
            wait_time = 10
            logger.info(f"\n[DELAY] Waiting {wait_time} seconds before next profile...")
            logger.info(f"[DELAY] Scraped so far: {len(results)} profiles")
            logger.info(f"[DELAY] Remaining: {len(profile_urls) - i - 1} profiles")
            await asyncio.sleep(wait_time)
    
    # Don't forget remaining batch data
    if batch_callback and batch_data:
        logger.info(f"\n[BATCH] Saving final batch of {len(batch_data)} profiles...")
        try:
            batch_callback(batch_data)
            logger.info(f"[BATCH] ✓ Final batch saved successfully")
        except Exception as e:
            logger.error(f"[BATCH] ✗ Error saving final batch: {str(e)}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"SCRAPING COMPLETE")
    logger.info(f"Total profiles scraped: {len(results)}")
    logger.info(f"Success rate: {(len(results)/len(profile_urls)*100):.1f}%")
    logger.info(f"{'='*80}\n")
    
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