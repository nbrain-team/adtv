"""
Web Unlocker scraper for Bright Data - handles anti-bot measures automatically
"""
import requests
from bs4 import BeautifulSoup
import os
import time
import logging
from typing import List, Dict, Optional, Any
import re
import json
from .agent_website_scraper import AgentWebsiteScraper
from .google_search_scraper import GoogleSearchScraper

# Set up logging
logger = logging.getLogger(__name__)

class WebUnlockerScraper:
    """Scraper using Bright Data's Web Unlocker API"""
    
    def __init__(self):
        # Get API token from environment or use default
        self.api_token = os.getenv('BRIGHTDATA_API_TOKEN')
        if not self.api_token:
            logger.error("BRIGHTDATA_API_TOKEN environment variable not set!")
            raise ValueError("BRIGHTDATA_API_TOKEN is required for Web Unlocker")
        
        self.zone = os.getenv('BRIGHTDATA_ZONE', 'homes_web_unlocker')
        
        # API endpoint
        self.api_url = "https://api.brightdata.com/request"
        
        # Headers for API requests
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page using Web Unlocker API"""
        try:
            logger.info(f"Fetching: {url}")
            
            # Prepare the request payload
            payload = {
                "zone": self.zone,
                "url": url,
                "format": "raw"
            }
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # Check response status
            if response.status_code == 200:
                logger.info(f"Successfully fetched {url}")
                return BeautifulSoup(response.content, 'html.parser')
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def scrape_agent_list(self, list_url: str) -> List[str]:
        """Scrape list of agent profile URLs"""
        soup = self.get_page(list_url)
        if not soup:
            logger.error("Failed to get page soup")
            return []
        
        logger.info(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
        profile_links = set()
        
        # Try multiple selectors for agent links
        selectors = [
            'a[href*="/real-estate-agents/"]',
            '.agent-card a',
            '.realtor-card a',
            'a.agent-name',
            '[class*="agent"] a',
            'div[class*="card"] a',
            # More specific homes.com selectors
            '.agent-list-card-title a',
            '.agent-card-content a',
            'h3.agent-name a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Selector '{selector}' found {len(elements)} elements")
            
            for elem in elements:
                href = elem.get('href')
                if href and ('/real-estate-agents/' in href or '/profile/' in href):
                    # Make absolute URL
                    if not href.startswith('http'):
                        href = f"https://www.homes.com{href}"
                    
                    # Filter out non-profile URLs
                    if not any(skip in href for skip in ['/search/', '/office/', '/company/', '/listings/']):
                        profile_links.add(href)
        
        # Debug: If no profiles found, print some page content
        if len(profile_links) == 0:
            logger.warning("No profiles found. Checking page content...")
            # Look for any links with real estate agent patterns
            all_links = soup.find_all('a', href=True)
            agent_pattern = re.compile(r'real.*estate.*agent|realtor|agent.*profile', re.I)
            for link in all_links[:20]:  # Check first 20 links
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if agent_pattern.search(href) or agent_pattern.search(text):
                    logger.info(f"  Potential agent link: {href} - {text[:50]}")
        
        logger.info(f"Found {len(profile_links)} unique agent profiles")
        return list(profile_links)
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and strip text content"""
        if not text:
            return None
        return ' '.join(text.strip().split())
    
    def parse_numeric(self, text: Optional[str]) -> Optional[int]:
        """Extract numeric value from text"""
        if not text:
            return None
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None
    
    def scrape_agent_profile(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Scrape individual agent profile"""
        soup = self.get_page(profile_url)
        if not soup:
            return None
        
        data = {
            "profile_url": profile_url,
            "source": "homes.com"
        }
        
        # Extract name
        name_selectors = [
            'h1.agent-name',
            'h1[class*="agent-name"]',
            '.agent-detail-name h1',
            'h1',
            '.profile-name',
            '[class*="name"] h1'
        ]
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                full_name = self.clean_text(name_elem.get_text())
                if full_name and not any(skip in full_name.lower() for skip in ['real estate', 'homes.com', 'find agent']):
                    parts = full_name.split(' ', 1)
                    data['first_name'] = parts[0]
                    data['last_name'] = parts[1] if len(parts) > 1 else None
                    break
        
        # Extract company/brokerage
        company_selectors = [
            '.brokerage-name',
            '[class*="brokerage"]',
            '[class*="company"]',
            '.agent-office',
            '.agent-broker',
            '.agent-brokerage-name',
            'div[data-testid="agent-brokerage"]',
            '.office-name',
            '.broker-name'
        ]
        company_found = False
        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                company_text = self.clean_text(company_elem.get_text())
                if company_text and not any(skip in company_text.lower() for skip in ['agent', 'realtor', 'profile']):
                    data['company'] = company_text
                    company_found = True
                    break
        
        # If no company found, try looking for text patterns
        if not company_found:
            # Look for patterns like "at Company Name" or "with Company Name"
            company_pattern = re.compile(r'(?:at|with|of)\s+([A-Z][^,\n]+?)(?:\s*[-,]|\s*$)', re.I)
            page_text = soup.get_text()
            company_match = company_pattern.search(page_text)
            if company_match:
                data['company'] = self.clean_text(company_match.group(1))
        
        # Extract location
        location_elem = soup.select_one('.agent-location, [class*="location"], [class*="address"], .agent-city-state')
        if location_elem:
            location_text = self.clean_text(location_elem.get_text())
            if location_text:
                parts = location_text.split(',')
                data['city'] = parts[0].strip() if parts else None
                data['state'] = parts[1].strip() if len(parts) > 1 else None
        
        # Extract phone
        phone_elem = soup.select_one('a[href^="tel:"]')
        if phone_elem:
            phone_href = phone_elem.get('href')
            if phone_href:
                data['cell_phone'] = phone_href.replace('tel:', '').strip()
        else:
            # Look for phone in text
            phone_pattern = re.compile(r'(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})')
            page_text = soup.get_text()
            phone_match = phone_pattern.search(page_text)
            if phone_match:
                data['cell_phone'] = '-'.join(phone_match.groups())
        
        # Extract email
        email_elem = soup.select_one('a[href^="mailto:"]')
        if email_elem:
            email_href = email_elem.get('href')
            if email_href:
                data['email'] = email_href.replace('mailto:', '').strip()
        
        # Extract Facebook profile from homes.com
        facebook_selectors = [
            'a.social-link[href*="facebook.com"]',
            'a.text-only.social-link[href*="facebook.com"]',
            'a[aria-label*="Facebook"]',
            'a[title*="Facebook"]',
            'a[href*="facebook.com"]',
            'a[href*="fb.com"]'
        ]
        
        facebook_found = False
        logger.info(f"  Looking for Facebook profile on homes.com...")
        
        for selector in facebook_selectors:
            facebook_elem = soup.select_one(selector)
            if facebook_elem:
                href = facebook_elem.get('href')
                if href and ('facebook.com' in href or 'fb.com' in href):
                    logger.info(f"    ✓ Found Facebook profile: {href}")
                    data['facebook_profile'] = href
                    facebook_found = True
                    break
        
        if not facebook_found:
            logger.info(f"    ✗ No Facebook profile found on homes.com")
        
        # Extract website link
        website_selectors = [
            'a.website-link[href]',
            'a.text-only.website-link[href]',
            'a[aria-label*="Agent Website"]',
            'a[title*="Agent Website"]',
            'a:contains("Agent Website")',
            'a:contains("Website")',
            'a[href*="kwcommercial.com"]',
            'a[href*="kw.com"]'
        ]
        
        website_found = False
        logger.info(f"  Looking for agent website...")
        
        for selector in website_selectors:
            # BeautifulSoup doesn't support :contains, so handle it differently
            if ':contains(' in selector:
                text_to_find = selector.split(':contains("')[1].split('")')[0]
                website_elems = soup.find_all('a', string=re.compile(text_to_find, re.I))
                logger.info(f"    Checking for links containing '{text_to_find}': found {len(website_elems)} elements")
                for elem in website_elems:
                    href = elem.get('href')
                    if href and href.startswith('http'):
                        logger.info(f"    ✓ Found agent website: {href}")
                        data['agent_website'] = href
                        website_found = True
                        break
            else:
                website_elem = soup.select_one(selector)
                if website_elem:
                    href = website_elem.get('href')
                    if href and href.startswith('http'):
                        logger.info(f"    ✓ Found agent website via {selector}: {href}")
                        data['agent_website'] = href
                        website_found = True
                        break
            
            if website_found:
                break
        
        if not website_found:
            logger.info(f"    ✗ No agent website found")
        
        # Extract years of experience
        exp_text = soup.find(text=re.compile(r'\d+\s*years?\s*(of\s*)?experience', re.I))
        if exp_text:
            years_match = re.search(r'(\d+)', exp_text)
            if years_match:
                data['years_exp'] = int(years_match.group(1))
        
        # Extract sales data if available
        stats_section = soup.find_all(text=re.compile(r'(deals?|transactions?|sales?)', re.I))
        for stat in stats_section:
            parent = stat.parent
            if parent:
                text = parent.get_text()
                # Look for total deals
                deals_match = re.search(r'(\d+)\s*(total\s*)?(deals?|transactions?)', text, re.I)
                if deals_match:
                    data['seller_deals_total_deals'] = int(deals_match.group(1))
                
                # Look for dollar amounts
                value_match = re.search(r'\$([0-9,]+)', text)
                if value_match:
                    value_str = value_match.group(1).replace(',', '')
                    data['seller_deals_total_value'] = int(value_str)
        
        # Set defaults
        data.setdefault('dma', None)
        data.setdefault('fb_or_website', profile_url)
        data.setdefault('years_exp', None)
        
        # Debug print extracted data
        logger.info(f"  Extracted data:")
        logger.info(f"    Name: {data.get('first_name')} {data.get('last_name')}")
        logger.info(f"    Company: {data.get('company')}")
        logger.info(f"    Location: {data.get('city')}, {data.get('state')}")
        logger.info(f"    Phone: {data.get('cell_phone')}")
        logger.info(f"    Email: {data.get('email')}")
        logger.info(f"    Agent Website: {data.get('agent_website')}")
        logger.info(f"    Facebook Profile: {data.get('facebook_profile')}")
        logger.info(f"    Seller Value: {data.get('seller_deals_total_value')}")
        
        return data


def scrape_with_web_unlocker(list_url: str, max_profiles: int = 10, use_google_search: bool = None, batch_callback=None) -> List[Dict[str, Any]]:
    """Main entry point for Web Unlocker scraping with pagination support"""
    logger.info("Using Bright Data Web Unlocker API...")
    scraper = WebUnlockerScraper()
    agent_scraper = AgentWebsiteScraper()  # Initialize Step 2 scraper
    
    # Check if Google search should be used (can be disabled via env var)
    if use_google_search is None:
        use_google_search = os.getenv('USE_GOOGLE_SEARCH', 'true').lower() == 'true'
    
    google_scraper = None
    if use_google_search:
        google_scraper = GoogleSearchScraper()  # Initialize Google search scraper
    
    all_profile_urls = []
    current_url = list_url
    page_num = 1
    max_pages = 20  # Safety limit to prevent infinite loops
    
    # Scrape multiple pages until we have enough profiles or no more pages
    while len(all_profile_urls) < max_profiles and page_num <= max_pages:
        logger.info(f"\nScraping page {page_num}: {current_url}")
        
        # Get agent profile URLs from current page
        profile_urls = scraper.scrape_agent_list(current_url)
        
        if not profile_urls:
            logger.warning(f"No profiles found on page {page_num}")
            break
        
        # Check for duplicates before adding
        new_profiles = [url for url in profile_urls if url not in all_profile_urls]
        if not new_profiles:
            logger.warning(f"All profiles on page {page_num} are duplicates, stopping pagination")
            break
            
        all_profile_urls.extend(new_profiles)
        logger.info(f"Found {len(profile_urls)} profiles on page {page_num} ({len(new_profiles)} new), total: {len(all_profile_urls)}")
        
        # Check if we have enough profiles
        if len(all_profile_urls) >= max_profiles:
            all_profile_urls = all_profile_urls[:max_profiles]
            logger.info(f"Reached max_profiles limit of {max_profiles}")
            break
        
        # Look for next page link
        soup = scraper.get_page(current_url)
        if soup:
            next_page_url = None
            
            # Try different pagination selectors
            pagination_selectors = [
                'a[aria-label="Next page"]',
                'a.next-page',
                'a[rel="next"]',
                '.pagination a:contains("Next")',
                '.pagination a:contains(">")',
                'a[title="Next"]',
                'nav[aria-label="pagination"] a[aria-label*="next"]',
                '.page-numbers a.next',
                # Add more homes.com specific selectors
                'a[href*="?page="]',
                'a.pagination-next',
                '.pagination-list a[aria-label*="next"]',
                'ul.pagination a[rel="next"]'
            ]
            
            logger.info("Looking for pagination links...")
            for selector in pagination_selectors:
                next_elem = soup.select_one(selector)
                if next_elem and next_elem.get('href'):
                    href = next_elem['href']
                    logger.info(f"Found next page link with selector '{selector}': {href}")
                    if not href.startswith('http'):
                        # Make absolute URL
                        from urllib.parse import urljoin
                        next_page_url = urljoin(current_url, href)
                    else:
                        next_page_url = href
                    logger.info(f"Next page URL: {next_page_url}")
                    break
            
            # Alternative: Look for numbered pagination
            if not next_page_url:
                logger.info("No 'Next' link found, trying numbered pagination...")
                # Try to find current page number and increment
                current_page_elem = soup.select_one('.pagination .active, .page-numbers .current, .pagination-list .is-current')
                if current_page_elem:
                    try:
                        current_page_num = int(current_page_elem.get_text().strip())
                        next_page_num = current_page_num + 1
                        logger.info(f"Current page: {current_page_num}, looking for page {next_page_num}")
                        
                        # Look for link with next page number
                        next_link = soup.select_one(f'.pagination a:contains("{next_page_num}"), .page-numbers a:contains("{next_page_num}")')
                        if next_link and next_link.get('href'):
                            href = next_link['href']
                            logger.info(f"Found page {next_page_num} link: {href}")
                            if not href.startswith('http'):
                                from urllib.parse import urljoin
                                next_page_url = urljoin(current_url, href)
                            else:
                                next_page_url = href
                        else:
                            logger.warning(f"Could not find link for page {next_page_num}")
                    except Exception as e:
                        logger.error(f"Error parsing page numbers: {e}")
                else:
                    logger.warning("Could not find current page number element")
                    
                # Last resort: check for page parameter in URL
                if not next_page_url:
                    logger.info("Trying URL parameter pagination...")
                    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                    parsed = urlparse(current_url)
                    query_params = parse_qs(parsed.query)
                    
                    # Check if there's a page parameter
                    current_page = int(query_params.get('page', ['1'])[0])
                    logger.info(f"Current page from URL: {current_page}")
                    
                    # Increment page
                    query_params['page'] = [str(current_page + 1)]
                    new_query = urlencode(query_params, doseq=True)
                    next_page_url = urlunparse(parsed._replace(query=new_query))
                    logger.info(f"Generated next page URL: {next_page_url}")
            
            if next_page_url:
                if next_page_url == current_url:
                    logger.warning("Next page URL is same as current URL, stopping pagination")
                    break
                current_url = next_page_url
                page_num += 1
                time.sleep(2)  # Be respectful between pages
            else:
                logger.warning("No next page found")
                break
        else:
            break
    
    # Log pagination summary
    if page_num > max_pages:
        logger.warning(f"Stopped pagination at max_pages limit ({max_pages})")
    elif len(all_profile_urls) >= max_profiles:
        logger.info(f"Stopped pagination after reaching {max_profiles} profiles")
    else:
        logger.info(f"Pagination ended naturally after {page_num} pages")
    
    logger.info(f"\nTotal profiles to scrape: {len(all_profile_urls)}")
    
    # Scrape individual profiles
    results = []
    batch_data = []
    BATCH_SIZE = 50
    
    for i, url in enumerate(all_profile_urls):
        logger.info(f"\nScraping profile {i+1}/{len(all_profile_urls)}: {url}")
        
        profile_data = scraper.scrape_agent_profile(url)
        if profile_data and (profile_data.get('first_name') or profile_data.get('last_name')):
            
            # Step 2 Option 1: Use Google Search (if enabled)
            if use_google_search:
                try:
                    logger.info(f"\nStep 2: Using Google search for additional contact info...")
                    google_results = google_scraper.search_agent_contact(profile_data)
                    
                    # Update with Google results if found
                    if google_results.get('google_email'):
                        profile_data['personal_email'] = google_results['google_email']
                    if google_results.get('google_phone'):
                        profile_data['phone2'] = google_results['google_phone']
                except Exception as e:
                    logger.error(f"  ✗ Google search failed: {str(e)}")
                    logger.info(f"  Continuing without Google search results...")
            
            # Step 2 Option 2: If agent website was found and Google didn't find everything
            if profile_data.get('agent_website') and (
                not profile_data.get('personal_email') or 
                not profile_data.get('phone2') or 
                not profile_data.get('facebook_profile')
            ):
                logger.info(f"\nStep 2b: Scraping agent website for additional data...")
                step2_data = agent_scraper.scrape_agent_website(profile_data['agent_website'])
                
                # Merge Step 2 data into profile data (only if not already found)
                if not profile_data.get('facebook_profile') and step2_data.get('facebook_profile'):
                    profile_data['facebook_profile'] = step2_data['facebook_profile']
                    logger.info(f"  ✓ Found Facebook profile on agent website: {step2_data['facebook_profile']}")
                
                # Only update if Google didn't find these
                if not profile_data.get('phone2') and step2_data.get('phone2'):
                    profile_data['phone2'] = step2_data.get('phone2')
                if not profile_data.get('personal_email') and step2_data.get('personal_email'):
                    profile_data['personal_email'] = step2_data.get('personal_email')
            
            results.append(profile_data)
            batch_data.append(profile_data)
            logger.info(f"  ✓ Scraped: {profile_data.get('first_name')} {profile_data.get('last_name')}")
            
            # Call batch callback when we have BATCH_SIZE profiles
            if batch_callback and len(batch_data) >= BATCH_SIZE:
                batch_callback(batch_data)
                batch_data = []
                logger.info(f"  ✓ Batch of {BATCH_SIZE} profiles saved")
        else:
            logger.warning(f"  ✗ Failed to extract data")
        
        # Be respectful with delays
        if i < len(all_profile_urls) - 1:
            time.sleep(2)
    
    # Don't forget remaining batch data
    if batch_callback and batch_data:
        batch_callback(batch_data)
        logger.info(f"  ✓ Final batch of {len(batch_data)} profiles saved")
    
    logger.info(f"\nCompleted: Scraped {len(results)} profiles successfully")
    return results


if __name__ == "__main__":
    # Test the scraper
    test_url = "https://www.homes.com/real-estate-agents/carlsbad-ca/"
    results = scrape_with_web_unlocker(test_url, max_profiles=5)
    
    logger.info("\n=== Results ===")
    for r in results:
        logger.info(f"{r.get('first_name')} {r.get('last_name')} - {r.get('company')} ({r.get('city')}, {r.get('state')})")
        if r.get('cell_phone'):
            logger.info(f"  Phone: {r.get('cell_phone')}")
        if r.get('email'):
            logger.info(f"  Email: {r.get('email')}") 