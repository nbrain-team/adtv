from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Any
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Import Web Unlocker scraper as highest priority
try:
    from .web_unlocker_scraper import scrape_with_web_unlocker
    WEB_UNLOCKER_AVAILABLE = True
except ImportError:
    WEB_UNLOCKER_AVAILABLE = False
    print("Web Unlocker scraper not available")

# Import Bright Data scraper as second priority
try:
    from .brightdata_scraper import scrape_homes_brightdata
    BRIGHTDATA_AVAILABLE = True
except ImportError:
    BRIGHTDATA_AVAILABLE = False
    print("Bright Data scraper not available")

# Import the proxy scraper as third priority
try:
    from .proxy_scraper import scrape_with_proxy
    PROXY_SCRAPER_AVAILABLE = True
except ImportError:
    PROXY_SCRAPER_AVAILABLE = False
    print("Proxy scraper not available")

# Import the indirect navigation scraper as fourth priority
try:
    from .indirect_scraper import scrape_indirect
    INDIRECT_SCRAPER_AVAILABLE = True
except ImportError:
    INDIRECT_SCRAPER_AVAILABLE = False
    print("Indirect scraper not available")

# Import the new Playwright scraper
try:
    from .playwright_scraper import scrape_with_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available. Install with: pip install playwright && python -m playwright install chromium")

# Import the simple scraper as fallback
try:
    from .simple_scraper import scrape_with_simple
    SIMPLE_SCRAPER_AVAILABLE = True
except ImportError:
    SIMPLE_SCRAPER_AVAILABLE = False
    print("Simple scraper not available")

# Log scraper availability at module load
import logging
logger = logging.getLogger(__name__)
logger.info(f"Scraper availability - Web Unlocker: {WEB_UNLOCKER_AVAILABLE}, BrightData: {BRIGHTDATA_AVAILABLE}, Proxy: {PROXY_SCRAPER_AVAILABLE}, Indirect: {INDIRECT_SCRAPER_AVAILABLE}, Playwright: {PLAYWRIGHT_AVAILABLE}, Simple: {SIMPLE_SCRAPER_AVAILABLE}")

# --- Enhanced Scraping Configuration ---

# A list of common user-agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

