#!/bin/bash
# Trigger GitHub Actions deployment for backend

echo "🚀 Triggering backend deployment..."

# Make a trivial change to trigger deployment
git commit --allow-empty -m "trigger: Force backend redeployment with monitoring"
git push origin main

echo "✅ Deployment triggered! Monitor at:"
echo "   https://github.com/TomerCohen95/tailorjob/actions"
echo ""
echo "⏳ Waiting 3 minutes for deployment to complete..."
sleep 180

echo ""
echo "🧪 Testing /metrics endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://tailorjob-api.azurewebsites.net/metrics)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! /metrics endpoint is live"
    echo ""
    curl -s https://tailorjob-api.azurewebsites.net/metrics | head -20
else
    echo "❌ Endpoint returned HTTP $HTTP_CODE"
    echo "Check deployment logs at: https://github.com/TomerCohen95/tailorjob/actions"
fi