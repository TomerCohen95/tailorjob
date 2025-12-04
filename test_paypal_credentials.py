#!/usr/bin/env python3
"""
Test PayPal credentials by attempting to get an OAuth token.
"""
import requests
import base64
import os
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('backend/.env'):
    load_dotenv('backend/.env')

CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
SECRET = os.getenv('PAYPAL_SECRET')
BASE_URL = os.getenv('PAYPAL_BASE_URL', 'https://api-m.sandbox.paypal.com')

print("🔍 Testing PayPal Credentials...")
print(f"   Base URL: {BASE_URL}")
print(f"   Client ID: {CLIENT_ID[:20]}...{CLIENT_ID[-10:]}" if CLIENT_ID else "   Client ID: NOT SET")
print()

if not CLIENT_ID or not SECRET:
    print("❌ ERROR: PayPal credentials not found in environment")
    print("   Make sure PAYPAL_CLIENT_ID and PAYPAL_SECRET are set in backend/.env")
    exit(1)

# Attempt to get OAuth token
print("📡 Requesting OAuth token from PayPal...")
auth = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}

try:
    response = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        headers=headers,
        data={"grant_type": "client_credentials"},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ SUCCESS: Credentials are valid!")
        print(f"   Access Token: {token_data['access_token'][:50]}...")
        print(f"   Expires In: {token_data.get('expires_in', 'N/A')} seconds")
        print(f"   Token Type: {token_data.get('token_type', 'N/A')}")
        exit(0)
    elif response.status_code == 401:
        print("❌ FAIL: 401 Unauthorized")
        print("   The credentials are INVALID or REVOKED")
        print()
        print("Response:")
        print(response.text)
        print()
        print("📝 Next Steps:")
        print("   1. Go to https://developer.paypal.com/")
        print("   2. Navigate to: Dashboard → My Apps & Credentials")
        print("   3. Under 'Sandbox', get new Client ID and Secret")
        print("   4. Update backend/.env with new credentials")
        exit(1)
    else:
        print(f"❌ FAIL: Unexpected response {response.status_code}")
        print()
        print("Response:")
        print(response.text)
        exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"❌ ERROR: Network request failed")
    print(f"   {str(e)}")
    exit(1)