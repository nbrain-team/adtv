#!/usr/bin/env python3
"""Quick test of SERP API functionality"""
import os
from serpapi import GoogleSearch

def test_serp_basic():
    """Test basic SERP API functionality"""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ SERP_API_KEY not set!")
        return False
    
    print("✅ SERP_API_KEY is set")
    
    # Test a simple search
    query = '"John Smith" "@" Huntsville AL'
    print(f"\n🔍 Testing query: {query}")
    
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": api_key,
            "num": 5
        })
        
        results = search.get_dict()
        organic_results = results.get('organic_results', [])
        
        print(f"✅ Got {len(organic_results)} results")
        
        # Show first result
        if organic_results:
            first = organic_results[0]
            print(f"\nFirst result:")
            print(f"  Title: {first.get('title', 'N/A')}")
            print(f"  Link: {first.get('link', 'N/A')}")
            print(f"  Snippet: {first.get('snippet', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing SERP API Connection")
    print("="*50)
    
    if test_serp_basic():
        print("\n✅ SERP API is working!")
    else:
        print("\n❌ SERP API test failed") 