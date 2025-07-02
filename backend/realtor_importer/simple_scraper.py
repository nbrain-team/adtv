"""
Simple scraper using requests and BeautifulSoup as a fallback
when Selenium/Playwright are not available
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Any
import time
import random

# User agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

def get_soup(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return BeautifulSoup object"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean and strip text content"""
    return text.strip() if text else None

def parse_numeric(text: Optional[str]) -> Optional[int]:
    """Parse numeric values from text"""
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text)
    return int(cleaned) if cleaned else None

def scrape_homes_list_simple(list_url: str) -> List[str]:
    """Scrape a homes.com list page for profile links using requests"""
    print(f"Simple scraper: Fetching list page: {list_url}")
    soup = get_soup(list_url)
    if not soup:
        return []
    
    profile_links = set()
    
    # Look for agent links - these patterns work on homes.com
    link_patterns = [
        'a[href*="/real-estate-agents/"]',
        'a[href*="/agent/"]',
        'a.agent-name',
        'a.agent-card-link',
        '.agent-list-card a',
        '.agent-card a'
    ]
    
    for pattern in link_patterns:
        for link in soup.select(pattern):
            href = link.get('href')
            if href and ('/real-estate-agents/' in href or '/agent/' in href):
                # Make absolute URL
                if not href.startswith('http'):
                    href = f"https://www.homes.com{href}"
                # Filter out non-profile links
                if not any(skip in href for skip in ['/search/', '/office/', '/company/']):
                    profile_links.add(href)
    
    print(f"Simple scraper: Found {len(profile_links)} profile links")
    return list(profile_links)

def scrape_homes_profile_simple(profile_url: str) -> Optional[Dict[str, Any]]:
    """Scrape individual agent profile using requests"""
    print(f"Simple scraper: Fetching profile: {profile_url}")
    soup = get_soup(profile_url)
    if not soup:
        return None
    
    data = {"profile_url": profile_url}
    
    # Extract name - try multiple selectors
    name_element = soup.select_one('h1, .agent-name, [class*="agent-name"]')
    if name_element:
        full_name = clean_text(name_element.get_text())
        if full_name:
            parts = full_name.split(' ', 1)
            data['first_name'] = parts[0] if parts else None
            data['last_name'] = parts[1] if len(parts) > 1 else None
    
    # Extract company/brokerage
    company_selectors = [
        '.brokerage-name',
        '[class*="brokerage"]',
        '.agent-company',
        '.office-name'
    ]
    for selector in company_selectors:
        elem = soup.select_one(selector)
        if elem:
            data['company'] = clean_text(elem.get_text())
            break
    
    # Extract location
    location_selectors = [
        '.agent-location',
        '[class*="location"]',
        '.agent-city-state',
        '.agent-address'
    ]
    for selector in location_selectors:
        elem = soup.select_one(selector)
        if elem:
            location_text = clean_text(elem.get_text())
            if location_text:
                parts = location_text.split(',')
                data['city'] = clean_text(parts[0]) if parts else None
                data['state'] = clean_text(parts[1]) if len(parts) > 1 else None
            break
    
    # Extract phone
    phone_link = soup.select_one('a[href^="tel:"]')
    if phone_link:
        phone_href = phone_link.get('href')
        if phone_href:
            data['cell_phone'] = phone_href.replace('tel:', '').strip()
    
    # Extract email
    email_link = soup.select_one('a[href^="mailto:"]')
    if email_link:
        email_href = email_link.get('href')
        if email_href:
            data['email'] = email_href.replace('mailto:', '').strip()
    
    # Try to extract any stats/metrics
    stats_text = soup.get_text()
    
    # Look for patterns like "X deals" or "X transactions"
    deals_match = re.search(r'(\d+)\s*(?:total\s*)?(?:deals?|transactions?)', stats_text, re.I)
    if deals_match:
        data['seller_deals_total_deals'] = int(deals_match.group(1))
    
    # Look for dollar amounts
    value_match = re.search(r'\$([0-9,]+(?:\.\d+)?)\s*(?:million|M)?\s*(?:in\s*sales)?', stats_text, re.I)
    if value_match:
        value_str = value_match.group(1).replace(',', '')
        multiplier = 1000000 if 'million' in value_match.group(0).lower() or 'M' in value_match.group(0) else 1
        data['seller_deals_total_value'] = int(float(value_str) * multiplier)
    
    # Set defaults
    data.setdefault('dma', None)
    data.setdefault('source', 'homes.com')
    data.setdefault('years_exp', None)
    data.setdefault('fb_or_website', profile_url)
    
    return data

def scrape_with_simple(list_url: str, max_profiles: int = 10) -> List[Dict[str, Any]]:
    """Main entry point for simple scraper"""
    print("Using simple requests-based scraper (no browser required)...")
    
    # Get profile links
    profile_links = scrape_homes_list_simple(list_url)
    if not profile_links:
        print("No profiles found on list page")
        return []
    
    # Scrape individual profiles
    scraped_data = []
    for i, profile_url in enumerate(profile_links[:max_profiles]):
        print(f"\nScraping profile {i+1}/{min(len(profile_links), max_profiles)}")
        
        profile_data = scrape_homes_profile_simple(profile_url)
        if profile_data:
            # Only add if we at least got a name
            if profile_data.get('first_name') or profile_data.get('last_name'):
                scraped_data.append(profile_data)
        
        # Random delay to be respectful
        if i < len(profile_links) - 1:
            time.sleep(random.uniform(1, 3))
    
    print(f"\nSimple scraper completed. Found {len(scraped_data)} profiles with data.")
    return scraped_data 