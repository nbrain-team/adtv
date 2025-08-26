"""
Contact enrichment services - Google SERP, Facebook API, Website Scraping
"""
import re
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import phonenumbers
from urllib.parse import urlparse, urljoin
import asyncio
import aiohttp
import facebook
import os
import json

logger = logging.getLogger(__name__)


class GoogleSERPService:
    """Service for searching Google via Serper.dev API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.generic_email_prefixes = (
            'info', 'contact', 'team', 'sales', 'email', 'support', 'admin', 'office', 'hello'
        )
        # Enhanced phone pattern to catch more formats
        self.phone_patterns = [
            re.compile(r'(\+?1?\s*\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'),  # Standard US
            re.compile(r'(\([0-9]{3}\)\s*[0-9]{3}-[0-9]{4})'),  # (555) 555-5555
            re.compile(r'([0-9]{3}\.[0-9]{3}\.[0-9]{4})'),  # 555.555.5555
            re.compile(r'([0-9]{3}\s[0-9]{3}\s[0-9]{4})'),  # 555 555 5555
            re.compile(r'(1-[0-9]{3}-[0-9]{3}-[0-9]{4})'),  # 1-555-555-5555
            re.compile(r'(\+1\s*[0-9]{3}\s*[0-9]{3}\s*[0-9]{4})'),  # +1 555 555 5555
            re.compile(r'([(]?[0-9]{3}[)]?\s?[0-9]{3}[-\s]?[0-9]{4})'),  # Various formats
        ]
    
    async def search_contact_info(self, name: str, company: str = None, city: str = None, 
                                  state: str = None, website: str = None) -> Dict[str, Any]:
        """Search for contact information using various query strategies"""
        results = {
            'emails': [],
            'phones': [],
            'sources': []
        }
        
        # Build search queries
        queries = self._build_search_queries(name, company, city, state, website)
        
        for query in queries:
            try:
                # Call Serper.dev API
                headers = {
                    'X-API-KEY': self.api_key,
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'q': query,
                    'num': 20
                }
                
                response = requests.post(self.base_url, json=payload, headers=headers)
                if response.status_code != 200:
                    logger.error(f"Serper.dev API error: {response.status_code} - {response.text}")
                    continue
                    
                search_results = response.json()
                
                # Extract from organic results
                for result in search_results.get('organic', []):
                    snippet = result.get('snippet', '')
                    title = result.get('title', '')
                    link = result.get('link', '')
                    
                    # Search for emails
                    emails = self.email_pattern.findall(snippet + ' ' + title)
                    for email in emails:
                        if self._is_valid_email(email, name):
                            results['emails'].append({
                                'email': email.lower(),
                                'source': link,
                                'confidence': self._calculate_email_confidence(email, name, company)
                            })
                    
                    # Search for phones
                    phones = self._find_phone_numbers(snippet + ' ' + title)
                    for phone in phones:
                        formatted_phone = self._format_phone(phone)
                        if formatted_phone:
                            # Determine type and adjust confidence
                            phone_conf = 0.8
                            phone_type_str = 'unknown'
                            try:
                                parsed = phonenumbers.parse(formatted_phone, "US")
                                ptype = phonenumbers.number_type(parsed)
                                # Bias toward mobile numbers
                                if ptype in (phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE):
                                    phone_conf += 0.15
                                    phone_type_str = 'mobile'
                                elif ptype == phonenumbers.PhoneNumberType.FIXED_LINE:
                                    phone_type_str = 'fixed_line'
                                # Basic heuristics to penalize office-style numbers
                                national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                                digits = re.sub(r'\D', '', national)
                                if len(digits) >= 10:
                                    area = digits[:3]
                                    last4 = digits[-4:]
                                    if area in {'800','888','877','866','855','844','833','822'}:
                                        phone_conf -= 0.25
                                    if last4 in {'0000','1000','2000','3000','4000','5000'}:
                                        phone_conf -= 0.1
                                text_ctx = (snippet + ' ' + title).lower()
                                if any(token in text_ctx for token in ['cell', 'mobile', 'text me']):
                                    phone_conf += 0.1
                                if any(token in text_ctx for token in ['office', 'main line', 'switchboard']):
                                    phone_conf -= 0.1
                            except Exception:
                                pass
                            results['phones'].append({
                                'phone': formatted_phone,
                                'source': link,
                                'confidence': max(0.0, min(1.0, phone_conf)),
                                'type': phone_type_str
                            })
                    
                    results['sources'].append(link)
                
                # Also check people also ask if available
                for paa in search_results.get('peopleAlsoAsk', []):
                    snippet = paa.get('snippet', '')
                    emails = self.email_pattern.findall(snippet)
                    phones = self._find_phone_numbers(snippet)
                    
                    for email in emails:
                        if self._is_valid_email(email, name):
                            results['emails'].append({
                                'email': email.lower(),
                                'source': 'People Also Ask',
                                'confidence': 0.7
                            })
                    
                    for phone in phones:
                        formatted_phone = self._format_phone(phone)
                        if formatted_phone:
                            phone_conf = 0.7
                            phone_type_str = 'unknown'
                            try:
                                parsed = phonenumbers.parse(formatted_phone, "US")
                                ptype = phonenumbers.number_type(parsed)
                                if ptype in (phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE):
                                    phone_conf += 0.15
                                    phone_type_str = 'mobile'
                                elif ptype == phonenumbers.PhoneNumberType.FIXED_LINE:
                                    phone_type_str = 'fixed_line'
                                national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                                digits = re.sub(r'\D', '', national)
                                if len(digits) >= 10:
                                    area = digits[:3]
                                    last4 = digits[-4:]
                                    if area in {'800','888','877','866','855','844','833','822'}:
                                        phone_conf -= 0.25
                                    if last4 in {'0000','1000','2000','3000','4000','5000'}:
                                        phone_conf -= 0.1
                                text_ctx = snippet.lower()
                                if any(token in text_ctx for token in ['cell', 'mobile', 'text me']):
                                    phone_conf += 0.1
                                if any(token in text_ctx for token in ['office', 'main line', 'switchboard']):
                                    phone_conf -= 0.1
                            except Exception:
                                pass
                            results['phones'].append({
                                'phone': formatted_phone,
                                'source': 'People Also Ask',
                                'confidence': max(0.0, min(1.0, phone_conf)),
                                'type': phone_type_str
                            })
                
            except Exception as e:
                logger.error(f"Error searching with Serper.dev for {query}: {str(e)}")
                continue
        
        # Deduplicate and get best results
        results['emails'] = self._deduplicate_results(results['emails'], 'email')
        results['phones'] = self._deduplicate_results(results['phones'], 'phone')
        
        return results
    
    def _build_search_queries(self, name: str, company: str, city: str, state: str, website: str) -> List[str]:
        """Build minimal search queries per spec (2 email + 2 phone)."""
        queries: List[str] = []
        if not name:
            return queries

        has_city_state = bool(city and state)

        # Email queries
        if has_city_state and company:
            # “Full Name” Company Name "email" “@” City, State
            queries.append(f'"{name}" {company} "email" "@" {city}, {state}')
        if has_city_state:
            # “Full Name” "email" “@” City, State
            queries.append(f'"{name}" "email" "@" {city}, {state}')

        # Phone queries
        if has_city_state:
            # “Name” “cell” OR “mobile” OR “phone” City State
            queries.append(f'"{name}" "cell" OR "mobile" OR "phone" {city} {state}')
        if city and company:
            # “Name” “cell” OR “mobile” OR “phone” City Company
            queries.append(f'"{name}" "cell" OR "mobile" OR "phone" {city} {company}')

        logger.info(
            f"Building search queries for: name='{name}', city='{city}', state='{state}', company='{company}'"
        )
        logger.info(f"Generated queries: {queries}")
        return queries
    
    def _is_valid_email(self, email: str, name: str) -> bool:
        """Check if email is likely valid for the person"""
        email_lower = email.lower()
        name_parts = name.lower().split()
        
        # Avoid generic emails by local-part
        try:
            local_part = email_lower.split('@')[0]
            local_part = local_part.split('+')[0]
            for prefix in self.generic_email_prefixes:
                if local_part == prefix or local_part.startswith(prefix + '.') or local_part.endswith('.' + prefix):
                    # Allow through only if name appears in the address strongly
                    for part in name_parts:
                        if len(part) > 2 and part in email_lower:
                            return True
                    return False
        except Exception:
            pass
        
        # Accept email if it contains any part of the name
        for part in name_parts:
            if len(part) > 2 and part in email_lower:
                return True
        
        # Accept email if it's from a real estate domain
        real_estate_domains = ['remax', 'kw.com', 'coldwellbanker', 'century21', 'sothebys', 'compass.com', 'exp', 'bhhsca']
        if any(domain in email_lower for domain in real_estate_domains):
            return True
        
        # If none of the above, still accept if it looks professional (not obviously spam)
        if '@' in email and '.' in email.split('@')[1]:
            return True
        
        return False
    
    def _calculate_email_confidence(self, email: str, name: str, company: str) -> float:
        """Calculate confidence score for email"""
        confidence = 0.5
        email_lower = email.lower()
        
        # Name match
        name_parts = name.lower().split()
        for part in name_parts:
            if part in email_lower:
                confidence += 0.2
        
        # Company domain match
        if company and '@' in email:
            domain = email.split('@')[1]
            if company.lower().replace(' ', '') in domain:
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _find_phone_numbers(self, text: str) -> List[str]:
        """Find phone numbers in a given text using multiple patterns."""
        found_numbers = []
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Remove any non-digit characters from the match
                cleaned_match = re.sub(r'\D', '', match)
                if len(cleaned_match) == 10: # Assuming US phone numbers are 10 digits
                    found_numbers.append(cleaned_match)
        return found_numbers

    def _format_phone(self, phone: str) -> Optional[str]:
        """Format phone number to standard format"""
        try:
            # Parse phone number (assuming US)
            parsed = phonenumbers.parse(phone, "US")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        except:
            pass
        return None
    
    def _deduplicate_results(self, results: List[Dict], key: str) -> List[Dict]:
        """Deduplicate results keeping highest confidence"""
        seen = {}
        for item in results:
            value = item[key]
            if value not in seen or item['confidence'] > seen[value]['confidence']:
                seen[value] = item
        return list(seen.values())


class FacebookService:
    """Service for fetching Facebook page data"""
    
    def __init__(self, access_token: str):
        self.graph = facebook.GraphAPI(access_token)
    
    async def get_page_data(self, facebook_url: str) -> Dict[str, Any]:
        """Get Facebook page data including recent posts"""
        try:
            # Extract page ID or username from URL
            page_id = self._extract_page_id(facebook_url)
            if not page_id:
                return {}
            
            # Get page info
            page_info = self.graph.get_object(
                id=page_id,
                fields='name,followers_count,about,phone,website,emails'
            )
            
            # Get recent posts
            posts = self.graph.get_connections(
                id=page_id,
                connection_name='posts',
                fields='message,created_time,likes.summary(true),comments.summary(true),shares',
                limit=5
            )
            
            # Process results
            result = {
                'followers': page_info.get('followers_count', 0),
                'about': page_info.get('about', ''),
                'phone': page_info.get('phone'),
                'website': page_info.get('website'),
                'emails': page_info.get('emails', []),
                'posts': []
            }
            
            # Process posts
            for post in posts.get('data', []):
                if post.get('message'):
                    result['posts'].append({
                        'message': post['message'],
                        'created_time': post['created_time'],
                        'likes': post.get('likes', {}).get('summary', {}).get('total_count', 0),
                        'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                        'shares': post.get('shares', {}).get('count', 0) if post.get('shares') else 0
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Facebook data for {facebook_url}: {str(e)}")
            return {}
    
    def _extract_page_id(self, url: str) -> Optional[str]:
        """Extract page ID or username from Facebook URL"""
        # Handle various Facebook URL formats
        patterns = [
            r'facebook\.com/pages/[^/]+/(\d+)',
            r'facebook\.com/profile\.php\?id=(\d+)',
            r'facebook\.com/([^/\?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


class WebsiteScraper:
    """Service for scraping contact info from websites"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_patterns = [
            re.compile(r'(\+?1?\s*\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'),
            re.compile(r'(\([0-9]{3}\)\s*[0-9]{3}-[0-9]{4})'),
            re.compile(r'([0-9]{3}\.[0-9]{3}\.[0-9]{4})'),
            re.compile(r'([0-9]{3}\s[0-9]{3}\s[0-9]{4})'),
            re.compile(r'(1-[0-9]{3}-[0-9]{3}-[0-9]{4})'),
            re.compile(r'(\+1\s*[0-9]{3}\s*[0-9]{3}\s*[0-9]{4})'),
        ]
        self.social_patterns = {
            'facebook': r'facebook\.com/[^/\s]+',
            'twitter': r'twitter\.com/[^/\s]+',
            'linkedin': r'linkedin\.com/[^/\s]+',
            'instagram': r'instagram\.com/[^/\s]+'
        }
    
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape website for contact information"""
        results = {
            'emails': [],
            'phones': [],
            'social_links': {},
            'scraped': False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # First try the main page
                content = await self._fetch_page(session, url)
                if content:
                    self._extract_contact_info(content, results)
                
                # Try common contact pages
                contact_paths = ['/contact', '/about', '/contact-us', '/about-us']
                base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                
                for path in contact_paths:
                    contact_url = urljoin(base_url, path)
                    content = await self._fetch_page(session, contact_url)
                    if content:
                        self._extract_contact_info(content, results)
                
                results['scraped'] = True
                
        except Exception as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
        
        # Deduplicate
        results['emails'] = list(set(results['emails']))
        results['phones'] = list(set(results['phones']))
        
        return results
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch page content"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except:
            pass
        return None
    
    def _extract_contact_info(self, html: str, results: Dict[str, Any]):
        """Extract contact information from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Extract emails
        emails = self.email_pattern.findall(text)
        for email in emails:
            if '@' in email and not email.endswith('.png') and not email.endswith('.jpg'):
                results['emails'].append(email.lower())
        
        # Extract phones
        phones = []
        for pattern in self.phone_patterns:
            found = pattern.findall(text)
            phones.extend(found)
        
        for phone in phones:
            try:
                parsed = phonenumbers.parse(phone, "US")
                if phonenumbers.is_valid_number(parsed):
                    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                    results['phones'].append(formatted)
            except:
                pass
        
        # Extract social links
        for social, pattern in self.social_patterns.items():
            links = re.findall(pattern, str(soup))
            if links:
                results['social_links'][social] = f"https://{links[0]}"


