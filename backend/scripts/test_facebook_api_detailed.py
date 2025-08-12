#!/usr/bin/env python3
"""
Test Facebook automation API endpoints with detailed error reporting
"""
import requests
import json
import sys

# Get the base URL and token from command line or use defaults
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://adtv-backend.onrender.com"
TOKEN = sys.argv[2] if len(sys.argv) > 2 else None

if not TOKEN:
    print("⚠️  No token provided. Some endpoints may fail.")
    print("Usage: python test_facebook_api_detailed.py [BASE_URL] [TOKEN]")

headers = {}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

print(f"Testing API at: {BASE_URL}")
print(f"Token: {'Provided' if TOKEN else 'Not provided'}")
print("=" * 60)

def test_endpoint(method, path, data=None, params=None, description=""):
    """Test an endpoint and show detailed error information"""
    print(f"\n{method} {path}")
    if description:
        print(f"Description: {description}")
    
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"Unsupported method: {method}")
            return
        
        print(f"Status: {response.status_code}")
        
        # Try to parse JSON response
        try:
            json_data = response.json()
            print(f"Response: {json.dumps(json_data, indent=2)}")
        except:
            # If not JSON, show text
            print(f"Response (text): {response.text[:500]}")
        
        # For 500 errors, try to extract error details
        if response.status_code == 500:
            print("❌ INTERNAL SERVER ERROR - Check backend logs for details")
        
        return response
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

# Test 1: Get clients
print("\n=== TEST 1: Get Facebook Clients ===")
response = test_endpoint("GET", "/api/facebook-automation/clients")

# Extract client ID if available
client_id = None
if response and response.status_code == 200:
    try:
        clients = response.json()
        if clients and len(clients) > 0:
            client_id = clients[0]['id']
            print(f"✅ Found client ID: {client_id}")
    except:
        pass

# Test 2: Get posts (with client_id if available)
print("\n=== TEST 2: Get Facebook Posts ===")
params = {"limit": 10}
if client_id:
    params["client_id"] = client_id
    print(f"Using client_id: {client_id}")

response = test_endpoint("GET", "/api/facebook-automation/posts", params=params)

# Test 3: Get campaigns
print("\n=== TEST 3: Get Facebook Campaigns ===")
params = {}
if client_id:
    params["client_id"] = client_id

response = test_endpoint("GET", "/api/facebook-automation/campaigns", params=params)

# Test 4: Get analytics
print("\n=== TEST 4: Get Facebook Analytics ===")
data = {
    "timeframe": "last_7_days"
}
if client_id:
    data["client_ids"] = [client_id]

response = test_endpoint("POST", "/api/facebook-automation/analytics", data=data)

print("\n=== SUMMARY ===")
print("If you're seeing 500 errors, check the backend logs in Render.")
print("Common issues:")
print("- Database connection problems")
print("- Missing tables or data")
print("- Enum value mismatches")
print("- Permission issues") 