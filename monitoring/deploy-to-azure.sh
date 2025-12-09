#!/bin/bash

# TailorJob Monitoring Stack - Azure Container Instances Deployment
# Deploys to Azure using your existing resource group: tailorjob-rg

set -e

echo "🚀 TailorJob Monitoring - Azure Deployment"
echo "==========================================="
echo ""

# Configuration
RESOURCE_GROUP="tailorjob-rg"
LOCATION="eastus"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
ACR_NAME="tailorjobacr"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Subscription: $SUBSCRIPTION_ID"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo ""
    echo "Please create .env file with:"
    echo "  DISCORD_WEBHOOK_URL=your-webhook-url"
    echo "  GRAFANA_ADMIN_PASSWORD=your-strong-password"
    echo ""
    echo "Example:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "❌ Error: DISCORD_WEBHOOK_URL not set in .env"
    exit 1
fi

if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    echo "❌ Error: GRAFANA_ADMIN_PASSWORD not set in .env"
    exit 1
fi

echo "✅ Environment variables validated"
echo ""

# Check if logged in to Azure
echo "🔐 Checking Azure login..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged in to Azure"
    echo "Please run: az login"
    exit 1
fi
echo "✅ Logged in to Azure"
echo ""

# Check if resource group exists
echo "📦 Checking resource group..."
if ! az group show --name $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "❌ Resource group $RESOURCE_GROUP not found"
    echo "Creating resource group..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
fi
echo "✅ Resource group exists"
echo ""

# Create Azure File Share for persistent storage
echo "💾 Creating Azure File Share for persistent data..."
STORAGE_ACCOUNT="tailorjobmonitoring"
FILE_SHARE_PROMETHEUS="prometheus-data"
FILE_SHARE_GRAFANA="grafana-data"

# Create storage account if it doesn't exist
if ! az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "Creating storage account: $STORAGE_ACCOUNT"
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2
fi

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query '[0].value' -o tsv)

# Create file shares
for SHARE in $FILE_SHARE_PROMETHEUS $FILE_SHARE_GRAFANA; do
    if ! az storage share exists --name $SHARE --account-name $STORAGE_ACCOUNT --account-key $STORAGE_KEY --query exists -o tsv | grep -q true; then
        echo "Creating file share: $SHARE"
        az storage share create \
            --name $SHARE \
            --account-name $STORAGE_ACCOUNT \
            --account-key $STORAGE_KEY
    fi
done

echo "✅ Storage configured"
echo ""

# Get ACR credentials
echo "🔐 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
echo "✅ ACR credentials retrieved"
echo ""

# Deploy Prometheus
echo "📊 Deploying Prometheus..."
PROMETHEUS_FQDN="tailorjob-prometheus-$(date +%s)"

az container create \
    --resource-group $RESOURCE_GROUP \
    --name tailorjob-prometheus \
    --image ${ACR_LOGIN_SERVER}/prometheus:latest \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --dns-name-label $PROMETHEUS_FQDN \
    --ports 9090 \
    --cpu 1 \
    --memory 1 \
    --os-type Linux \
    --azure-file-volume-account-name $STORAGE_ACCOUNT \
    --azure-file-volume-account-key $STORAGE_KEY \
    --azure-file-volume-share-name $FILE_SHARE_PROMETHEUS \
    --azure-file-volume-mount-path /prometheus \
    --command-line "prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus --web.enable-lifecycle" \
    --restart-policy Always \
    --location $LOCATION

PROMETHEUS_URL="http://${PROMETHEUS_FQDN}.${LOCATION}.azurecontainer.io:9090"
echo "✅ Prometheus deployed: $PROMETHEUS_URL"
echo ""

# Deploy Grafana
echo "📈 Deploying Grafana..."
GRAFANA_FQDN="tailorjob-grafana-$(date +%s)"

az container create \
    --resource-group $RESOURCE_GROUP \
    --name tailorjob-grafana \
    --image ${ACR_LOGIN_SERVER}/grafana:latest \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --dns-name-label $GRAFANA_FQDN \
    --ports 3000 \
    --cpu 1 \
    --memory 1 \
    --os-type Linux \
    --environment-variables \
        GF_SECURITY_ADMIN_USER=admin \
        GF_SECURITY_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" \
        GF_INSTALL_PLUGINS=grafana-piechart-panel \
        GF_USERS_ALLOW_SIGN_UP=false \
    --azure-file-volume-account-name $STORAGE_ACCOUNT \
    --azure-file-volume-account-key $STORAGE_KEY \
    --azure-file-volume-share-name $FILE_SHARE_GRAFANA \
    --azure-file-volume-mount-path /var/lib/grafana \
    --restart-policy Always \
    --location $LOCATION

GRAFANA_URL="http://${GRAFANA_FQDN}.${LOCATION}.azurecontainer.io:3000"
echo "✅ Grafana deployed: $GRAFANA_URL"
echo ""

# Deploy Alertmanager
echo "🔔 Deploying Alertmanager..."
ALERTMANAGER_FQDN="tailorjob-alertmanager-$(date +%s)"

