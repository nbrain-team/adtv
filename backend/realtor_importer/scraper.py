from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Any
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Import the indirect navigation scraper as primary method
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


def scrape_realtor_list_with_playwright(list_url: str, max_profiles: int = 10) -> List[Dict[str, Any]]:
    """
    Alternative scraping method using Playwright for better bot detection evasion.
    Tries indirect navigation first, then falls back to other methods.
    """
    # Try indirect navigation first (most likely to succeed)
    if INDIRECT_SCRAPER_AVAILABLE:
        print("Using indirect navigation scraper (navigating from homepage)...")
        try:
            return scrape_indirect(list_url, max_profiles)
        except Exception as e:
            print(f"Indirect navigation scraper failed: {e}")
            print("Falling back to direct Playwright scraper...")
    
    # Try direct Playwright scraper
    if PLAYWRIGHT_AVAILABLE:
        print("Using Playwright scraper for better bot detection evasion...")
        try:
            return scrape_with_playwright(list_url, max_profiles)
        except Exception as e:
            print(f"Playwright scraper failed: {e}")
            print("Falling back to Selenium...")
    
    # Try Selenium
    try:
        print("Using Selenium scraper...")
        profile_links = scrape_realtor_list_page(list_url)
        scraped_data = []
        
        for i, profile_url in enumerate(profile_links[:max_profiles]):
            print(f"Scraping profile {i+1}/{min(len(profile_links), max_profiles)}: {profile_url}")
            profile_data = scrape_realtor_profile_page(profile_url)
            if profile_data:
                scraped_data.append(profile_data)
            # Add delay between requests to avoid rate limiting
            if i < len(profile_links) - 1:
                time.sleep(2)
        
        return scraped_data
    except Exception as e:
        print(f"Selenium scraper failed: {e}")
        
        # Final fallback to simple scraper
        if SIMPLE_SCRAPER_AVAILABLE:
            print("Falling back to simple requests-based scraper...")
            return scrape_with_simple(list_url, max_profiles)
        else:
            print("All scraping methods failed. Please ensure Chrome/ChromeDriver or requests/beautifulsoup4 are installed.")
            return [] 