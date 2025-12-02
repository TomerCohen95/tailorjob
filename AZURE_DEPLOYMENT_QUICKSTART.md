# Azure Deployment Quick Start

Quick reference for deploying TailorJob backend to Azure App Service.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed: `brew install azure-cli`
- Git repository initialized

## Option 1: Automated Deployment (Recommended)

Run the automated deployment script:

```bash
./deploy-to-azure.sh
```

This interactive script will:
1. Create Azure resources (Resource Group, App Service Plan, Web App)
2. Configure the app
3. Guide you through code deployment
4. Provide instructions for setting environment variables

## Option 2: Manual Deployment

### Step 1: Install Azure CLI (if not installed)

```bash
brew install azure-cli
az login
```

### Step 2: Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="tailorjob-rg"
LOCATION="eastus"
APP_NAME="tailorjob-api"  # Must be globally unique
APP_SERVICE_PLAN="tailorjob-plan"

# Create resources
az group create --name $RESOURCE_GROUP --location $LOCATION
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --is-linux --sku B1
az webapp create --name $APP_NAME --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.11"
```

### Step 3: Configure Startup

```bash
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "startup.sh"
```

### Step 4: Set Basic Settings

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    ENVIRONMENT="production"
```

### Step 5: Deploy Code

**Via Git:**
```bash
az webapp deployment source config-local-git --name $APP_NAME --resource-group $RESOURCE_GROUP
# Add the git remote (URL will be shown in output)
git remote add azure <deployment-url>
git push azure main:master
```

**Via ZIP:**
```bash
cd backend
zip -r ../backend.zip . -x "venv/*" -x "*.pyc" -x "__pycache__/*" -x ".env"
cd ..
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src backend.zip
```

### Step 6: Set Environment Variables

Create `backend/.env.azure` from the template:

```bash
cp backend/.env.azure.template backend/.env.azure
# Edit .env.azure with your actual values
```

Upload via Azure Portal:
1. Go to https://portal.azure.com
2. Navigate to App Services → your-app-name
3. Settings → Configuration → New application setting
4. Add each variable from `.env.azure`

Or via CLI (after filling in `.env.azure`):
```bash
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings @backend/.env.azure
```

## Important Environment Variables

**Must set these in Azure:**
- `SUPABASE_URL` and `SUPABASE_KEY`
- `UPSTASH_REDIS_URL`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT`
- `PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`, `PAYPAL_PLAN_ID_BASIC`, `PAYPAL_PLAN_ID_PRO`
- `FRONTEND_URL=https://tailorjob.vercel.app`
- `CORS_ORIGINS=["https://tailorjob.vercel.app","https://your-app.azurewebsites.net"]`

## Testing

```bash
# Get app URL
az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "defaultHostName" -o tsv

# Test API
curl https://your-app.azurewebsites.net/

# View logs
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME
```

## Update Frontend

After deployment, update [`src/lib/api.ts`](src/lib/api.ts:3):

```typescript
const API_BASE_URL = 'https://your-app.azurewebsites.net/api';
```

## Files Created

- [`backend/startup.sh`](backend/startup.sh) - Gunicorn startup script
- [`backend/web.config`](backend/web.config) - Azure web configuration
- [`backend/.env.azure.template`](backend/.env.azure.template) - Environment variables template
- [`deploy-to-azure.sh`](deploy-to-azure.sh) - Automated deployment script
- [`docs/AZURE_MIGRATION_GUIDE.md`](docs/AZURE_MIGRATION_GUIDE.md) - Detailed migration guide

## Troubleshooting

**App not starting?**
```bash
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME
```

**502 Bad Gateway?**
- Check `WEBSITES_PORT=8000` is set
- Verify startup.sh is configured
- Check application logs

**CORS errors?**
- Ensure `CORS_ORIGINS` includes both Vercel and Azure domains
- Verify JSON format with proper escaping

## Cost

- **B1 tier**: ~$13/month (1.75GB RAM, 1 core, always on)
- **Free tier**: $0 but has 60min/day limit (not recommended for production)

## Next Steps

1. ✅ Run `./deploy-to-azure.sh` or follow manual steps
2. ✅ Set environment variables in Azure Portal
3. ✅ Wait 2-3 minutes for app to start
4. ✅ Test API endpoints
5. ✅ Update frontend API URL
6. ✅ Monitor logs for 24-48 hours
7. ✅ Decommission Render when stable

## Full Documentation

See [`docs/AZURE_MIGRATION_GUIDE.md`](docs/AZURE_MIGRATION_GUIDE.md) for complete details including:
- Architecture explanation
- Environment variables reference
- Scaling strategies
- Monitoring setup
- Rollback procedures