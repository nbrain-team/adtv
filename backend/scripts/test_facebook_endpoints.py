"""
Test Facebook automation endpoints
"""

import requests
import sys

def test_endpoints(base_url, token=None):
    """Test if Facebook automation endpoints are accessible"""
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    endpoints = [
        '/api/facebook-automation/clients',
        '/api/facebook-automation/stats',
        '/api/facebook-automation/campaigns'
    ]
    
    print(f"Testing endpoints at: {base_url}")
    print("-" * 50)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
    
    print("-" * 50)

if __name__ == "__main__":
    # Test production
    prod_url = "https://adtv-backend.onrender.com"
    
    # Get token from command line if provided
    token = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not token:
        print("⚠️  No auth token provided. Pass it as first argument.")
        print("   You can get your token from browser's localStorage")
        print("   In browser console: localStorage.getItem('token')")
        print()
    
    test_endpoints(prod_url, token) 