def get_soup_with_selenium(url: str) -> Optional[BeautifulSoup]:
    """
    Fetches a URL using a headless Selenium-controlled Chrome browser
    and returns a BeautifulSoup object.
    Now configured to use Chrome/Chromedriver from Nix environment variables.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") # Required for running as root in a Docker container
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Check for chromedriver path - try multiple locations
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    
    if not chromedriver_path:
        # Try common locations on Render
        possible_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "/opt/render/project/src/chromedriver",
            os.path.expanduser("~/chromedriver")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                chromedriver_path = path
                break
    
    if not chromedriver_path:
        raise ValueError("Could not find chromedriver. Please ensure Chrome and chromedriver are installed.")
    
    chrome_bin_path = os.getenv("CHROME_BIN")
    if not chrome_bin_path:
        # Try common Chrome locations
        possible_chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
        
        for path in possible_chrome_paths:
            if os.path.exists(path):
                chrome_bin_path = path
                break
    
    if chrome_bin_path:
        chrome_options.binary_location = chrome_bin_path

    service = Service(executable_path=chromedriver_path)

    # The webdriver manager is not used here to avoid issues in Render's environment.
    # The build script ensures Chrome is installed system-wide.
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        # Wait for dynamic content to load. Adjust time as needed.
        time.sleep(5) 
        page_source = driver.page_source
        return BeautifulSoup(page_source, 'lxml')
    except Exception as e:
        print(f"Error fetching {url} with Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def scrape_realtor_list_page(list_url: str) -> List[str]:
    """
    Scrapes a homes.com list page to find all individual realtor profile links.
    NOTE: These selectors are based on anticipated page structure and may need adjustment.
    """
    print(f"Attempting to scrape list page with Selenium: {list_url}")
    soup = get_soup_with_selenium(list_url)
    if not soup:
        print("Failed to get page soup with Selenium.")
        return []

    profile_links = set()
    # This selector targets links within a common agent card structure.
    # Updated selector to be more specific to what has been observed on homes.com sites.
    for a_tag in soup.select('.agent-card-details-container a, a.for-sale-card-link, .agent-card a, a.agent-name'):
        href = a_tag.get('href')
        if href and ('/real-estate-agents/' in href or '/agent/' in href):
            # Ensure we construct an absolute URL
            if not href.startswith('http'):
                href = f"https://www.homes.com{href}"
            profile_links.add(href)
    
    print(f"Found {len(profile_links)} profile links.")
    return list(profile_links)


def clean_text(text: Optional[str]) -> Optional[str]:
    """Helper to clean and strip text content."""
    return text.strip() if text else None

def parse_numeric(text: Optional[str]) -> Optional[int]:
    """Helper to parse numeric values from text, removing symbols."""
    if not text:
        return None
    return int(re.sub(r'[^\d]', '', text))


def scrape_realtor_profile_page(profile_url: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes a single realtor profile page for their details.
    NOTE: These selectors are based on anticipated page structure and may need adjustment.
    """
    soup = get_soup_with_selenium(profile_url)
    if not soup:
        return None

    # Helper to find text by a label and return the next sibling's text
    def get_value_by_label(label_text: str) -> Optional[str]:
        label_element = soup.find(lambda tag: tag.name in ['dt', 'span', 'div'] and label_text in tag.get_text())
        if label_element:
            value_element = label_element.find_next_sibling()
            if value_element:
                return clean_text(value_element.get_text())
        return None

    data = {
        "profile_url": profile_url
    }

    # --- Basic Info ---
    # These selectors are broad and will likely need refinement.
    name_element = soup.select_one('h1[data-testid="agent-name"], .agent-name')
    data['first_name'] = clean_text(name_element.get_text().split(' ')[0]) if name_element else None
    data['last_name'] = clean_text(' '.join(name_element.get_text().split(' ')[1:])) if name_element else None
    
    company_element = soup.select_one('[data-testid="agent-brokerage"], .brokerage-name')
    data['company'] = clean_text(company_element.get_text()) if company_element else None

    location_element = soup.select_one('[data-testid="agent-location"], .agent-location')
    if location_element:
        location_text = location_element.get_text() # e.g., "Chicago, IL"
        parts = location_text.split(',')
        data['city'] = clean_text(parts[0]) if len(parts) > 0 else None
        data['state'] = clean_text(parts[1]) if len(parts) > 1 else None

    # --- Contact Info ---
    # This is often obfuscated. These selectors are optimistic.
    data['cell_phone'] = get_value_by_label("Cell")
    data['email'] = clean_text(soup.select_one('a[href^="mailto:"]'))
    
    # --- Professional Info ---
    data['years_exp'] = parse_numeric(get_value_by_label("Years of Experience"))
    
    fb_link = soup.select_one('a[href*="facebook.com"]')
    data['fb_or_website'] = fb_link['href'] if fb_link else profile_url # Default to profile URL if no other site found

    # --- Sales Data ---
    # This data is often in tables or specific stat blocks.
    def get_deals_value(deal_type: str, metric: str) -> Optional[str]:
        # Example: Looks for a div with text "For Sale" then finds a sibling with "Total deals"
        header = soup.find(lambda tag: tag.name in ['h2', 'h3'] and deal_type in tag.get_text())
        if header:
            metric_element = header.find_next(lambda tag: tag.name in ['span', 'div'] and metric in tag.get_text())
            if metric_element and metric_element.find_next_sibling():
                return clean_text(metric_element.find_next_sibling().get_text())
        return None

    data['seller_deals_total_deals'] = parse_numeric(get_deals_value("For Sale", "Total deals"))
    data['seller_deals_total_value'] = parse_numeric(get_deals_value("For Sale", "Total value"))
    data['seller_deals_avg_price'] = parse_numeric(get_deals_value("For Sale", "Avg. sale price"))
    
    data['buyer_deals_total_deals'] = parse_numeric(get_deals_value("For Rent", "Total deals")) # Assuming buyer deals are 'for rent', may need to be 'Sold'
    data['buyer_deals_total_value'] = parse_numeric(get_deals_value("For Rent", "Total value"))
    data['buyer_deals_avg_price'] = parse_numeric(get_deals_value("For Rent", "Avg. sale price"))

    # Add missing fields from user spec as None
    data.setdefault('dma', None)
    data.setdefault('source', "homes.com")

    return data


