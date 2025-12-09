#!/bin/bash

# Update Prometheus configuration on Azure Container Instance
# Run this after pushing backend code to enable monitoring

set -e

echo "📊 Updating Prometheus Configuration"
echo "====================================="
echo ""

RESOURCE_GROUP="tailorjob-rg"
STORAGE_ACCOUNT="tailorjobmonitoring"
CONTAINER_NAME="tailorjob-prometheus"

# Get storage account key
echo "🔑 Getting storage credentials..."
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query '[0].value' -o tsv)

# Upload prometheus.yml to Azure Files
echo "📤 Uploading prometheus.yml..."
az storage file upload \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --share-name prometheus-data \
    --source ./prometheus.yml \
    --path prometheus.yml \
    --no-progress

echo "✅ Configuration uploaded"
echo ""

# Restart Prometheus to reload config
echo "🔄 Restarting Prometheus..."
az container restart \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME

echo "✅ Prometheus restarted"
echo ""
echo "⏳ Wait 30 seconds for Prometheus to start scraping..."
echo ""
echo "Then check:"
echo "  http://tailorjob-prometheus-1765272255.eastus.azurecontainer.io:9090/targets"
echo ""
echo "You should see 'tailorjob-api' as UP (green)"