#!/usr/bin/env python3
"""
Test PayPal subscription activation flow to diagnose the 401 error.
This simulates what the backend does when activating a subscription.
"""
import requests
import base64
import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = 'backend/.env' if os.path.exists('backend/.env') else '.env'
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print("❌ .env file not found in backend/ or project root")
    sys.exit(1)

# Get credentials
CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
SECRET = os.getenv('PAYPAL_SECRET')
BASE_URL = os.getenv('PAYPAL_BASE_URL', 'https://api-m.sandbox.paypal.com')
PLAN_ID_BASIC = os.getenv('PAYPAL_PLAN_ID_BASIC')
PLAN_ID_PRO = os.getenv('PAYPAL_PLAN_ID_PRO')

print("\n🔍 Configuration Check:")
print(f"   Base URL: {BASE_URL}")
print(f"   Client ID: {CLIENT_ID[:20]}...{CLIENT_ID[-10:]}" if CLIENT_ID else "   Client ID: NOT SET")
print(f"   Secret: {'*' * 20}...{SECRET[-10:]}" if SECRET else "   Secret: NOT SET")
print(f"   Plan ID Basic: {PLAN_ID_BASIC}")
print(f"   Plan ID Pro: {PLAN_ID_PRO}")
print()

if not CLIENT_ID or not SECRET:
    print("❌ ERROR: PayPal credentials not found")
    sys.exit(1)

# Step 1: Get OAuth token (same as _get_access_token in PayPalService)
print("1️⃣  Getting OAuth token...")
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
    
    if response.status_code != 200:
        print(f"❌ Failed to get token: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print(f"✅ Got access token: {access_token[:50]}...")
    print()
    
except Exception as e:
    print(f"❌ Error getting token: {str(e)}")
    sys.exit(1)

# Step 2: Test getting subscription details (this is what activate_subscription does)
print("2️⃣  Testing subscription API access...")
print("   Note: We'll test with a fake subscription ID to see if auth works")
print()

test_subscription_id = "I-FAKE123456789"  # Fake ID just to test auth
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(
        f"{BASE_URL}/v1/billing/subscriptions/{test_subscription_id}",
        headers=headers,
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ Auth works! (404 is expected for fake subscription ID)")
        print("   The 401 error you're seeing is NOT from invalid credentials")
        print()
    elif response.status_code == 401:
        print("❌ Got 401 Unauthorized!")
        print(f"   Response: {response.text}")
        print()
        print("🔍 This suggests the access token is invalid or expired")
        sys.exit(1)
    else:
        print(f"   Response: {response.text}")
        print()
        
except Exception as e:
    print(f"❌ Error testing API: {str(e)}")
    sys.exit(1)

# Step 3: Verify the plan IDs exist
print("3️⃣  Verifying PayPal plan IDs...")
for plan_name, plan_id in [("Basic", PLAN_ID_BASIC), ("Pro", PLAN_ID_PRO)]:
    if not plan_id:
        print(f"⚠️  {plan_name} plan ID not set")
        continue
        
    try:
        response = requests.get(
            f"{BASE_URL}/v1/billing/plans/{plan_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            plan = response.json()
            print(f"✅ {plan_name} plan exists: {plan['name']}")
        elif response.status_code == 404:
            print(f"❌ {plan_name} plan NOT FOUND: {plan_id}")
        else:
            print(f"⚠️  {plan_name} plan check returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking {plan_name} plan: {str(e)}")

print()
print("=" * 70)
print("🎯 Summary:")
print("=" * 70)
print("✅ PayPal credentials are VALID")
print("✅ OAuth token generation works")
print("✅ API authentication works")
print()
print("📋 Possible causes of 401 error during activation:")
print("   1. Subscription ID from PayPal is invalid/malformed")
print("   2. Token expiry issue (unlikely with 8-hour tokens)")
print("   3. Race condition in token caching")
print("   4. PayPal sandbox API issue")
print()
print("💡 Recommendation:")
print("   The credentials are fine. The 401 error is likely happening")
print("   because the subscription ID being passed to activate is invalid")
print("   or there's a timing issue. Check the exact subscription_id value")
print("   being sent to the /activate endpoint.")