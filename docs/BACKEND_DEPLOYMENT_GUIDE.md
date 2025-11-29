# Backend Deployment Guide

## Current Setup
- **Frontend**: Deployed on Vercel → https://tailorjob.vercel.app/
- **Backend**: Running locally on http://localhost:8000
- **Database**: Supabase (already in cloud)
- **Stack**: FastAPI + Python + Redis + Azure OpenAI

## Best Deployment Options for FastAPI Backend

### Option 1: Azure App Service (Recommended for Azure OpenAI Integration)

**Pros:**
- ✅ Native integration with Azure OpenAI
- ✅ Managed service (no server management)
- ✅ Auto-scaling
- ✅ Built-in CI/CD with GitHub
- ✅ Same ecosystem as your OpenAI API

**Setup:**
```bash
# 1. Install Azure CLI
brew install azure-cli  # macOS
# or: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

# 2. Login to Azure
az login

# 3. Create resource group
az group create --name tailorjob-rg --location eastus

# 4. Create App Service Plan
az appservice plan create \
  --name tailorjob-plan \
  --resource-group tailorjob-rg \
  --is-linux \
  --sku B1

# 5. Create Web App
az webapp create \
  --name tailorjob-api \
  --resource-group tailorjob-rg \
  --plan tailorjob-plan \
  --runtime "PYTHON:3.11"

# 6. Configure environment variables
az webapp config appsettings set \
  --resource-group tailorjob-rg \
  --name tailorjob-api \
  --settings \
    SUPABASE_URL="your_supabase_url" \
    SUPABASE_KEY="your_supabase_key" \
    AZ_OPENAI_ENDPOINT="your_azure_openai_endpoint" \
    AZ_OPENAI_API_KEY="your_api_key"

# 7. Deploy from GitHub (recommended)
# Or deploy from local:
cd backend
zip -r deploy.zip .
az webapp deployment source config-zip \
  --resource-group tailorjob-rg \
  --name tailorjob-api \
  --src deploy.zip
```

**URL:** `https://tailorjob-api.azurewebsites.net`

**Cost:** ~$13/month (B1 tier)

---

### Option 2: Railway (Simplest, Best for Quick Deploy)

**Pros:**
- ✅ Extremely easy setup (< 5 minutes)
- ✅ Free tier available ($5/month credit)
- ✅ Auto-deploys from GitHub
- ✅ Built-in Redis
- ✅ No configuration needed

**Setup:**
```bash
# 1. Go to: https://railway.app/
# 2. Sign in with GitHub
# 3. Click "New Project" → "Deploy from GitHub repo"
# 4. Select: tomercohen/tailorjob
# 5. Root directory: backend
# 6. Railway auto-detects Python/FastAPI
# 7. Add environment variables in dashboard
# 8. Deploy automatically!
```

**URL:** `https://tailorjob-production.up.railway.app`

**Cost:** Free tier ($5 credit/month), then $5-20/month

---

### Option 3: Render (Good Balance)

**Pros:**
- ✅ Simple setup
- ✅ Free tier available
- ✅ Auto-SSL
- ✅ Auto-deploys from GitHub
- ✅ Good for Python apps

**Setup:**
```bash
# 1. Go to: https://render.com/
# 2. Sign in with GitHub
# 3. New → Web Service
# 4. Connect repository: tomercohen/tailorjob
# 5. Root directory: backend
# 6. Build command: pip install -r requirements.txt
# 7. Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
# 8. Add environment variables
# 9. Deploy!
```

**URL:** `https://tailorjob.onrender.com`

**Cost:** Free tier (spins down after inactivity), or $7/month

---

### Option 4: Google Cloud Run (Serverless)

**Pros:**
- ✅ Serverless (pay per request)
- ✅ Auto-scaling to zero
- ✅ Fast cold starts
- ✅ Free tier (2M requests/month)

**Setup:**
```bash
# 1. Create Dockerfile in backend/
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 2. Install gcloud CLI
# 3. Deploy
cd backend
gcloud run deploy tailorjob-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

**URL:** `https://tailorjob-api-xyz.run.app`

**Cost:** Free tier, then pay-per-use (~$0.01/1000 requests)

---

## Quick Recommendation

### **Use Railway** (Easiest for getting started):

1. **Go to**: https://railway.app/
2. **Sign in** with GitHub
3. **New Project** → Deploy from GitHub
4. **Select repo**: tomercohen/tailorjob
5. **Settings** → Set root directory: `backend`
6. **Variables** → Add:
   ```
   SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
   SUPABASE_KEY=your_key
   AZ_OPENAI_ENDPOINT=your_endpoint
   AZ_OPENAI_API_KEY=your_key
   REDIS_URL=redis://default:password@redis.railway.internal:6379
   ```
7. **Deploy** → Automatic!

Railway will give you a URL like: `https://tailorjob-production.up.railway.app`

---

## After Deployment: Update Frontend

Once backend is deployed, update frontend to point to production API:

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://your-backend-url.railway.app/api'  // Production
  : 'http://localhost:8000/api';                 // Development
```

Or use environment variable:

```bash
# In Vercel → Settings → Environment Variables
VITE_API_URL=https://your-backend-url.railway.app/api
```

Then in code:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
```

---

## Required Environment Variables

All deployment platforms need these:

```bash
# Supabase
SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
SUPABASE_KEY=your_service_role_key

# Azure OpenAI
AZ_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZ_OPENAI_API_KEY=your_key
AZ_OPENAI_API_VERSION=2024-08-01-preview
AZ_OPENAI_DEPLOYMENT_NAME=your_deployment

# Redis (optional - for background jobs)
REDIS_URL=redis://user:pass@host:6379

# CORS (for production)
CORS_ORIGINS=["https://tailorjob.vercel.app"]
```

---

## Testing Deployment

After deploying backend:

```bash
# Test health endpoint
curl https://your-backend-url/health

# Test API
curl https://your-backend-url/api/cv/list \
  -H "Authorization: Bearer YOUR_SUPABASE_TOKEN"
```

---

## My Recommendation

**Start with Railway:**
1. Fastest setup (< 5 minutes)
2. Free to start
3. Auto-deploys from GitHub
4. Built-in Redis
5. Easy to migrate later if needed

**Then migrate to Azure App Service** if you need:
- Better Azure OpenAI integration
- More control
- Enterprise features

---

## Deployment Checklist

- [ ] Choose deployment platform (Railway recommended)
- [ ] Set up account and connect GitHub
- [ ] Configure environment variables
- [ ] Deploy backend
- [ ] Get production URL
- [ ] Update frontend API_BASE_URL
- [ ] Update CORS in backend to allow Vercel domain
- [ ] Test end-to-end
- [ ] Monitor logs

---

## Need Help?

Each platform has detailed guides:
- **Railway**: https://docs.railway.app/
- **Render**: https://render.com/docs
- **Azure**: https://learn.microsoft.com/en-us/azure/app-service/
- **Google Cloud Run**: https://cloud.google.com/run/docs