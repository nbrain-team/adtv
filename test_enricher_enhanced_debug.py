#!/usr/bin/env python3
"""
Enhanced debug for Contact Enricher - shows exactly what's happening
"""
import os
import sys
import asyncio
import re
from serpapi import GoogleSearch
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def test_enrichment_step_by_step():
    """Test enrichment with detailed step-by-step output"""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ SERP_API_KEY not set!")
        return
    
    # Get test data
    print("Enter contact details to test:")
    name = input("Name: ").strip()
    city = input("City: ").strip()
    state = input("State (2 letters): ").strip()
    company = input("Company (optional): ").strip() or None
    
    print("\n" + "="*60)
    print("🔍 STEP-BY-STEP ENRICHMENT DEBUG")
    print("="*60)
    
    # Step 1: Build queries
    print("\n📌 Step 1: Building search queries")
    queries = []
    
    # Most effective query with @
    if name and city:
        query1 = f'"{name}" "@" {city} {state}'
        if company:
            query1 += f' {company}'
        queries.append(query1)
        print(f"  Query 1: {query1}")
    
    # Additional queries
    if city:
        query2 = f'"{name}" realtor {city} email phone'
        queries.append(query2)
        print(f"  Query 2: {query2}")
        
        query3 = f'"{name}" real estate agent {city} contact information'
        queries.append(query3)
        print(f"  Query 3: {query3}")
    
    # Step 2: Execute searches and analyze results
    all_emails = []
    all_phones = []
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    for i, query in enumerate(queries[:3]):  # Test first 3 queries
        print(f"\n📌 Step 2.{i+1}: Executing search")
        print(f"  Query: {query}")
        
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": api_key,
                "num": 10
            })
            
            results = search.get_dict()
            organic_results = results.get('organic_results', [])
            
            print(f"  ✅ Got {len(organic_results)} results")
            
            # Analyze each result
            for j, result in enumerate(organic_results[:5]):  # First 5 results
                snippet = result.get('snippet', '')
                title = result.get('title', '')
                link = result.get('link', '')
                full_text = f"{snippet} {title}"
                
                print(f"\n  Result {j+1}:")
                print(f"    URL: {link}")
                print(f"    Title: {title[:50]}...")
                print(f"    Snippet: {snippet[:100]}...")
                
                # Look for emails
                raw_emails = email_pattern.findall(full_text)
                
                if raw_emails:
                    print(f"    📧 Raw emails found: {raw_emails}")
                    
                    # Test email validation
                    for email in raw_emails:
                        is_valid = test_email_validation(email, name)
                        if is_valid:
                            print(f"       ✅ {email} - VALID for {name}")
                            all_emails.append(email)
                        else:
                            print(f"       ❌ {email} - REJECTED (doesn't match name)")
                elif '@' in full_text:
                    print(f"    ⚠️  Contains @ but no valid email extracted")
                    # Find @ context
                    at_pos = full_text.find('@')
                    start = max(0, at_pos - 30)
                    end = min(len(full_text), at_pos + 30)
                    print(f"       Context: ...{full_text[start:end]}...")
                else:
                    print(f"    ❌ No @ symbol found")
                    
        except Exception as e:
            print(f"  ❌ Search failed: {str(e)}")
    
    # Step 3: Summary
    print(f"\n📌 Step 3: Summary")
    print(f"  Total unique emails found: {len(set(all_emails))}")
    for email in set(all_emails):
        print(f"    - {email}")
    
    # Step 4: Test website scraping if available
    if company:
        print(f"\n📌 Step 4: Testing website search")
        website_query = f'site:{company.lower().replace(" ", "")}.com contact email phone'
        print(f"  Query: {website_query}")
        # ... (would implement website search here)

def test_email_validation(email: str, name: str) -> bool:
    """Test if email would be considered valid"""
    email_lower = email.lower()
    name_parts = name.lower().split()
    
    # Check generic patterns
    generic_patterns = ['info@', 'contact@', 'admin@', 'support@', 'noreply@', 'sales@', 'office@']
    is_generic = any(pattern in email_lower for pattern in generic_patterns)
    
    # Check if name appears in email
    name_in_email = any(part in email_lower for part in name_parts if len(part) > 2)
    
    # Real estate domains
    real_estate_domains = ['remax', 'kw.com', 'coldwellbanker', 'century21', 'sothebys', 'compass.com', 'exp', 'bhhsca']
    is_real_estate = any(domain in email_lower for domain in real_estate_domains)
    
    print(f"       Validation details:")
    print(f"         - Is generic: {is_generic}")
    print(f"         - Name in email: {name_in_email}")
    print(f"         - Real estate domain: {is_real_estate}")
    
    # Logic from the service
    if is_generic and not name_in_email:
        return False
    
    if name_in_email:
        return True
        
    if is_real_estate:
        return True
        
    return True  # Default to accepting

async def test_specific_person():
    """Test with a specific person where you know the email exists"""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ SERP_API_KEY not set!")
        return
    
    print("\n🎯 Testing with specific person")
    print("="*60)
    
    # Provide the exact search string you used manually
    manual_query = input("Enter the EXACT search query you used in Google: ").strip()
    expected_email = input("Enter the email you found manually: ").strip()
    
    print(f"\n🔍 Searching: {manual_query}")
    
    try:
        search = GoogleSearch({
            "q": manual_query,
            "api_key": api_key,
            "num": 20
        })
        
        results = search.get_dict()
        organic_results = results.get('organic_results', [])
        
        print(f"\n📊 Got {len(organic_results)} results from SERP API")
        
        # Look for the expected email
        found = False
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        for i, result in enumerate(organic_results):
            snippet = result.get('snippet', '')
            title = result.get('title', '')
            link = result.get('link', '')
            
            if expected_email.lower() in snippet.lower() or expected_email.lower() in title.lower():
                found = True
                print(f"\n✅ FOUND! Expected email appears in result {i+1}")
                print(f"  URL: {link}")
                print(f"  Title: {title}")
                print(f"  Snippet: {snippet}")
                
                # Check if regex would extract it
                emails = email_pattern.findall(f"{snippet} {title}")
                if expected_email in emails:
                    print(f"  ✅ Regex successfully extracts the email")
                else:
                    print(f"  ❌ Regex failed to extract the email")
                    print(f"  All extracted: {emails}")
                break
        
        if not found:
            print(f"\n❌ Expected email '{expected_email}' not found in any results")
            print("\nShowing first 3 results for comparison:")
            for i, result in enumerate(organic_results[:3]):
                print(f"\nResult {i+1}:")
                print(f"  URL: {result.get('link', 'N/A')}")
                print(f"  Snippet: {result.get('snippet', 'N/A')[:200]}...")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    """Run debug tests"""
    print("🐛 Contact Enricher Enhanced Debug")
    print("==================================")
    
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("\n❌ SERP_API_KEY not set!")
        print("Set it with: export SERP_API_KEY='your_serpapi_key'")
        return
    
    print(f"\n✅ SERP_API_KEY is set")
    
    while True:
        print("\n\nChoose a test:")
        print("1. Test enrichment step-by-step")
        print("2. Test with specific person (where you found email manually)")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            await test_enrichment_step_by_step()
        elif choice == '2':
            await test_specific_person()
        elif choice == '3':
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main()) 