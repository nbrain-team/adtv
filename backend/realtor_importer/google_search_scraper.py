"""
Google Search Scraper - Extracts contact info directly from Google search results
"""
import re
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
import requests
import urllib.parse
import time
import os

class GoogleSearchScraper:
    """Scraper for extracting contact info from Google search results"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv('BRIGHTDATA_API_TOKEN', 
            '041d23cddd90190caf6a08a9d703285033917e714f29ea3d6ab8b6d03533e7d6')
        self.api_url = "https://api.brightdata.com/request"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }
        
        # Patterns to avoid
        self.corporate_phone_patterns = [
            r'800', r'888', r'877', r'866', r'855', r'844', r'833',
            r'ext\.?', r'extension', r'x\d+'  # Extensions
        ]
    
    def search_google(self, query: str) -> Optional[BeautifulSoup]:
        """Perform Google search using Bright Data"""
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        try:
            print(f"  Searching Google: {query[:50]}...")  # Truncate long queries
            
            payload = {
                "zone": "homes_web_unlocker",
                "url": search_url,
                "format": "raw"
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Check if we got a valid Google page
                if soup.find('div', id='search') or soup.find('div', class_='g'):
                    return soup
                else:
                    print(f"  Warning: Got response but doesn't look like Google search results")
                    return None
            else:
                print(f"  API error: {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"  Timeout error searching Google")
            return None
        except Exception as e:
            print(f"  Error searching Google: {type(e).__name__}: {str(e)}")
            return None
    
    def extract_email_from_results(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract email addresses from Google search results"""
        emails_found = []
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Look in search result snippets
        snippets = soup.find_all(['span', 'div'], class_=re.compile(r'st|snippet|IsZvec|VwiC3b|yXK7lf'))
        
        for snippet in snippets:
            text = snippet.get_text()
            # Find all emails in the snippet
            for match in email_pattern.finditer(text):
                email = match.group()
                # Skip generic emails
                if not any(prefix in email.lower() for prefix in ['info@', 'sales@', 'support@', 'admin@']):
                    emails_found.append(email)
        
        # Also check meta descriptions
        meta_descriptions = soup.find_all('meta', attrs={'name': 'description'})
        for meta in meta_descriptions:
            content = meta.get('content', '')
            for match in email_pattern.finditer(content):
                email = match.group()
                if email not in emails_found:
                    emails_found.append(email)
        
        if emails_found:
            print(f"    Found {len(emails_found)} email(s) in search results")
            return emails_found[0]  # Return first email found
        
        return None
    
    def extract_phone_from_results(self, soup: BeautifulSoup, prefer_mobile: bool = True) -> Optional[str]:
        """Extract phone numbers from Google search results, preferring mobile/cell"""
        phones_found = []
        mobile_phones = []
        
        # Phone pattern
        phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        
        # Look in search result snippets
        snippets = soup.find_all(['span', 'div'], class_=re.compile(r'st|snippet|IsZvec|VwiC3b|yXK7lf'))
        
        for snippet in snippets:
            text = snippet.get_text()
            
            # Check if this snippet mentions mobile/cell
            is_mobile_context = any(term in text.lower() for term in ['mobile', 'cell', 'direct'])
            
            # Find all phones in the snippet
            for match in phone_pattern.finditer(text):
                phone = match.group()
                
                # Skip if it has extension or is corporate number
                if any(pattern in phone or pattern in text[max(0, match.start()-20):match.end()+20].lower() 
                       for pattern in self.corporate_phone_patterns):
                    continue
                
                # Clean the phone number
                clean_phone = re.sub(r'[^\d\-\(\)\s\+]', '', phone)
                
                if is_mobile_context and clean_phone not in mobile_phones:
                    mobile_phones.append(clean_phone)
                elif clean_phone not in phones_found:
                    phones_found.append(clean_phone)
        
        # Debug output
        print(f"    Found {len(mobile_phones)} mobile and {len(phones_found)} other phones")
        
        # Return mobile phone if found, otherwise first phone
        if mobile_phones:
            return mobile_phones[0]
        elif phones_found:
            return phones_found[0]
        
        return None
    
    def search_agent_contact(self, agent_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Search Google for agent's contact information"""
        result = {
            'google_email': None,
            'google_phone': None
        }
        
        # Build search components
        name = f"{agent_data.get('first_name', '')} {agent_data.get('last_name', '')}".strip()
        company = agent_data.get('company', '')
        location = f"{agent_data.get('city', '')}, {agent_data.get('state', '')}".strip(', ')
        
        if not name:
            print("  No agent name available for Google search")
            return result
        
        # Search for email
        email_query = f'"email address" @ "{name}" "{company}" "{location}"'
        email_soup = self.search_google(email_query)
        if email_soup:
            result['google_email'] = self.extract_email_from_results(email_soup)
            if result['google_email']:
                print(f"    ✓ Found email via Google: {result['google_email']}")
        
        # Small delay between searches
        time.sleep(2)
        
        # Search for phone (prefer mobile/cell)
        phone_query = f'"mobile phone" OR "cell phone" "{name}" "{company}" "{location}"'
        phone_soup = self.search_google(phone_query)
        if phone_soup:
            result['google_phone'] = self.extract_phone_from_results(phone_soup, prefer_mobile=True)
            if result['google_phone']:
                print(f"    ✓ Found phone via Google: {result['google_phone']}")
        
        return result 