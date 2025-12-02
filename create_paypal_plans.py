#!/usr/bin/env python3
"""
Create PayPal v2 subscription products and plans for TailorJob.
"""
import requests
import base64
import json
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

if not CLIENT_ID or not SECRET:
    print("❌ ERROR: PayPal credentials not found")
    exit(1)

print("🚀 Creating PayPal v2 Subscription Plans...")
print()

# Get access token
print("1️⃣ Getting OAuth token...")
auth = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
response = requests.post(f"{BASE_URL}/v1/oauth2/token", headers=headers, data={"grant_type": "client_credentials"})
token = response.json()["access_token"]
print(f"✅ Got token")
print()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Step 1: Create Product
print("2️⃣ Creating Product...")
product_data = {
    "name": "TailorJob Subscription",
    "description": "Professional CV tailoring service with AI-powered matching",
    "type": "SERVICE",
    "category": "SOFTWARE",
    "image_url": "https://tailorjob.vercel.app/logo.png",
    "home_url": "https://tailorjob.vercel.app"
}

response = requests.post(f"{BASE_URL}/v1/catalogs/products", headers=headers, json=product_data)
if response.status_code == 201:
    product = response.json()
    product_id = product['id']
    print(f"✅ Product created: {product_id}")
    print(f"   Name: {product['name']}")
else:
    print(f"❌ Failed to create product: {response.text}")
    exit(1)
print()

# Step 2: Create Basic Plan ($9.99/month)
print("3️⃣ Creating Basic Plan ($9.99/month)...")
basic_plan_data = {
    "product_id": product_id,
    "name": "TailorJob Basic Monthly",
    "description": "Basic plan with 10 CV uploads, 50 matches, and 5 tailored CVs per month",
    "billing_cycles": [
        {
            "frequency": {
                "interval_unit": "MONTH",
                "interval_count": 1
            },
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,  # 0 = infinite
            "pricing_scheme": {
                "fixed_price": {
                    "value": "9.99",
                    "currency_code": "USD"
                }
            }
        }
    ],
    "payment_preferences": {
        "auto_bill_outstanding": True,
        "setup_fee": {
            "value": "0",
            "currency_code": "USD"
        },
        "setup_fee_failure_action": "CONTINUE",
        "payment_failure_threshold": 3
    }
}

response = requests.post(f"{BASE_URL}/v1/billing/plans", headers=headers, json=basic_plan_data)
if response.status_code == 201:
    basic_plan = response.json()
    basic_plan_id = basic_plan['id']
    print(f"✅ Basic Plan created: {basic_plan_id}")
    
    # Activate the plan
    response = requests.post(f"{BASE_URL}/v1/billing/plans/{basic_plan_id}/activate", headers=headers)
    if response.status_code == 204:
        print(f"✅ Basic Plan activated")
    else:
        print(f"⚠️  Failed to activate plan: {response.text}")
else:
    print(f"❌ Failed to create Basic plan: {response.text}")
    exit(1)
print()

# Step 3: Create Pro Plan ($19.99/month)
print("4️⃣ Creating Pro Plan ($19.99/month)...")
pro_plan_data = {
    "product_id": product_id,
    "name": "TailorJob Pro Monthly",
    "description": "Pro plan with unlimited CV uploads, matches, and tailored CVs",
    "billing_cycles": [
        {
            "frequency": {
                "interval_unit": "MONTH",
                "interval_count": 1
            },
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,  # 0 = infinite
            "pricing_scheme": {
                "fixed_price": {
                    "value": "19.99",
                    "currency_code": "USD"
                }
            }
        }
    ],
    "payment_preferences": {
        "auto_bill_outstanding": True,
        "setup_fee": {
            "value": "0",
            "currency_code": "USD"
        },
        "setup_fee_failure_action": "CONTINUE",
        "payment_failure_threshold": 3
    }
}

response = requests.post(f"{BASE_URL}/v1/billing/plans", headers=headers, json=pro_plan_data)
if response.status_code == 201:
    pro_plan = response.json()
    pro_plan_id = pro_plan['id']
    print(f"✅ Pro Plan created: {pro_plan_id}")
    
    # Activate the plan
    response = requests.post(f"{BASE_URL}/v1/billing/plans/{pro_plan_id}/activate", headers=headers)
    if response.status_code == 204:
        print(f"✅ Pro Plan activated")
    else:
        print(f"⚠️  Failed to activate plan: {response.text}")
else:
    print(f"❌ Failed to create Pro plan: {response.text}")
    exit(1)
print()

# Summary
print("=" * 70)
print("🎉 SUCCESS! Plans created and activated")
print("=" * 70)
print()
print("📋 Update your backend/app/services/paypal_service.py with these IDs:")
print()
print("PLAN_IDS = {")
print(f"    'basic_monthly': '{basic_plan_id}',")
print(f"    'pro_monthly': '{pro_plan_id}',")
print("}")
print()
print("💡 Or update backend/.env:")
print(f"PAYPAL_PLAN_ID_BASIC={basic_plan_id}")
print(f"PAYPAL_PLAN_ID_PRO={pro_plan_id}")
print()