class EmailValidator:
    """Service for validating emails using ZeroBounce"""
    
    def __init__(self, api_key: str = "848cbcd03ba043eaa677fc9f56c77da6"):
        self.api_key = api_key
        self.api_url = "https://api.zerobounce.net/v2/validate"
    
    async def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email using ZeroBounce API"""
        try:
            params = {
                'api_key': self.api_key,
                'email': email
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'valid': result.get('status') == 'valid',
                            'status': result.get('status'),
                            'sub_status': result.get('sub_status'),
                            'score': result.get('zerobounce_score', 0),
                            'did_you_mean': result.get('did_you_mean')
                        }
        except Exception as e:
            logger.error(f"Error validating email {email}: {str(e)}")
        
        return {'valid': None, 'status': 'error'}


class ContactEnricher:
    """Main service orchestrating all enrichment services"""
    
    def __init__(self):
        # Get API keys from environment variables
        serp_api_key = os.getenv("SERP_API_KEY")
        facebook_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        if not serp_api_key:
            raise ValueError("SERP_API_KEY environment variable not set")
        
        self.google_service = GoogleSERPService(serp_api_key)
        self.facebook_service = FacebookService(facebook_token) if facebook_token else None
        self.website_scraper = WebsiteScraper()
        self.email_validator = EmailValidator()
    
    async def enrich_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single contact with all available data"""
        enriched = {
            'original_data': contact_data,
            'enrichment_results': {}
        }
        
        # Extract key fields
        name = contact_data.get('Name', '')
        company = contact_data.get('Company', '')
        city = contact_data.get('City', '')
        state = contact_data.get('State', '')
        website = contact_data.get('Agent_Website', '')
        facebook = contact_data.get('Facebook_Profile', '')
        
        # 1. Google SERP search
        if name:
            google_results = await self.google_service.search_contact_info(
                name, company, city, state, website
            )
            enriched['enrichment_results']['google'] = google_results
        
        # 2. Website scraping
        if website and website != 'Not Found':
            website_results = await self.website_scraper.scrape_website(website)
            enriched['enrichment_results']['website'] = website_results
        
        # 3. Facebook data
        if self.facebook_service and facebook and facebook != 'Not Found':
            facebook_results = await self.facebook_service.get_page_data(facebook)
            enriched['enrichment_results']['facebook'] = facebook_results
        
        # 4. Consolidate and validate results
        best_email = self._get_best_email(enriched['enrichment_results'])
        if best_email:
            validation = await self.email_validator.validate_email(best_email['email'])
            enriched['enrichment_results']['email_validation'] = validation
        
        return enriched
    
    def _get_best_email(self, results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the highest confidence email from all sources"""
        all_emails = []
        
        # From Google
        if 'google' in results:
            all_emails.extend(results['google'].get('emails', []))
        
        # From website
        if 'website' in results:
            for email in results['website'].get('emails', []):
                all_emails.append({
                    'email': email,
                    'source': 'website',
                    'confidence': 0.9
                })
        
        # From Facebook
        if 'facebook' in results:
            for email in results['facebook'].get('emails', []):
                all_emails.append({
                    'email': email,
                    'source': 'facebook',
                    'confidence': 0.95
                })
        
        # Sort by confidence and return best
        if all_emails:
            return max(all_emails, key=lambda x: x['confidence'])
        
        return None 