# Azure Migration Guide: Render → Azure App Service

This guide provides step-by-step instructions for migrating your TailorJob FastAPI backend from Render to Azure App Service.

## Overview

**Current Setup (Render):**
- Service: Web Service (Python)
- Runtime: Python 3.11
- Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Working Directory: `backend/`

**Target Setup (Azure):**
- Service: Azure App Service (Linux, Python 3.11)
- Deployment: Git-based or ZIP deployment
- Runtime: Gunicorn with Uvicorn workers (production-ready)

---

## 1. Files to Create

### 1.1 Startup Script: `backend/startup.sh`

Create this file in your `backend/` directory:

```bash
#!/bin/bash

# Azure App Service startup script for FastAPI
# This uses Gunicorn with Uvicorn workers for production

# Default to port 8000 if not set by Azure
PORT="${PORT:-8000}"

# Start Gunicorn with Uvicorn workers
# - 4 workers (adjust based on your App Service plan)
# - Uvicorn worker class for async support
# - Bind to 0.0.0.0 to accept external connections
# - Timeout of 120s for long-running requests (CV parsing)
exec gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

**Make it executable:**
```bash
chmod +x backend/startup.sh
```

### 1.2 Azure Web Config: `backend/web.config`

Create this file for IIS configuration (Azure uses this even on Linux):

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" scriptProcessor="D:\home\python\python.exe|D:\home\site\wwwroot\startup.sh" resourceType="Unspecified" requireAccess="Script"/>
    </handlers>
  </system.webServer>
</configuration>
```

### 1.3 Update Requirements: `backend/requirements.txt`

Add Gunicorn to your existing requirements:

```txt
fastapi==0.115.5
uvicorn[standard]==0.34.0
gunicorn==21.2.0  # ADD THIS LINE
python-dotenv==1.0.1
# ... rest of your requirements
```

---

## 2. Environment Variables Configuration

### 2.1 Current Render Environment Variables

From your `render.yaml` and `.env`:

| Render Variable | Value/Source | Azure Equivalent |
|----------------|--------------|------------------|
| `SUPABASE_URL` | Secret | Same name |
| `SUPABASE_KEY` | Secret | Same name |
| `UPSTASH_REDIS_URL` | Secret | Same name |
| `AZURE_OPENAI_ENDPOINT` | Secret | Same name |
| `AZURE_OPENAI_KEY` | Secret | Same name |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o-mini` | Same name |
| `AZURE_OPENAI_API_VERSION` | `2024-08-01-preview` | Same name |
| `PAYPAL_CLIENT_ID` | Secret | Same name |
| `PAYPAL_SECRET` | Secret | Same name |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` | Same name |
| `PAYPAL_WEBHOOK_ID` | Secret | Same name |
| `PAYPAL_PLAN_ID_BASIC` | Secret | Same name |
| `PAYPAL_PLAN_ID_PRO` | Secret | Same name |
| `CORS_ORIGINS` | `["https://tailorjob.vercel.app"]` | **UPDATE THIS** |
| `FRONTEND_URL` | Not set | **ADD THIS** |
| `USE_MATCHER_V5` | `true` | Same name |
| `ENVIRONMENT` | `development` | **Change to `production`** |

### 2.2 Azure-Specific Variables to Add

| Variable | Value | Purpose |
|----------|-------|---------|
| `WEBSITES_PORT` | `8000` | Tells Azure which port your app uses |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Enable Oryx build system |
| `FRONTEND_URL` | `https://tailorjob.vercel.app` | For PayPal redirects |
| `CORS_ORIGINS` | `["https://tailorjob.vercel.app","https://your-azure-app.azurewebsites.net"]` | Include Azure domain |
| `ENVIRONMENT` | `production` | Production mode |

---

## 3. CORS Configuration Changes

### Current Issue
Your [`backend/app/config.py`](backend/app/config.py:40) has:
```python
CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:8080"]'
```

### Required Change
Update the Azure environment variable to include your Azure domain:

```json
["https://tailorjob.vercel.app","https://tailorjob-api.azurewebsites.net"]
```

**Note:** Replace `tailorjob-api.azurewebsites.net` with your actual Azure App Service domain.

---

## 4. Azure App Service Deployment

### 4.1 Prerequisites

1. **Azure CLI installed:**
   ```bash
   # macOS
   brew install azure-cli
   
   # Verify installation
   az --version
   ```

2. **Login to Azure:**
   ```bash
   az login
   ```

