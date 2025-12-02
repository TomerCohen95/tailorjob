#!/bin/bash
# Script to show environment variables that need to be set on Render

echo "=== Environment Variables Needed on Render ==="
echo ""
echo "Based on your local backend/.env file:"
echo ""

# Read backend/.env and format for Render
grep -v '^#' backend/.env | grep -v '^$' | while IFS='=' read -r key value; do
    # Skip if empty
    if [ -z "$key" ]; then
        continue
    fi
    
    echo "Key: $key"
    echo "Value: ${value:0:50}..." # Show first 50 chars for security
    echo "---"
done

echo ""
echo "=== Instructions ==="
echo "1. Go to https://dashboard.render.com"
echo "2. Select your backend service"
echo "3. Go to Environment tab"
echo "4. Add/Update each variable listed above"
echo ""
echo "=== Missing Variables to Add ==="
echo "These new variables were added for PayPal integration:"
echo "- PAYPAL_PLAN_ID_BASIC"
echo "- PAYPAL_PLAN_ID_PRO"
echo "- FRONTEND_URL (optional - auto-detects if not set)"