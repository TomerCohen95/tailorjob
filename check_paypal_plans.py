#!/usr/bin/env python3
"""
Check what PayPal v2 subscription plans exist in your account.
"""
import requests
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables - try both locations
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('backend/.env'):
    load_dotenv('backend/.env')

# Get PayPal credentials
CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
SECRET = os.getenv('PAYPAL_SECRET')
BASE_URL = os.getenv('PAYPAL_BASE_URL', 'https://api-m.sandbox.paypal.com')

if not CLIENT_ID or not SECRET:
    print("❌ ERROR: PAYPAL_CLIENT_ID or PAYPAL_SECRET not found in backend/.env")
    print("   Make sure backend/.env has these variables set")
    exit(1)

print("🔍 Checking PayPal v2 Subscription Plans...")
print(f"📍 Base URL: {BASE_URL}")
print(f"🔑 Client ID: {CLIENT_ID[:20]}...")
print()

# Step 1: Get access token
print("1️⃣ Getting OAuth token...")
auth = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {"grant_type": "client_credentials"}

response = requests.post(f"{BASE_URL}/v1/oauth2/token", headers=headers, data=data)
if response.status_code != 200:
    print(f"❌ Failed to get token: {response.text}")
    exit(1)

token = response.json()["access_token"]
print(f"✅ Got access token: {token[:20]}...")
print()

# Step 2: List products (required for v2 plans)
print("2️⃣ Listing Products...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(f"{BASE_URL}/v1/catalogs/products", headers=headers)
if response.status_code == 200:
    products = response.json().get('products', [])
    print(f"✅ Found {len(products)} products")
    for product in products:
        print(f"   📦 Product: {product['id']} - {product['name']}")
else:
    print(f"❌ Failed to list products: {response.text}")
    products = []
print()

# Step 3: List billing plans (v2)
print("3️⃣ Listing v2 Billing Plans...")
response = requests.get(f"{BASE_URL}/v1/billing/plans", headers=headers)

if response.status_code == 200:
    result = response.json()
    plans = result.get('plans', [])
    print(f"✅ Found {len(plans)} v2 billing plans")
    print()
    
    if plans:
        for plan in plans:
            print(f"📋 Plan ID: {plan['id']}")
            print(f"   Name: {plan.get('name', 'N/A')}")
            print(f"   Status: {plan.get('status', 'N/A')}")
            print(f"   Product ID: {plan.get('product_id', 'N/A')}")
            
            # Show billing cycles
            billing_cycles = plan.get('billing_cycles', [])
            for cycle in billing_cycles:
                tenure = cycle.get('tenure_type', 'N/A')
                frequency = cycle.get('frequency', {})
                interval = frequency.get('interval_count', 'N/A')
                unit = frequency.get('interval_unit', 'N/A')
                pricing = cycle.get('pricing_scheme', {}).get('fixed_price', {})
                price = pricing.get('value', 'N/A')
                currency = pricing.get('currency_code', 'N/A')
                
                print(f"   💰 {tenure}: {price} {currency} every {interval} {unit}")
            print()
    else:
        print("⚠️  No v2 billing plans found!")
        print()
        print("💡 To create v2 plans, you need to:")
        print("   1. Create a Product first")
        print("   2. Create a Plan linked to that Product")
        print("   3. Use those Plan IDs in your code")
else:
    print(f"❌ Failed to list plans: {response.status_code}")
    print(f"   Response: {response.text}")

print()
print("=" * 60)
print("📝 Summary:")
print(f"   Products: {len(products)}")
print(f"   v2 Plans: {len(plans) if response.status_code == 200 else 'ERROR'}")
print("=" * 60)