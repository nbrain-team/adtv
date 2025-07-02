"""
Web Unlocker scraper for Bright Data - handles anti-bot measures automatically
"""
import requests
from bs4 import BeautifulSoup
import os
import time
from typing import List, Dict, Optional, Any
import re
import json

class WebUnlockerScraper:
    """Scraper using Bright Data's Web Unlocker API"""
    
    def __init__(self):
        # Get API token from environment or use default
        self.api_token = os.getenv('BRIGHTDATA_API_TOKEN', 
            '041d23cddd90190caf6a08a9d703285033917e714f29ea3d6ab8b6d03533e7d6')
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
            print(f"Fetching: {url}")
            
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
                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def scrape_agent_list(self, list_url: str) -> List[str]:
        """Scrape list of agent profile URLs"""
        soup = self.get_page(list_url)
        if not soup:
            return []
        
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        
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
                print(f"Selector '{selector}' found {len(elements)} elements")
            
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
            print("No profiles found. Checking page content...")
            # Look for any links with real estate agent patterns
            all_links = soup.find_all('a', href=True)
            agent_pattern = re.compile(r'real.*estate.*agent|realtor|agent.*profile', re.I)
            for link in all_links[:20]:  # Check first 20 links
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if agent_pattern.search(href) or agent_pattern.search(text):
                    print(f"  Potential agent link: {href} - {text[:50]}")
        
        print(f"Found {len(profile_links)} unique agent profiles")
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
        company_elem = soup.select_one('.brokerage-name, [class*="brokerage"], [class*="company"], .agent-office')
        if company_elem:
            data['company'] = self.clean_text(company_elem.get_text())
        
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
        
        return data


def scrape_with_web_unlocker(list_url: str, max_profiles: int = 10) -> List[Dict[str, Any]]:
    """Main entry point for Web Unlocker scraping"""
    print("Using Bright Data Web Unlocker API...")
    scraper = WebUnlockerScraper()
    
    # Get agent profile URLs
    profile_urls = scraper.scrape_agent_list(list_url)
    
    if not profile_urls:
        print("No profiles found on list page")
        return []
    
    # Scrape individual profiles
    results = []
    for i, url in enumerate(profile_urls[:max_profiles]):
        print(f"\nScraping profile {i+1}/{min(len(profile_urls), max_profiles)}: {url}")
        
        profile_data = scraper.scrape_agent_profile(url)
        if profile_data and (profile_data.get('first_name') or profile_data.get('last_name')):
            results.append(profile_data)
            print(f"  ✓ Scraped: {profile_data.get('first_name')} {profile_data.get('last_name')}")
        else:
            print(f"  ✗ Failed to extract data")
        
        # Be respectful with delays
        if i < len(profile_urls) - 1:
            time.sleep(2)
    
    print(f"\nCompleted: Scraped {len(results)} profiles successfully")
    return results


if __name__ == "__main__":
    # Test the scraper
    test_url = "https://www.homes.com/real-estate-agents/carlsbad-ca/"
    results = scrape_with_web_unlocker(test_url, max_profiles=5)
    
    print("\n=== Results ===")
    for r in results:
        print(f"{r.get('first_name')} {r.get('last_name')} - {r.get('company')} ({r.get('city')}, {r.get('state')})")
        if r.get('cell_phone'):
            print(f"  Phone: {r.get('cell_phone')}")
        if r.get('email'):
            print(f"  Email: {r.get('email')}") 