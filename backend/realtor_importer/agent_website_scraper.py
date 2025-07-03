"""
Step 2 Scraper - Visits agent websites to extract additional contact information
"""
import re
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

class AgentWebsiteScraper:
    """Scraper for extracting data from agent's personal websites"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Patterns to ignore for emails
        self.generic_email_patterns = [
            r'^info@',
            r'^sales@',
            r'^customerservice@',
            r'^support@',
            r'^admin@',
            r'^contact@',
            r'^hello@',
            r'^help@',
            r'^office@',
            r'^team@',
            r'^noreply@',
            r'^no-reply@'
        ]
        
        # Patterns to ignore for phone numbers
        self.corporate_phone_patterns = [
            r'^1?-?800',
            r'^1?-?888',
            r'^1?-?877',
            r'^1?-?866',
            r'^1?-?855',
            r'^1?-?844',
            r'^1?-?833'
        ]
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page using requests"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None
    
    def is_generic_email(self, email: str) -> bool:
        """Check if email is generic/corporate"""
        email_lower = email.lower()
        for pattern in self.generic_email_patterns:
            if re.match(pattern, email_lower):
                return True
        return False
    
    def is_corporate_phone(self, phone: str) -> bool:
        """Check if phone is corporate (800 number etc)"""
        # Remove all non-digits for checking
        digits_only = re.sub(r'\D', '', phone)
        for pattern in self.corporate_phone_patterns:
            if re.match(pattern.replace('-', ''), digits_only):
                return True
        return False
    
    def extract_emails(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract personal email from page"""
        emails_found = []
        
        # Find all email links
        email_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in email_links:
            email = link.get('href', '').replace('mailto:', '').strip()
            if email and '@' in email and not self.is_generic_email(email):
                emails_found.append(email)
        
        # Also look for emails in text using regex
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        text = soup.get_text()
        for match in email_pattern.finditer(text):
            email = match.group()
            if not self.is_generic_email(email) and email not in emails_found:
                emails_found.append(email)
        
        # Return the first personal email found
        return emails_found[0] if emails_found else None
    
    def extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract personal phone number from page"""
        phones_found = []
        
        # Find all tel: links
        phone_links = soup.find_all('a', href=re.compile(r'^tel:', re.I))
        for link in phone_links:
            phone = link.get('href', '').replace('tel:', '').strip()
            if phone and not self.is_corporate_phone(phone):
                phones_found.append(phone)
        
        # Also look for phones in text using regex
        phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        text = soup.get_text()
        
        # Try to avoid footer sections
        main_content = soup.find('main') or soup.find('div', class_=re.compile(r'content|main', re.I)) or soup
        main_text = main_content.get_text()
        
        for match in phone_pattern.finditer(main_text):
            phone = match.group()
            if not self.is_corporate_phone(phone) and phone not in phones_found:
                phones_found.append(phone)
        
        # Return the first personal phone found
        return phones_found[0] if phones_found else None
    
    def extract_facebook(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Facebook profile link"""
        facebook_patterns = [
            r'facebook\.com/[^/\s]+/?$',
            r'fb\.com/[^/\s]+/?$'
        ]
        
        # Look for Facebook links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            for pattern in facebook_patterns:
                if re.search(pattern, href, re.I):
                    # Make sure it's a full URL
                    if not href.startswith('http'):
                        href = 'https://' + href.lstrip('/')
                    return href
        
        return None
    
    def scrape_agent_website(self, website_url: str) -> Dict[str, Optional[str]]:
        """Main method to scrape agent's website"""
        print(f"\nStep 2: Scraping agent website: {website_url}")
        
        result = {
            'phone2': None,
            'personal_email': None,
            'facebook_profile': None
        }
        
        soup = self.get_page(website_url)
        if not soup:
            print(f"  ✗ Failed to fetch website")
            return result
        
        # Extract data
        result['personal_email'] = self.extract_emails(soup)
        result['phone2'] = self.extract_phone(soup)
        result['facebook_profile'] = self.extract_facebook(soup)
        
        # Print results
        print(f"  Personal Email: {result['personal_email'] or 'Not found'}")
        print(f"  Phone 2: {result['phone2'] or 'Not found'}")
        print(f"  Facebook: {result['facebook_profile'] or 'Not found'}")
        
        return result 