#!/usr/bin/env python3
"""
Verify PayPal plan IDs exist and are accessible with the configured credentials.
"""

import os
import requests
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# PayPal config
CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
SECRET = os.getenv('PAYPAL_SECRET')
BASE_URL = os.getenv('PAYPAL_BASE_URL', 'https://api-m.sandbox.paypal.com')
PLAN_ID_BASIC = os.getenv('PAYPAL_PLAN_ID_BASIC')
PLAN_ID_PRO = os.getenv('PAYPAL_PLAN_ID_PRO')

def get_access_token():
    """Get PayPal OAuth token"""
    url = f"{BASE_URL}/v1/oauth2/token"
    auth = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    
    print(f"🔑 Authenticating with PayPal ({BASE_URL})...")
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code != 200:
        print(f"❌ Auth failed: {response.status_code}")
        print(response.text)
        return None
    
    print("✅ Authentication successful")
    return response.json()["access_token"]

def check_plan(token, plan_id, plan_name):
    """Check if a plan exists and is accessible"""
    url = f"{BASE_URL}/v1/billing/plans/{plan_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📋 Checking {plan_name} plan: {plan_id}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        plan = response.json()
        print(f"✅ Plan exists and is accessible")
        print(f"   Name: {plan.get('name')}")
        print(f"   Status: {plan.get('status')}")
        print(f"   Description: {plan.get('description', 'N/A')}")
        
        # Check billing cycles
        if 'billing_cycles' in plan:
            for cycle in plan['billing_cycles']:
                pricing = cycle.get('pricing_scheme', {}).get('fixed_price', {})
                print(f"   Price: {pricing.get('value')} {pricing.get('currency_code')}")
        
        return True
    elif response.status_code == 404:
        print(f"❌ Plan NOT FOUND (404)")
        print(f"   This plan ID doesn't exist in your PayPal account")
        return False
    elif response.status_code == 401:
        print(f"❌ Unauthorized (401)")
        print(f"   Your credentials may be invalid")
        return False
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

def test_create_subscription(token, plan_id):
    """Test creating a subscription (without completing it)"""
    url = f"{BASE_URL}/v1/billing/subscriptions"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "plan_id": plan_id,
        "application_context": {
            "brand_name": "TailorJob Test",
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        }
    }
    
    print(f"\n🧪 Testing subscription creation with plan {plan_id}...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Subscription can be created")
        print(f"   Subscription ID: {result.get('id')}")
        print(f"   Status: {result.get('status')}")
        
        # Find approval URL
        for link in result.get('links', []):
            if link.get('rel') == 'approve':
                print(f"   Approval URL: {link.get('href')}")
        
        return True
    else:
        print(f"❌ Subscription creation failed: {response.status_code}")
        print(response.text)
        return False

def main():
    print("=" * 60)
    print("PayPal Plan Verification Tool")
    print("=" * 60)
    
    print(f"\n🔧 Configuration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Client ID: {CLIENT_ID[:20]}...")
    print(f"   Basic Plan ID: {PLAN_ID_BASIC}")
    print(f"   Pro Plan ID: {PLAN_ID_PRO}")
    
    # Get auth token
    token = get_access_token()
    if not token:
        print("\n❌ Failed to authenticate. Check your credentials.")
        return
    
    # Check both plans
    basic_ok = check_plan(token, PLAN_ID_BASIC, "Basic")
    pro_ok = check_plan(token, PLAN_ID_PRO, "Pro")
    
    # Test subscription creation if plans exist
    if basic_ok:
        test_create_subscription(token, PLAN_ID_BASIC)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if basic_ok and pro_ok:
        print("✅ All plans are valid and accessible")
        print("\n💡 Your sandbox setup is correct!")
        print("   The error might be:")
        print("   1. Authentication issue in production")
        print("   2. CORS/network issue")
        print("   3. Frontend sending wrong parameters")
    else:
        print("❌ Some plans are not accessible")
        print("\n💡 Next steps:")
        print("   1. Create the missing plans using create_paypal_plans.py")
        print("   2. Update your .env files with the new plan IDs")
        print("   3. Redeploy to Azure with updated configuration")

if __name__ == "__main__":
    main()