def scrape_realtor_list_with_playwright(list_url: str, max_profiles: int = 10, use_google_search: bool = True, batch_callback=None) -> List[Dict[str, Any]]:
    """
    Alternative scraping method using Playwright for better bot detection evasion.
    Tries Web Unlocker first, then Bright Data, then proxy, then other methods.
    
    Args:
        list_url: The URL to scrape
        max_profiles: Maximum number of profiles to scrape
        use_google_search: Whether to use Google search for additional info
        batch_callback: Optional callback function to call with batches of results
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"REALTOR SCRAPER - STARTING")
    logger.info(f"URL: {list_url}")
    logger.info(f"Max profiles: {max_profiles}")
    logger.info(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*80}\n")
    
    # Log environment status
    logger.info("ENVIRONMENT CHECK:")
    logger.info(f"  Bright Data Browser Available: {BRIGHTDATA_AVAILABLE}")
    logger.info(f"  Bright Data Browser URL: {'Yes' if os.getenv('BRIGHTDATA_BROWSER_URL') else 'No'}")
    logger.info(f"  Web Unlocker Available: {WEB_UNLOCKER_AVAILABLE}")
    logger.info(f"  API Token: {'Yes' if os.getenv('BRIGHTDATA_API_TOKEN') else 'No'}")
    logger.info(f"  Proxy Available: {PROXY_SCRAPER_AVAILABLE}")
    logger.info(f"  Residential Proxy URL: {'Yes' if os.getenv('RESIDENTIAL_PROXY_URL') else 'No'}")
    logger.info("")
    
    # Try Bright Data Browser API FIRST (since we have credentials)
    if BRIGHTDATA_AVAILABLE:
        logger.info("ATTEMPTING: Bright Data Browser API (Priority 1)")
        # Get the endpoint from environment or use default
        brightdata_url = os.getenv('BRIGHTDATA_BROWSER_URL', 
            'wss://brd-customer-hl_6f2331cd-zone-homes_scraper:o47ipk4as8nq@brd.superproxy.io:9222')
        logger.info(f"  Endpoint: {brightdata_url[:50]}...")
        
        try:
            logger.info("  Calling scrape_homes_brightdata...")
            result = scrape_homes_brightdata(list_url, max_profiles, batch_callback=batch_callback)
            logger.info(f"  ✓ SUCCESS: Scraped {len(result)} profiles")
            return result
        except Exception as e:
            logger.error(f"  ✗ FAILED: {str(e)}")
            logger.error(f"  Error type: {type(e).__name__}")
            import traceback
            logger.error(f"  Traceback:\n{traceback.format_exc()}")
            logger.info("  Moving to next scraper...")
    else:
        logger.error("  ✗ Bright Data Browser not available - Import failed")
    
    # Try Web Unlocker second
    if WEB_UNLOCKER_AVAILABLE and os.getenv('BRIGHTDATA_API_TOKEN'):
        logger.info("\nATTEMPTING: Bright Data Web Unlocker API (Priority 2)")
        logger.info(f"  API Token present: Yes")
        try:
            logger.info("  Calling scrape_with_web_unlocker...")
            result = scrape_with_web_unlocker(list_url, max_profiles, use_google_search=use_google_search, batch_callback=batch_callback)
            logger.info(f"  ✓ SUCCESS: Scraped {len(result)} profiles")
            return result
        except Exception as e:
            logger.error(f"  ✗ FAILED: {e}")
            logger.info("  Moving to next scraper...")
    else:
        logger.info("\n  ✗ Web Unlocker not available or no API token")
    
    # Try proxy scraper if available and configured
    if PROXY_SCRAPER_AVAILABLE and os.getenv('RESIDENTIAL_PROXY_URL'):
        logger.info("\nATTEMPTING: Proxy scraper (Priority 3)")
        try:
            logger.info("  Calling scrape_with_proxy...")
            result = scrape_with_proxy(list_url, max_profiles, batch_callback=batch_callback)
            logger.info(f"  ✓ SUCCESS: Scraped {len(result)} profiles")
            return result
        except Exception as e:
            logger.error(f"  ✗ FAILED: {e}")
            logger.info("  Moving to next scraper...")
    else:
        logger.info("\n  ✗ Proxy scraper not available or not configured")
    
    # Log failure state
    logger.error("\n" + "="*80)
    logger.error("ALL PRIORITY SCRAPERS FAILED!")
    logger.error("Falling back to less reliable methods...")
    logger.error("="*80 + "\n")
    
    # Try indirect navigation (most likely to succeed without proxy)
    if INDIRECT_SCRAPER_AVAILABLE:
        logger.info("ATTEMPTING: Indirect navigation scraper (Fallback 1)")
        try:
            result = scrape_indirect(list_url, max_profiles, batch_callback=batch_callback)
            logger.info(f"  ✓ SUCCESS: Scraped {len(result)} profiles")
            return result
        except Exception as e:
            logger.error(f"  ✗ FAILED: {e}")
    
    # Try direct Playwright scraper
    if PLAYWRIGHT_AVAILABLE:
        logger.info("\nATTEMPTING: Direct Playwright scraper (Fallback 2)")
        try:
            result = scrape_with_playwright(list_url, max_profiles, batch_callback=batch_callback)
            logger.info(f"  ✓ SUCCESS: Scraped {len(result)} profiles")
            return result
        except Exception as e:
            logger.error(f"  ✗ FAILED: {e}")
    
    # Try Selenium
    logger.info("\nATTEMPTING: Selenium scraper (Fallback 3)")
    try:
        profile_links = scrape_realtor_list_page(list_url)
        scraped_data = []
        batch_data = []
        BATCH_SIZE = 50
        
        for i, profile_url in enumerate(profile_links[:max_profiles]):
            logger.info(f"  Scraping profile {i+1}/{min(len(profile_links), max_profiles)}: {profile_url}")
            profile_data = scrape_realtor_profile_page(profile_url)
            if profile_data:
                scraped_data.append(profile_data)
                batch_data.append(profile_data)
                
                # Call batch callback every BATCH_SIZE profiles
                if batch_callback and len(batch_data) >= BATCH_SIZE:
                    batch_callback(batch_data)
                    batch_data = []
            
            # Add delay between requests to avoid rate limiting
            if i < len(profile_links) - 1:
                time.sleep(2)
        
        # Don't forget remaining batch data
        if batch_callback and batch_data:
            batch_callback(batch_data)
        
        logger.info(f"  ✓ SUCCESS: Scraped {len(scraped_data)} profiles")
        return scraped_data
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        
        # Final fallback to simple scraper
        if SIMPLE_SCRAPER_AVAILABLE:
            logger.info("\nATTEMPTING: Simple requests-based scraper (Last resort)")
            try:
                result = scrape_with_simple(list_url, max_profiles, batch_callback=batch_callback)
                logger.info(f"  ✓ SUCCESS: Scraped {len(result)} profiles")
                return result
            except Exception as e:
                logger.error(f"  ✗ FAILED: {e}")
        
    logger.error("\n" + "="*80)
    logger.error("CRITICAL: ALL SCRAPING METHODS FAILED")
    logger.error("Please check:")
    logger.error("  1. Bright Data credentials are correct")
    logger.error("  2. Network connectivity")
    logger.error("  3. Target website is accessible")
    logger.error("="*80 + "\n")
    
    return [] 