3. **Set your subscription (if you have multiple):**
   ```bash
   az account list --output table
   az account set --subscription "YOUR_SUBSCRIPTION_ID"
   ```

### 4.2 Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="tailorjob-rg"
LOCATION="eastus"  # or your preferred region
APP_NAME="tailorjob-api"  # Must be globally unique
APP_SERVICE_PLAN="tailorjob-plan"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create App Service Plan (Linux, B1 tier = ~$13/month)
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11"
```

### 4.3 Configure Deployment

**Option A: Git Deployment (Recommended)**

```bash
# Enable local Git deployment
az webapp deployment source config-local-git \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# Get deployment credentials
az webapp deployment list-publishing-credentials \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{username:publishingUserName, password:publishingPassword}" \
  --output json

# Add Azure remote to your git repo
# URL format: https://<username>@<app-name>.scm.azurewebsites.net/<app-name>.git
git remote add azure https://<your-deployment-url>

# Deploy
git push azure main:master
```

**Option B: ZIP Deployment**

```bash
# From your project root
cd backend
zip -r ../backend.zip . -x "venv/*" -x "*.pyc" -x "__pycache__/*"
cd ..

# Deploy ZIP
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src backend.zip
```

### 4.4 Configure Startup Command

```bash
# Tell Azure to use your startup script
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "startup.sh"
```

### 4.5 Set Environment Variables

```bash
# Set each environment variable
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    SUPABASE_URL="https://sdclmjzsepnxuhhruazg.supabase.co" \
    SUPABASE_KEY="YOUR_SUPABASE_SERVICE_KEY" \
    UPSTASH_REDIS_URL="YOUR_REDIS_URL" \
    AZURE_OPENAI_ENDPOINT="YOUR_ENDPOINT" \
    AZURE_OPENAI_KEY="YOUR_KEY" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" \
    AZURE_OPENAI_API_VERSION="2024-08-01-preview" \
    PAYPAL_CLIENT_ID="YOUR_PAYPAL_CLIENT_ID" \
    PAYPAL_SECRET="YOUR_PAYPAL_SECRET" \
    PAYPAL_BASE_URL="https://api-m.sandbox.paypal.com" \
    PAYPAL_WEBHOOK_ID="YOUR_WEBHOOK_ID" \
    PAYPAL_PLAN_ID_BASIC="YOUR_BASIC_PLAN_ID" \
    PAYPAL_PLAN_ID_PRO="YOUR_PRO_PLAN_ID" \
    FRONTEND_URL="https://tailorjob.vercel.app" \
    CORS_ORIGINS='["https://tailorjob.vercel.app","https://tailorjob-api.azurewebsites.net"]' \
    USE_MATCHER_V5="true" \
    ENVIRONMENT="production"
```

**Alternative: Set via Azure Portal**
1. Go to Azure Portal → App Services → Your App
2. Navigate to **Settings → Configuration**
3. Click **+ New application setting** for each variable
4. Click **Save** and **Continue** when prompted to restart

---

## 5. How Azure Runs Your Backend

### 5.1 Build Process (Oryx)

When you deploy, Azure's Oryx build system:

1. **Detects Python app** (finds `requirements.txt`)
2. **Creates virtual environment** in `/home/site/wwwroot`
3. **Installs dependencies** via `pip install -r requirements.txt`
4. **Sets up Python runtime** (3.11 as specified)

### 5.2 Runtime Process

1. **Azure reads `startup.sh`** (specified in startup-file config)
2. **Executes the script** which starts Gunicorn
3. **Gunicorn spawns workers** (4 Uvicorn workers)
4. **Workers listen on port** specified by `WEBSITES_PORT` (8000)
5. **Azure proxy** forwards external port 80/443 → internal port 8000

### 5.3 Environment Variables

- **Stored in:** App Service → Configuration → Application settings
- **Accessed by:** Your Python app via `os.environ` (loaded by pydantic-settings)
- **No `.env` file needed** - Azure injects them at runtime
- **Secure storage** - Secrets are encrypted at rest

### 5.4 File System

```
/home/site/wwwroot/          # Your app code
├── app/                     # Your FastAPI app
├── requirements.txt
├── startup.sh
└── venv/                    # Auto-created virtual environment
```

---

## 6. Post-Deployment Steps

### 6.1 Verify Deployment

```bash
# Check logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME

# Get app URL
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --query "defaultHostName" \
  --output tsv
```

### 6.2 Test Your API

```bash
# Test health endpoint
curl https://tailorjob-api.azurewebsites.net/

