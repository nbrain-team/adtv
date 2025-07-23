#!/usr/bin/env python3
"""
Debug script for Contact Enricher email search
Tests why emails aren't being found
"""
import os
import sys
import asyncio
import re
from serpapi import GoogleSearch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from contact_enricher.services import GoogleSERPService

def test_serp_api_direct():
    """Test SERP API directly to see raw results"""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ SERP_API_KEY not set!")
        print("Set it with: export SERP_API_KEY='your_key'")
        return
    
    print("🔍 Testing SERP API directly...")
    
    # Test search queries
    test_queries = [
        '"John Smith" "@" Huntsville AL real estate',
        '"John Smith" realtor Huntsville email phone',
        '"John Smith" Huntsville real estate agent contact',
        'site:linkedin.com/in "John Smith" realtor Huntsville',
        '"John Smith" Huntsville AL contact information email'
    ]
    
    for query in test_queries:
        print(f"\n📌 Testing query: {query}")
        print("-" * 60)
        
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": api_key,
                "num": 10
            })
            
            results = search.get_dict()
            
            # Check for organic results
            organic_results = results.get('organic_results', [])
            print(f"Found {len(organic_results)} organic results")
            
            # Look for emails in results
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            emails_found = []
            
            for i, result in enumerate(organic_results[:3]):  # First 3 results
                print(f"\n  Result {i+1}:")
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  Link: {result.get('link', 'N/A')}")
                print(f"  Snippet: {result.get('snippet', 'N/A')[:200]}...")
                
                # Search for emails in snippet and title
                text = f"{result.get('snippet', '')} {result.get('title', '')}"
                found_emails = email_pattern.findall(text)
                
                if found_emails:
                    print(f"  ✅ Emails found: {found_emails}")
                    emails_found.extend(found_emails)
                else:
                    print(f"  ❌ No emails in this result")
            
            print(f"\n📧 Total emails found for this query: {len(set(emails_found))}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def test_enricher_service():
    """Test the GoogleSERPService with debug output"""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ SERP_API_KEY not set!")
        return
    
    print("\n\n🔬 Testing GoogleSERPService...")
    print("=" * 60)
    
    service = GoogleSERPService(api_key)
    
    # Test with a real person's data
    test_cases = [
        {
            "name": "John Smith",
            "company": "ABC Realty",
            "city": "Huntsville",
            "state": "AL",
            "website": None
        }
    ]
    
    for test in test_cases:
        print(f"\n📋 Testing: {test['name']} from {test.get('city', 'Unknown')}")
        
        # Test the search
        results = await service.search_contact_info(
            name=test['name'],
            company=test.get('company'),
            city=test.get('city'),
            state=test.get('state'),
            website=test.get('website')
        )
        
        print(f"\n📊 Results:")
        print(f"  Emails found: {len(results['emails'])}")
        for email_info in results['emails']:
            print(f"    - {email_info['email']} (confidence: {email_info['confidence']:.2f})")
        
        print(f"  Phones found: {len(results['phones'])}")
        for phone_info in results['phones']:
            print(f"    - {phone_info['phone']} (confidence: {phone_info['confidence']:.2f})")
        
        print(f"  Sources checked: {len(results['sources'])}")

def check_specific_url():
    """Check a specific URL for emails"""
    print("\n\n🌐 Checking specific URL for emails...")
    print("=" * 60)
    
    url = input("Enter a URL where you found an email: ").strip()
    
    if not url:
        print("No URL provided")
        return
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Search for emails
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            emails = email_pattern.findall(text)
            
            if emails:
                print(f"✅ Found {len(set(emails))} unique emails:")
                for email in set(emails):
                    print(f"  - {email}")
            else:
                print("❌ No emails found in page content")
                
            # Save content for analysis
            with open("debug_page_content.txt", "w") as f:
                f.write(text)
            print("\n💾 Page content saved to debug_page_content.txt for analysis")
            
        else:
            print(f"❌ Failed to fetch URL: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error fetching URL: {str(e)}")

async def test_with_real_data():
    """Test with actual data from the CSV"""
    print("\n\n🎯 Testing with real contact data...")
    print("=" * 60)
    
    # Get sample data
    name = input("Enter the exact name from your CSV: ").strip()
    city = input("Enter the city: ").strip()
    state = input("Enter the state (2 letters): ").strip()
    company = input("Enter the company (optional): ").strip()
    
    if not name:
        print("No name provided")
        return
    
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ SERP_API_KEY not set!")
        return
    
    # Build the "@" query that should work best
    query = f'"{name}" "@" {city} {state}'
    if company:
        query += f' {company}'
    
    print(f"\n🔍 Searching with query: {query}")
    
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": api_key,
            "num": 20  # Get more results
        })
        
        results = search.get_dict()
        organic_results = results.get('organic_results', [])
        
        print(f"\n📊 Found {len(organic_results)} results")
        
        # Look for emails with more detail
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        all_emails = []
        
        for i, result in enumerate(organic_results):
            snippet = result.get('snippet', '')
            title = result.get('title', '')
            link = result.get('link', '')
            
            # Check for emails
            text = f"{snippet} {title}"
            emails = email_pattern.findall(text)
            
            if emails or '@' in text:  # Even if regex doesn't match, @ sign is present
                print(f"\n  Result {i+1}: {link}")
                print(f"  Title: {title}")
                print(f"  Snippet: {snippet}")
                
                if emails:
                    print(f"  ✅ Emails: {emails}")
                    all_emails.extend(emails)
                else:
                    print(f"  ⚠️  Contains @ but no valid email extracted")
                    # Show where @ appears
                    at_index = text.find('@')
                    if at_index > 0:
                        start = max(0, at_index - 20)
                        end = min(len(text), at_index + 20)
                        print(f"  Context: ...{text[start:end]}...")
        
        print(f"\n📧 Total unique emails found: {len(set(all_emails))}")
        for email in set(all_emails):
            print(f"  - {email}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    """Run all debug tests"""
    print("🐛 Contact Enricher Debug Tool")
    print("==============================")
    
    # Check environment
    api_key = os.getenv("SERP_API_KEY")
    print(f"\n📋 Environment Check:")
    print(f"SERP_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    
    if not api_key:
        print("\n⚠️  Please set SERP_API_KEY first:")
        print("export SERP_API_KEY='your_serpapi_key'")
        return
    
    while True:
        print("\n\nChoose a test:")
        print("1. Test SERP API directly")
        print("2. Test GoogleSERPService")
        print("3. Check specific URL for emails")
        print("4. Test with real contact data")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            test_serp_api_direct()
        elif choice == '2':
            await test_enricher_service()
        elif choice == '3':
            check_specific_url()
        elif choice == '4':
            await test_with_real_data()
        elif choice == '5':
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main()) 