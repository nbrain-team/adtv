import asyncio
import os
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
import random
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BrightDataScraper:
    """
    Scraper that uses Bright Data's Browser API for maximum success
    """
    
    def __init__(self):
        # Get Bright Data credentials from environment
        # First try the environment variable, then fall back to the new endpoint
        self.ws_endpoint = os.getenv('BRIGHTDATA_BROWSER_URL', 
            'wss://brd-customer-hl_6f2331cd-zone-homes_scraper:o47ipk4as8nq@brd.superproxy.io:9222')
        
        logger.info(f"Initialized BrightDataScraper with endpoint: {self.ws_endpoint[:50]}...")
        
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
                    logger.info(f"[Page {page_num}] Page loaded, extracting links...")
                
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
                        
                        // Get all links
                        document.querySelectorAll('a').forEach(link => {
                            debugInfo.checked++;
                            const href = link.href || link.getAttribute('href');
                            
                            // Check if it's an agent profile link
                            if (href && href.includes('/real-estate-agents/')) {
                                // Make sure it's a profile, not a directory page
                                const parts = href.split('/');
                                const agentIndex = parts.indexOf('real-estate-agents');
                                
                                // Profile URLs have a name after 'real-estate-agents'
                                if (agentIndex >= 0 && parts.length > agentIndex + 1 && parts[agentIndex + 1]) {
                                    // Skip if it's just a location page (ends with state code)
                                    const lastPart = parts[parts.length - 1] || parts[parts.length - 2];
                                    // Check if it has an agent ID (usually alphanumeric)
                                    if (lastPart && 
                                        !lastPart.match(/^[a-z]{2}$/i) && 
                                        lastPart !== 'real-estate-agents' &&
                                        !lastPart.includes('-ca') &&
                                        !lastPart.includes('-il') &&
                                        !lastPart.includes('-ny') &&
                                        !lastPart.includes('-tx') &&
                                        !lastPart.includes('-fl') &&
                                        lastPart.length > 3) {
                                        const fullUrl = href.startsWith('http') ? href : 'https://www.homes.com' + href;
                                        // Double check it's not the same as the current page
                                        if (fullUrl !== window.location.href && !fullUrl.endsWith('/real-estate-agents/')) {
                                            links.push(fullUrl);
                                            debugInfo.found++;
                                        }
                                    }
                                }
                            }
                        });
                        
                        console.log('Debug info:', debugInfo);
                        console.log('Sample URLs found:', links.slice(0, 3));
                        return [...new Set(links)]; // Remove duplicates
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
            await self.human_delay(2000, 3000)
            
            # Log page title to verify we're on the right page
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Check if we're on an error page or captcha
            page_text = await page.inner_text('body')
            if 'captcha' in page_text.lower() and ('solve' in page_text.lower() or 'verify' in page_text.lower()):
                logger.error("CAPTCHA detected on page!")
                return None
            elif 'access denied' in page_text.lower() and len(page_text) < 500:
                logger.error("Access denied on page!")
                return None
            elif '404' in await page.title() or 'not found' in await page.title():
                logger.error("Page not found (404)!")
                return None
            
            data = {"profile_url": profile_url, "source": "homes.com"}
            
            # Try to log the page HTML structure for debugging
            try:
                # Get all h1, h2, h3 tags to understand the page structure
                headings = await page.evaluate("""
                    () => {
                        const headings = [];
                        document.querySelectorAll('h1, h2, h3').forEach(h => {
                            headings.push({
                                tag: h.tagName,
                                text: h.innerText.substring(0, 50),
                                classes: h.className
                            });
                        });
                        return headings;
                    }
                """)
                logger.info(f"Page headings found: {headings[:5]}")  # Log first 5 headings
                
                # Also try to find any elements with 'agent' in the class
                agent_elements = await page.evaluate("""
                    () => {
                        const elements = [];
                        document.querySelectorAll('[class*="agent" i], [class*="realtor" i], [class*="profile" i]').forEach(el => {
                            if (elements.length < 10) {
                                elements.push({
                                    tag: el.tagName,
                                    classes: el.className,
                                    text: el.innerText ? el.innerText.substring(0, 30) : ''
                                });
                            }
                        });
                        return elements;
                    }
                """)
                logger.info(f"Agent-related elements: {agent_elements[:5]}")
            except Exception as e:
                logger.error(f"Error getting page structure: {e}")
            
            # Extract name - try multiple selectors
            name_selectors = [
                'h1',  # Simple H1 - based on the test showing H1 contains name
                '.agent-info-name-and-icons',  # Found in analysis
                '.name-container',  # Found in analysis
                '.js-agent-name',  # Found in analysis
                'span.agent-name',  # Found in analysis
                '.agent-footer-name',  # Found in analysis
                'h1[data-testid="agent-name"]',
                'h1.agent-name', 
                'h1.AgentName',
                '.agent-details h1',
                '.agent-header h1',
                'h1[class*="agent"]',
                'h1[class*="name"]',
                '[data-testid*="name"] h1',
                '.profile-header h1',
                'main h1'
            ]
            
            name_found = False
            for selector in name_selectors:
                try:
                    elements = await page.locator(selector).all()
                    logger.info(f"Trying selector '{selector}' - found {len(elements)} elements")
                    
                    for elem in elements:
                        try:
                            full_name = (await elem.inner_text()).strip()
                            if full_name and not full_name.startswith('About') and not full_name.startswith('Transaction'):
                                logger.info(f"Found name with selector '{selector}': {full_name}")
                                parts = full_name.strip().split(' ', 1)
                                data['first_name'] = parts[0] if parts else None
                                data['last_name'] = parts[1] if len(parts) > 1 else None
                                name_found = True
                                break
                        except:
                            continue
                    
                    if name_found:
                        break
                except Exception as e:
                    logger.error(f"Error with selector {selector}: {e}")
                    continue
            
            if not name_found:
                logger.warning(f"Could not find agent name on {profile_url}")
            
            # Extract company - expanded selectors
            company_selectors = [
                '.agency-name',  # Found in analysis: "Ornate Inc"
                '.profile-column-left',  # This contained "Century" in the test
                '[data-testid="agent-brokerage"]',
                '.brokerage-name',
                '.agent-company',
                '.agent-brokerage',
                '[class*="brokerage"]',
                '[class*="company"]',
                '.agent-details .company',
                '.profile-company',
                'a[href*="/brokerages/"]',
                '.AgentBrokerage'
            ]
            
            company_found = False
            for selector in company_selectors:
                try:
                    if selector == '.agency-name':
                        # For agency-name, just get the first one
                        elem = page.locator(selector).first
                        if await elem.count() > 0:
                            company_text = (await elem.inner_text()).strip()
                            if company_text:
                                data['company'] = company_text
                                logger.info(f"Found company with selector '{selector}': {company_text}")
                                company_found = True
                                break
                    elif selector == '.profile-column-left':
                        # For profile-column-left, we need to extract just the company from the structure
                        elem = await page.locator(selector).first
                        if await elem.count() > 0:
                            # Look for agency-name within this element
                            agency_elem = await elem.locator('.agency-name').first
                            if await agency_elem.count() > 0:
                                company_text = (await agency_elem.inner_text()).strip()
                                if company_text:
                                    data['company'] = company_text
                                    logger.info(f"Found company within profile-column-left: {company_text}")
                                    company_found = True
                                    break
                    else:
                        # For other selectors, use the original logic
                        elements = await page.locator(selector).all()
                        for elem in elements:
                            try:
                                company_text = (await elem.inner_text()).strip()
                                if company_text and len(company_text) > 2:
                                    # Look for company keywords
                                    if any(keyword in company_text.lower() for keyword in ['century', 'remax', 'coldwell', 'realty', 'real estate', 'properties', 'group', 'llc', 'inc', 'corp', 'agency', 'brokers']):
                                        data['company'] = company_text
                                        logger.info(f"Found company with selector '{selector}': {company_text}")
                                        company_found = True
                                        break
                            except:
                                continue
                        
                        if company_found:
                            break
                except Exception as e:
                    logger.debug(f"Error with company selector {selector}: {e}")
                    continue
            
            if not company_found:
                logger.warning(f"Could not find company on {profile_url}")
            
            # Extract location - handle the specific div.location structure
            location_found = False
            
            # First try the specific structure with div.location containing city and state spans
            try:
                # Use wait_for to ensure element is ready
                location_elem = page.locator('div.location').first
                if await location_elem.count() > 0:
                    # Get the full text first
                    location_text = (await location_elem.inner_text()).strip()
                    logger.info(f"Found location div with text: {location_text}")
                    
                    # Try to get city from span.city
                    try:
                        city_elem = location_elem.locator('span.city').first
                        if await city_elem.count() > 0:
                            data['city'] = (await city_elem.inner_text()).strip()
                            logger.info(f"Found city: {data['city']}")
                    except:
                        pass
                    
                    # Try to get state from span.state
                    try:
                        state_elem = location_elem.locator('span.state').first
                        if await state_elem.count() > 0:
                            data['state'] = (await state_elem.inner_text()).strip()
                            logger.info(f"Found state: {data['state']}")
                    except:
                        pass
                    
                    # If spans didn't work, try parsing the text
                    if not data.get('city') and not data.get('state') and location_text:
                        # Text is like "Sacramento CA"
                        parts = location_text.rsplit(' ', 1)
                        if len(parts) == 2:
                            data['city'] = parts[0].strip()
                            data['state'] = parts[1].strip()
                            logger.info(f"Parsed location from text: {data['city']}, {data['state']}")
                    
                    if data.get('city') or data.get('state'):
                        location_found = True
            except Exception as e:
                logger.debug(f"Error extracting location from div.location: {e}")
            
            # If not found, try other selectors
            if not location_found:
                location_selectors = [
                    '.profile-column-left',
                    '[data-testid="agent-location"]',
                    '.agent-location',
                    '.agent-address',
                    '[class*="location"]',
                    '[class*="address"]',
                    '.agent-details .location',
                    '.profile-location',
                    '.AgentLocation',
                    'address'
                ]
                
                for selector in location_selectors:
                    try:
                        elem = await page.locator(selector).first
                        if await elem.count() > 0:
                            text = (await elem.inner_text()).strip()
                            if text and len(text) > 2:
                                # Look for city/state pattern in the text
                                import re
                                city_state_match = re.search(r'([A-Za-z\s]+?)\s+([A-Z]{2})(?:\s|$)', text)
                                if city_state_match:
                                    data['city'] = city_state_match.group(1).strip()
                                    data['state'] = city_state_match.group(2).strip()
                                    logger.info(f"Found location with selector '{selector}': {data['city']}, {data['state']}")
                                    location_found = True
                                    break
                    except Exception as e:
                        logger.debug(f"Error with location selector {selector}: {e}")
                        continue
            
            if not location_found:
                logger.warning(f"Could not find location on {profile_url}")
            
            # Extract phone - try multiple approaches
            phone_selectors = [
                'a.adp-phone-link',  # Found in analysis with tel: link
                'a[href^="tel:"]',
                '.cta-tablet-phone',  # Found in analysis
                '.agent-footer-phone',  # Found in analysis
                'button:has-text("Call")',
                '[data-testid*="phone"]',
                '[class*="phone"]',
                '.agent-phone',
                '.contact-phone'
            ]
            
            phone_found = False
            for selector in phone_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for elem in elements:
                        try:
                            # Check if it's a link with tel:
                            href = await elem.get_attribute('href')
                            if href and href.startswith('tel:'):
                                phone_number = href.replace('tel:', '').strip()
                                if phone_number:
                                    data['cell_phone'] = phone_number
                                    logger.info(f"Found phone with selector '{selector}': {phone_number}")
                                    phone_found = True
                                    break
                            
                            # If not a tel: link, check the text
                            text = await elem.inner_text()
                            if text and any(c.isdigit() for c in text):
                                # Check if it looks like a phone number
                                import re
                                phone_match = re.search(r'[\(\[]?(\d{3})[\)\]]?[-.\s]?(\d{3})[-.\s]?(\d{4})', text)
                                if phone_match:
                                    phone_number = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                                    data['cell_phone'] = phone_number
                                    logger.info(f"Found phone text with selector '{selector}': {phone_number}")
                                    phone_found = True
                                    break
                        except:
                            continue
                    
                    if phone_found:
                        break
                except Exception as e:
                    logger.debug(f"Error with phone selector {selector}: {e}")
                    continue
            
            if not phone_found:
                logger.warning(f"Could not find phone on {profile_url}")
            
            # Extract agent website
            website_found = False
            
            try:
                # Look for the specific website-link class
                website_elem = page.locator('a.website-link[href]').first
                if await website_elem.count() > 0:
                    website_url = await website_elem.get_attribute('href')
                    if website_url:
                        data['fb_or_website'] = website_url
                        website_found = True
                        logger.info(f"Found agent website: {website_url}")
                
                # If not found, try other website selectors
                if not website_found:
                    website_selectors = [
                        'a:has-text("Agent Website")',
                        'a[aria-label*="Website"]',
                        'a[title*="Website"]',
                        'a[href*="metrolistpro.com"]',  # Specific to some agents
                        'a[target="_blank"][rel*="noopener"]'
                    ]
                    
                    for selector in website_selectors:
                        try:
                            elem = await page.locator(selector).first
                            if await elem.count() > 0:
                                href = await elem.get_attribute('href')
                                # Make sure it's not a social media link or the homes.com profile
                                if href and not any(social in href for social in ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'homes.com']):
                                    data['fb_or_website'] = href
                                    website_found = True
                                    logger.info(f"Found agent website with selector '{selector}': {href}")
                                    break
                        except:
                            continue
            except Exception as e:
                logger.debug(f"Error extracting website: {e}")
            
            # Extract sales statistics
            try:
                stats_container = page.locator('div.stats-container').first
                if await stats_container.count() > 0:
                    # Extract all stat items
                    stat_items = await stats_container.locator('.stat-item').all()
                    
                    for item in stat_items:
                        try:
                            # Get the value (info-bold) and label (info-light)
                            value_elem = item.locator('.info-bold').first
                            label_elem = item.locator('.info-light').first
                            
                            if await value_elem.count() > 0 and await label_elem.count() > 0:
                                value = (await value_elem.inner_text()).strip()
                                label = (await label_elem.inner_text()).strip().lower()
                                
                                # Map the stats to data fields
                                if 'closed sales' in label:
                                    data['closed_sales'] = value
                                    logger.info(f"Found closed sales: {value}")
                                elif 'total value' in label:
                                    data['total_value'] = value
                                    logger.info(f"Found total value: {value}")
                                elif 'price range' in label:
                                    data['price_range'] = value
                                    logger.info(f"Found price range: {value}")
                                elif 'average price' in label:
                                    data['average_price'] = value
                                    logger.info(f"Found average price: {value}")
                        except:
                            continue
                            
                    logger.info(f"Successfully extracted sales statistics - closed_sales: {data.get('closed_sales')}, total_value: {data.get('total_value')}, price_range: {data.get('price_range')}, average_price: {data.get('average_price')}")
            except Exception as e:
                logger.debug(f"Error extracting sales statistics: {e}")
            
            # Set defaults for missing fields
            data.setdefault('dma', None)
            data.setdefault('fb_or_website', profile_url)
            
            # Log what we found
            logger.info(f"Extracted data summary:")
            logger.info(f"  Name: {data.get('first_name', 'None')} {data.get('last_name', 'None')}")
            logger.info(f"  Company: {data.get('company', 'None')}")
            logger.info(f"  Location: {data.get('city', 'None')}, {data.get('state', 'None')}")
            logger.info(f"  Phone: {data.get('cell_phone', 'None')}")
            logger.info(f"  Website: {data.get('fb_or_website', 'N/A')}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
                logger.info(f"  Website: {profile_data.get('fb_or_website', 'N/A')}")
                logger.info(f"  Sales Stats:")
                logger.info(f"    - Closed Sales: {profile_data.get('closed_sales', 'None')}")
                logger.info(f"    - Total Value: {profile_data.get('total_value', 'None')}")
                logger.info(f"    - Price Range: {profile_data.get('price_range', 'None')}")
                logger.info(f"    - Average Price: {profile_data.get('average_price', 'None')}")
                
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