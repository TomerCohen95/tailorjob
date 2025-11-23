#!/bin/bash

# TailorJob.ai - Azure OpenAI Setup Script
# This script automates the Azure OpenAI setup process

set -e

echo "🚀 TailorJob.ai - Azure OpenAI Setup"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="tailorjob-rg"
LOCATION="eastus"
SERVICE_NAME="tailorjob-openai"
DEPLOYMENT_NAME="gpt-4"
MODEL_NAME="gpt-4"
MODEL_VERSION="0613"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed${NC}"
    echo "Please install it from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    echo ""
    echo "For macOS: brew install azure-cli"
    exit 1
fi

echo -e "${GREEN}✅ Azure CLI found${NC}"
echo ""

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure${NC}"
    echo "Logging you in..."
    az login
fi

echo -e "${GREEN}✅ Logged in to Azure${NC}"
echo ""

# Show current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "📋 Current subscription: ${GREEN}$SUBSCRIPTION${NC}"
echo -e "🆔 Subscription ID: $SUBSCRIPTION_ID"
echo ""

# Ask for confirmation
read -p "Do you want to continue with this subscription? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled. Please set your subscription with:"
    echo "az account set --subscription <subscription-id>"
    exit 1
fi

# Choose deployment model
echo ""
echo "Choose your model deployment:"
echo "1. GPT-4 (Recommended, ~$30-50/month)"
echo "2. GPT-3.5-Turbo (Budget option, ~$2-5/month)"
read -p "Enter choice (1 or 2): " -n 1 -r
echo

if [[ $REPLY == "2" ]]; then
    DEPLOYMENT_NAME="gpt-35-turbo"
    MODEL_NAME="gpt-35-turbo"
    echo -e "${YELLOW}Using GPT-3.5-Turbo${NC}"
else
    echo -e "${GREEN}Using GPT-4${NC}"
fi

echo ""
echo "🏗️  Step 1: Creating Resource Group"
echo "=================================="

if az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Resource group '$RESOURCE_GROUP' already exists${NC}"
else
    az group create --name $RESOURCE_GROUP --location $LOCATION
    echo -e "${GREEN}✅ Resource group created${NC}"
fi

echo ""
echo "🤖 Step 2: Creating Azure OpenAI Service"
echo "========================================"

if az cognitiveservices account show --name $SERVICE_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Azure OpenAI service '$SERVICE_NAME' already exists${NC}"
else
    echo "This may take a few minutes..."
    az cognitiveservices account create \
        --name $SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --kind OpenAI \
        --sku S0 \
        --location $LOCATION \
        --yes
    
    echo -e "${GREEN}✅ Azure OpenAI service created${NC}"
fi

echo ""
echo "🚀 Step 3: Deploying Model"
echo "========================="

# Check if deployment exists
DEPLOYMENT_EXISTS=$(az cognitiveservices account deployment list \
    --name $SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='$DEPLOYMENT_NAME'].name" -o tsv)

if [ ! -z "$DEPLOYMENT_EXISTS" ]; then
    echo -e "${YELLOW}⚠️  Deployment '$DEPLOYMENT_NAME' already exists${NC}"
else
    echo "Deploying $MODEL_NAME model..."
    az cognitiveservices account deployment create \
        --name $SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --deployment-name $DEPLOYMENT_NAME \
        --model-name $MODEL_NAME \
        --model-version $MODEL_VERSION \
        --model-format OpenAI \
        --sku-capacity 10 \
        --sku-name "Standard"
    
    echo -e "${GREEN}✅ Model deployed${NC}"
fi

echo ""
echo "🔑 Step 4: Getting Credentials"
echo "=============================="

ENDPOINT=$(az cognitiveservices account show \
    --name $SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.endpoint" \
    --output tsv)

API_KEY=$(az cognitiveservices account keys list \
    --name $SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "key1" \
    --output tsv)

echo -e "${GREEN}✅ Credentials retrieved${NC}"
echo ""

echo "📝 Step 5: Updating .env file"
echo "============================="

# Update backend/.env
if [ -f "backend/.env" ]; then
    # Backup original
    cp backend/.env backend/.env.backup
    
    # Update values
    sed -i.tmp "s|AZURE_OPENAI_ENDPOINT=.*|AZURE_OPENAI_ENDPOINT=$ENDPOINT|" backend/.env
    sed -i.tmp "s|AZURE_OPENAI_KEY=.*|AZURE_OPENAI_KEY=$API_KEY|" backend/.env
    sed -i.tmp "s|AZURE_OPENAI_DEPLOYMENT=.*|AZURE_OPENAI_DEPLOYMENT=$DEPLOYMENT_NAME|" backend/.env
    rm backend/.env.tmp
    
    echo -e "${GREEN}✅ backend/.env updated${NC}"
else
    echo -e "${RED}❌ backend/.env not found${NC}"
    echo "Please create it manually with:"
    echo ""
    echo "AZURE_OPENAI_ENDPOINT=$ENDPOINT"
    echo "AZURE_OPENAI_KEY=$API_KEY"
    echo "AZURE_OPENAI_DEPLOYMENT=$DEPLOYMENT_NAME"
fi

echo ""
echo "🧪 Step 6: Testing Connection"
echo "============================"

cd backend

# Create test script
cat > test_azure_openai.py << 'EOF'
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

try:
    client = AzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_KEY'),
        api_version='2024-02-01',
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    )
    
    response = client.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Say "Hello from TailorJob.ai!"'}
        ],
        max_tokens=50
    )
    
    print('✅ Azure OpenAI connection successful!')
    print(f'Response: {response.choices[0].message.content}')
    exit(0)
except Exception as e:
    print(f'❌ Connection failed: {str(e)}')
    exit(1)
EOF

if python3 test_azure_openai.py; then
    echo -e "${GREEN}✅ Connection test passed!${NC}"
    rm test_azure_openai.py
else
    echo -e "${RED}❌ Connection test failed${NC}"
    echo "Please check your credentials and try again"
    exit 1
fi

cd ..

echo ""
echo "================================================"
echo -e "${GREEN}✅ Azure OpenAI Setup Complete!${NC}"
echo "================================================"
echo ""
echo "📋 Summary:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Service Name: $SERVICE_NAME"
echo "  Model: $DEPLOYMENT_NAME"
echo "  Endpoint: $ENDPOINT"
echo ""
echo "💡 Next Steps:"
echo "  1. Restart your backend server"
echo "  2. Test CV parsing and tailoring"
echo "  3. Monitor usage in Azure Portal"
echo ""
echo "📊 Monitor your usage:"
echo "  Azure Portal: https://portal.azure.com"
echo "  Resource: $SERVICE_NAME"
echo ""
echo "💰 Cost Management:"
echo "  Set up budget alerts in Azure Portal"
echo "  Cost Management → Budgets → Create"
echo ""
echo "🔐 Security reminder:"
echo "  - API keys are in .env (not committed to git)"
echo "  - Backup created at: backend/.env.backup"
echo "  - Rotate keys every 90 days"
echo ""