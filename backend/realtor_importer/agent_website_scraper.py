"""
Step 2 Scraper - Visits agent websites to extract additional contact information
"""
import re
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import urllib3

# Suppress SSL warnings for agent websites with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        """Fetch a page using requests with retries"""
        try:
            # Add timeout and allow redirects
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=15,
                allow_redirects=True,
                verify=False  # Some agent sites have SSL issues
            )
            
            # Check if we got a successful response
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"  HTTP {response.status_code} error for {url}")
                
        except requests.exceptions.Timeout:
            print(f"  Timeout error fetching {url}")
        except requests.exceptions.SSLError:
            print(f"  SSL error fetching {url}")
        except requests.exceptions.ConnectionError:
            print(f"  Connection error fetching {url}")
        except Exception as e:
            print(f"  Unexpected error fetching {url}: {type(e).__name__}: {e}")
            
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
        """Extract personal email from page, with fallback to any email"""
        personal_emails = []
        all_emails = []
        
        # Find all email links
        email_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in email_links:
            email = link.get('href', '').replace('mailto:', '').strip()
            if email and '@' in email:
                all_emails.append(email)
                if not self.is_generic_email(email):
                    personal_emails.append(email)
        
        # Also look for emails in text using regex
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        text = soup.get_text()
        for match in email_pattern.finditer(text):
            email = match.group()
            if email not in all_emails:
                all_emails.append(email)
                if not self.is_generic_email(email):
                    personal_emails.append(email)
        
        # Debug logging
        print(f"    Email search - Personal found: {len(personal_emails)}, Total found: {len(all_emails)}")
        
        # Return strategy: prefer personal email, fall back to any email
        if personal_emails:
            print(f"    Using personal email: {personal_emails[0]}")
            return personal_emails[0]
        elif all_emails:
            print(f"    No personal email found, using generic: {all_emails[0]}")
            return all_emails[0]
        
        return None
    
    def extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract personal phone number from page, with fallback to any phone"""
        personal_phones = []
        all_phones = []
        
        # Find all tel: links
        phone_links = soup.find_all('a', href=re.compile(r'^tel:', re.I))
        for link in phone_links:
            phone = link.get('href', '').replace('tel:', '').strip()
            if phone:
                # Clean the phone number
                clean_phone = re.sub(r'[^\d\-\(\)\s\+]', '', phone)
                if clean_phone not in all_phones:
                    all_phones.append(clean_phone)
                    if not self.is_corporate_phone(clean_phone):
                        personal_phones.append(clean_phone)
        
        # Look for phones in text using regex
        phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        
        # First try main content area
        main_content = soup.find('main') or soup.find('div', class_=re.compile(r'content|main', re.I))
        if main_content:
            main_text = main_content.get_text()
            for match in phone_pattern.finditer(main_text):
                phone = match.group()
                clean_phone = re.sub(r'[^\d\-\(\)\s\+]', '', phone)
                if clean_phone not in all_phones:
                    all_phones.append(clean_phone)
                    if not self.is_corporate_phone(clean_phone):
                        personal_phones.append(clean_phone)
        
        # If no phones found in main content, search entire page
        if not personal_phones and not all_phones:
            full_text = soup.get_text()
            for match in phone_pattern.finditer(full_text):
                phone = match.group()
                clean_phone = re.sub(r'[^\d\-\(\)\s\+]', '', phone)
                if clean_phone not in all_phones:
                    all_phones.append(clean_phone)
                    if not self.is_corporate_phone(clean_phone):
                        personal_phones.append(clean_phone)
        
        # Debug logging
        print(f"    Phone search - Personal found: {len(personal_phones)}, Total found: {len(all_phones)}")
        
        # Return strategy: prefer personal phone, fall back to any phone
        if personal_phones:
            print(f"    Using personal phone: {personal_phones[0]}")
            return personal_phones[0]
        elif all_phones:
            print(f"    No personal phone found, using corporate/generic: {all_phones[0]}")
            return all_phones[0]
        
        return None
    
    def extract_facebook(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Facebook profile link"""
        facebook_links = []
        
        # Look for Facebook links with various patterns
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Check for Facebook URLs
            if 'facebook.com' in href or 'fb.com' in href:
                # Clean and validate the URL
                if href.startswith('//'):
                    href = 'https:' + href
                elif not href.startswith('http'):
                    href = 'https://facebook.com' + href if href.startswith('/') else 'https://' + href
                
                # Skip Facebook's generic pages
                skip_patterns = ['facebook.com/sharer', 'facebook.com/dialog', 'facebook.com/tr?']
                if not any(skip in href for skip in skip_patterns):
                    facebook_links.append(href)
        
        # Also check for Facebook in onclick or data attributes
        for elem in soup.find_all(attrs={'onclick': re.compile(r'facebook\.com|fb\.com', re.I)}):
            onclick = elem.get('onclick', '')
            match = re.search(r'(https?://(?:www\.)?(?:facebook\.com|fb\.com)/[^\s\'"]+)', onclick)
            if match:
                facebook_links.append(match.group(1))
        
        # Debug logging
        print(f"    Facebook search - Found {len(facebook_links)} links")
        
        if facebook_links:
            # Return the first valid Facebook link
            print(f"    Using Facebook: {facebook_links[0]}")
            return facebook_links[0]
        
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
        
        # Log page title for debugging
        title = soup.find('title')
        if title:
            print(f"  Page title: {title.get_text()[:100]}")
        
        # Extract data
        result['personal_email'] = self.extract_emails(soup)
        result['phone2'] = self.extract_phone(soup)
        result['facebook_profile'] = self.extract_facebook(soup)
        
        # Print results
        print(f"  Step 2 Results:")
        print(f"    Personal Email: {result['personal_email'] or 'Not found'}")
        print(f"    Phone 2: {result['phone2'] or 'Not found'}")
        print(f"    Facebook: {result['facebook_profile'] or 'Not found'}")
        
        return result 