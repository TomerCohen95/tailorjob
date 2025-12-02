#!/bin/bash

# Azure Deployment Helper Script for TailorJob Backend
# This script helps you deploy your FastAPI backend to Azure App Service

set -e  # Exit on any error

echo "🚀 TailorJob Azure Deployment Helper"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed${NC}"
    echo "Install it with: brew install azure-cli"
    exit 1
fi

echo -e "${GREEN}✓ Azure CLI found${NC}"

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure${NC}"
    echo "Logging in..."
    az login
fi

echo -e "${GREEN}✓ Logged in to Azure${NC}"
echo ""

# Get configuration
echo -e "${BLUE}📝 Configuration${NC}"
echo "================="
echo ""

read -p "Resource Group name (default: tailorjob-rg): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-tailorjob-rg}

read -p "App Service Plan name (default: tailorjob-plan): " APP_SERVICE_PLAN
APP_SERVICE_PLAN=${APP_SERVICE_PLAN:-tailorjob-plan}

read -p "Web App name (must be globally unique, default: tailorjob-api): " APP_NAME
APP_NAME=${APP_NAME:-tailorjob-api}

read -p "Azure region (default: eastus): " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "App Service tier (default: B1, ~$13/month): " SKU
SKU=${SKU:-B1}

echo ""
echo -e "${BLUE}📦 Deployment Configuration:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Service Plan: $APP_SERVICE_PLAN"
echo "  Web App: $APP_NAME"
echo "  Location: $LOCATION"
echo "  Tier: $SKU"
echo ""

read -p "Continue with deployment? (y/n): " CONFIRM
if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo -e "${BLUE}🏗️  Step 1: Creating Azure Resources${NC}"
echo "======================================"

# Create resource group
echo "Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

echo -e "${GREEN}✓ Resource group created${NC}"

# Create App Service Plan
echo ""
echo "Creating App Service Plan..."
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku $SKU \
  --output table

echo -e "${GREEN}✓ App Service Plan created${NC}"

# Create Web App
echo ""
echo "Creating Web App..."
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11" \
  --output table

echo -e "${GREEN}✓ Web App created${NC}"

echo ""
echo -e "${BLUE}⚙️  Step 2: Configuring Web App${NC}"
echo "================================"

# Set startup command
echo "Setting startup command..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "startup.sh" \
  --output table

echo -e "${GREEN}✓ Startup command configured${NC}"

# Set basic app settings
echo ""
echo "Setting basic application settings..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    ENVIRONMENT="production" \
  --output table

echo -e "${GREEN}✓ Basic settings configured${NC}"

echo ""
echo -e "${BLUE}📤 Step 3: Deploying Code${NC}"
echo "========================="

read -p "Deploy code now? (y/n): " DEPLOY_CODE
if [[ $DEPLOY_CODE == "y" || $DEPLOY_CODE == "Y" ]]; then
    echo ""
    echo "Choose deployment method:"
    echo "  1) Git deployment (recommended)"
    echo "  2) ZIP deployment"
    read -p "Enter choice (1 or 2): " DEPLOY_METHOD
    
    if [[ $DEPLOY_METHOD == "1" ]]; then
        echo ""
        echo "Setting up Git deployment..."
        
        # Enable local git
        DEPLOY_URL=$(az webapp deployment source config-local-git \
          --name $APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --query url \
          --output tsv)
        
        echo -e "${GREEN}✓ Git deployment enabled${NC}"
        echo ""
        echo "Add Azure remote to your git repo:"
        echo -e "${YELLOW}git remote add azure $DEPLOY_URL${NC}"
        echo ""
        echo "Then deploy with:"
        echo -e "${YELLOW}git push azure main:master${NC}"
        
    elif [[ $DEPLOY_METHOD == "2" ]]; then
        echo ""
        echo "Creating ZIP package..."
        cd backend
        zip -r ../backend.zip . -x "venv/*" -x "*.pyc" -x "__pycache__/*" -x ".env"
        cd ..
        
        echo "Deploying ZIP..."
        az webapp deployment source config-zip \
          --resource-group $RESOURCE_GROUP \
          --name $APP_NAME \
          --src backend.zip
        
        echo -e "${GREEN}✓ Code deployed${NC}"
        rm backend.zip
    fi
else
    echo "Skipping code deployment"
fi

echo ""
echo -e "${BLUE}🔐 Step 4: Environment Variables${NC}"
echo "================================="
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: You need to set your environment variables!${NC}"
echo ""
echo "Set them via Azure Portal:"
echo "  1. Go to: https://portal.azure.com"
echo "  2. Navigate to: App Services → $APP_NAME"
echo "  3. Go to: Settings → Configuration"
echo "  4. Add these settings:"
echo ""
echo "Required variables:"
echo "  - SUPABASE_URL"
echo "  - SUPABASE_KEY"
echo "  - UPSTASH_REDIS_URL"
echo "  - AZURE_OPENAI_ENDPOINT"
echo "  - AZURE_OPENAI_KEY"
echo "  - AZURE_OPENAI_DEPLOYMENT"
echo "  - PAYPAL_CLIENT_ID"
echo "  - PAYPAL_SECRET"
echo "  - PAYPAL_PLAN_ID_BASIC"
echo "  - PAYPAL_PLAN_ID_PRO"
echo "  - FRONTEND_URL=https://tailorjob.vercel.app"
echo "  - CORS_ORIGINS=[\"https://tailorjob.vercel.app\",\"https://$APP_NAME.azurewebsites.net\"]"
echo "  - USE_MATCHER_V5=true"
echo ""
echo "Or set via CLI (create a .env.azure file and run):"
echo -e "${YELLOW}az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings @.env.azure${NC}"
echo ""

read -p "Open Azure Portal to set environment variables? (y/n): " OPEN_PORTAL
if [[ $OPEN_PORTAL == "y" || $OPEN_PORTAL == "Y" ]]; then
    open "https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$APP_NAME/configuration"
fi

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "======================="
echo ""
echo "Your app URL: https://$APP_NAME.azurewebsites.net"
echo "API Docs: https://$APP_NAME.azurewebsites.net/docs"
echo ""
echo "Next steps:"
echo "  1. Set environment variables (see above)"
echo "  2. Wait 2-3 minutes for app to start"
echo "  3. Test your API: curl https://$APP_NAME.azurewebsites.net/"
echo "  4. Check logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "  5. Update frontend API_BASE_URL to: https://$APP_NAME.azurewebsites.net/api"
echo ""
echo "For detailed instructions, see: docs/AZURE_MIGRATION_GUIDE.md"
echo ""