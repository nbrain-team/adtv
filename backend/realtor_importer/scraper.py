import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Any
import random

# --- Enhanced Scraping Configuration ---

# A list of common user-agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

def get_soup(url: str) -> Optional[BeautifulSoup]:
    """Fetches a URL and returns a BeautifulSoup object with rotated headers."""
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1' # Do Not Track header
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    except (requests.RequestException, requests.exceptions.Timeout) as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_realtor_list_page(list_url: str) -> List[str]:
    """
    Scrapes a homes.com list page to find all individual realtor profile links.
    NOTE: These selectors are based on anticipated page structure and may need adjustment.
    """
    soup = get_soup(list_url)
    if not soup:
        return []

    profile_links = set()
    # This selector targets links within a common agent card structure.
    for a_tag in soup.select('.agent-card-details-container a, a.for-sale-card-link, .agent-card a'):
        href = a_tag.get('href')
        if href and ('/real-estate-agents/' in href or '/agent/' in href):
            # Ensure we construct an absolute URL
            if not href.startswith('http'):
                href = f"https://www.homes.com{href}"
            profile_links.add(href)
    
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
    soup = get_soup(profile_url)
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