az container create \
    --resource-group $RESOURCE_GROUP \
    --name tailorjob-alertmanager \
    --image ${ACR_LOGIN_SERVER}/alertmanager:latest \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --dns-name-label $ALERTMANAGER_FQDN \
    --ports 9093 \
    --cpu 0.5 \
    --memory 0.5 \
    --os-type Linux \
    --command-line "alertmanager --config.file=/etc/alertmanager/alertmanager.yml --storage.path=/alertmanager" \
    --restart-policy Always \
    --location $LOCATION

ALERTMANAGER_URL="http://${ALERTMANAGER_FQDN}.${LOCATION}.azurecontainer.io:9093"
echo "✅ Alertmanager deployed: $ALERTMANAGER_URL"
echo ""

# Deploy Discord Webhook Forwarder
echo "💬 Deploying Discord Webhook Forwarder..."
DISCORD_FQDN="tailorjob-discord-$(date +%s)"

# Note: This requires the Docker image to be built and pushed to a registry first
# For now, we'll deploy a simple placeholder
echo "⚠️  Discord forwarder requires custom Docker image"
echo "    You'll need to:"
echo "    1. Build the image: docker build -f Dockerfile.discord-forwarder -t tailorjob-discord-forwarder ."
echo "    2. Push to Azure Container Registry or Docker Hub"
echo "    3. Update this script with the image URL"
echo ""

# Wait for containers to be ready
echo "⏳ Waiting for containers to start..."
sleep 30

# Check container statuses
echo ""
echo "🏥 Checking container health..."

for CONTAINER in tailorjob-prometheus tailorjob-grafana tailorjob-alertmanager; do
    STATUS=$(az container show \
        --resource-group $RESOURCE_GROUP \
        --name $CONTAINER \
        --query 'instanceView.state' -o tsv)
    
    if [ "$STATUS" = "Running" ]; then
        echo "✅ $CONTAINER: Running"
    else
        echo "⚠️  $CONTAINER: $STATUS"
    fi
done

echo ""
echo "✨ Deployment Complete!"
echo ""
echo "═══════════════════════════════════════════════════"
echo "📊 Access Your Monitoring Stack:"
echo "═══════════════════════════════════════════════════"
echo ""
echo "🔹 Grafana Dashboard:"
echo "   URL:      $GRAFANA_URL"
echo "   Username: admin"
echo "   Password: (from your .env file)"
echo ""
echo "🔹 Prometheus:"
echo "   URL: $PROMETHEUS_URL"
echo ""
echo "🔹 Alertmanager:"
echo "   URL: $ALERTMANAGER_URL"
echo ""
echo "═══════════════════════════════════════════════════"
echo "📝 Next Steps:"
echo "═══════════════════════════════════════════════════"
echo ""
echo "1. Open Grafana: $GRAFANA_URL"
echo "2. Login with admin / your-password"
echo "3. Add Prometheus data source:"
echo "   - Configuration → Data Sources → Add data source"
echo "   - Choose Prometheus"
echo "   - URL: $PROMETHEUS_URL"
echo "   - Click 'Save & Test'"
echo ""
echo "4. Import dashboard:"
echo "   - + → Import"
echo "   - Upload grafana-dashboards/tailorjob-dashboard.json"
echo ""
echo "5. Update backend to point to Prometheus:"
echo "   - Update prometheus.yml with your API URL"
echo "   - Restart containers"
echo ""
echo "═══════════════════════════════════════════════════"
echo "💰 Cost Estimate:"
echo "═══════════════════════════════════════════════════"
echo ""
echo "3 containers × ~\$10/month = ~\$30/month"
echo "Storage: ~\$1/month"
echo "Total: ~\$31/month (from your \$150 Azure credits)"
echo ""
echo "═══════════════════════════════════════════════════"
echo "🔧 Management Commands:"
echo "═══════════════════════════════════════════════════"
echo ""
echo "# View container logs"
echo "az container logs --resource-group $RESOURCE_GROUP --name tailorjob-grafana"
echo ""
echo "# Restart a container"
echo "az container restart --resource-group $RESOURCE_GROUP --name tailorjob-grafana"
echo ""
echo "# Delete all monitoring containers"
echo "az container delete --resource-group $RESOURCE_GROUP --name tailorjob-prometheus --yes"
echo "az container delete --resource-group $RESOURCE_GROUP --name tailorjob-grafana --yes"
echo "az container delete --resource-group $RESOURCE_GROUP --name tailorjob-alertmanager --yes"
echo ""
echo "═══════════════════════════════════════════════════"
echo ""
echo "🎉 Monitoring stack is now running on Azure!"
echo ""

# Save URLs to file
cat > deployment-urls.txt <<EOF
# TailorJob Monitoring URLs
# Generated: $(date)

Grafana Dashboard: $GRAFANA_URL
Username: admin
Password: (see .env file)

Prometheus: $PROMETHEUS_URL
Alertmanager: $ALERTMANAGER_URL

# Azure Container Names
Resource Group: $RESOURCE_GROUP
Prometheus Container: tailorjob-prometheus
Grafana Container: tailorjob-grafana
Alertmanager Container: tailorjob-alertmanager

# Storage
Storage Account: $STORAGE_ACCOUNT
File Shares: $FILE_SHARE_PROMETHEUS, $FILE_SHARE_GRAFANA
EOF

echo "📄 URLs saved to: deployment-urls.txt"
echo ""