# Test API docs
open https://tailorjob-api.azurewebsites.net/docs
```

### 6.3 Update Frontend

Update your frontend API URL from Render to Azure:

**File: [`src/lib/api.ts`](src/lib/api.ts:3)**

```typescript
// OLD (Render)
const API_BASE_URL = 'https://tailorjob-api.onrender.com/api';

// NEW (Azure)
const API_BASE_URL = 'https://tailorjob-api.azurewebsites.net/api';
```

### 6.4 Configure Custom Domain (Optional)

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname api.yourdomain.com

# Enable HTTPS
az webapp config ssl bind \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

---

## 7. Cost Comparison

### Render Pricing
- **Free Tier:** $0/month (spins down after inactivity, slow cold starts)
- **Starter:** $7/month (always on, 512MB RAM)

### Azure App Service Pricing
- **F1 (Free):** $0/month (60 min/day limit, 1GB RAM) - **Not recommended for production**
- **B1 (Basic):** ~$13/month (Always on, 1.75GB RAM, 1 core) - **Recommended**
- **B2 (Basic):** ~$26/month (3.5GB RAM, 2 cores)
- **S1 (Standard):** ~$69/month (Auto-scaling, staging slots, backups)

**Recommendation:** Start with **B1 tier** ($13/month) for production workloads.

### Cost Optimization
- **Reserved Instances:** Save up to 55% with 1-year commitment
- **Dev/Test Pricing:** Special rates if you have Visual Studio subscription
- **Auto-shutdown:** Configure for non-critical environments

---

## 8. Scaling Considerations

### Current Architecture Limitations

From [`backend/app/main.py`](backend/app/main.py:18-34):
- **Worker runs in FastAPI process** (not separate service)
- **Single worker instance** (not horizontally scalable yet)

### Azure App Service Scaling

**Vertical Scaling (Scale Up):**
```bash
# Upgrade to B2 (more RAM/CPU)
az appservice plan update \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B2
```

**Horizontal Scaling (Scale Out):**
```bash
# Add more instances (requires Standard tier or higher)
az appservice plan update \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku S1 \
  --number-of-workers 3
```

### Future Considerations

For true horizontal scaling of the CV worker:
1. **Extract worker to separate service** (Azure Container Apps or Functions)
2. **Use Redis for job queue** (already configured via Upstash)
3. **Implement distributed task queue** (Celery or similar)

---

## 9. Monitoring & Debugging

### Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app tailorjob-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Link to App Service
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app tailorjob-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv)

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY"
```

### View Logs

```bash
# Live log stream
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME

# Download logs
az webapp log download \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --log-file logs.zip
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Application Error" | Startup script failed | Check logs: `az webapp log tail` |
| Port binding error | Wrong `WEBSITES_PORT` | Set to `8000` |
| Import errors | Dependencies not installed | Check Oryx build logs |
| CORS errors | Missing Azure domain | Update `CORS_ORIGINS` |
| 502 Bad Gateway | App not responding | Check startup command and logs |

---

## 10. Migration Checklist

- [ ] Create `backend/startup.sh` with Gunicorn config
- [ ] Add `gunicorn==21.2.0` to `requirements.txt`
- [ ] Create Azure resource group and App Service
- [ ] Configure startup command to use `startup.sh`
- [ ] Set all environment variables in Azure
- [ ] Update `CORS_ORIGINS` to include Azure domain
- [ ] Add `FRONTEND_URL` variable for PayPal redirects
- [ ] Deploy code via Git or ZIP
- [ ] Test API endpoints and docs
- [ ] Update frontend API URL to Azure domain
- [ ] Configure custom domain (if applicable)
- [ ] Enable Application Insights for monitoring
- [ ] Set up alerts for errors and performance
- [ ] Document Azure credentials in team password manager
- [ ] Decommission Render service (after confirming Azure works)

---

## 11. Rollback Plan

If issues occur during migration:

1. **Keep Render running** until Azure is fully tested
2. **Frontend can point back to Render** by changing `API_BASE_URL`
3. **No database changes** - Supabase stays the same
4. **Redis stays external** - Upstash continues working

**Zero-downtime migration:**
1. Deploy to Azure
2. Test with Azure URL directly
3. Update frontend API URL only after confirming Azure works
4. Monitor for 24-48 hours
5. Decommission Render

---

## 12. Next Steps

1. **Review this guide** and ask questions
2. **Create Azure account** if you don't have one
3. **Run commands in order** from Section 4
4. **Test thoroughly** before switching frontend
5. **Monitor** for first 48 hours after migration

Need help? Check Azure documentation or contact support.