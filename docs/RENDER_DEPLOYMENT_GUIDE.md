# Deploy FastAPI Backend to Render (Free/Cheap)

## Why Render?
- ✅ **FREE tier** (with limitations: spins down after 15 min inactivity)
- ✅ **$7/month** for always-on instance
- ✅ Auto-deploys from GitHub
- ✅ Easy setup (< 10 minutes)
- ✅ Built-in SSL
- ✅ Good for Python/FastAPI

## Method 1: Deploy via Render Dashboard (Easiest)

### Step 1: Create render.yaml

```bash
# Create render.yaml in project root
cat > render.yaml << 'EOF'
services:
  - type: web
    name: tailorjob-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: AZ_OPENAI_ENDPOINT
        sync: false
      - key: AZ_OPENAI_API_KEY
        sync: false
      - key: AZ_OPENAI_API_VERSION
        value: 2024-08-01-preview
      - key: AZ_OPENAI_DEPLOYMENT_NAME
        sync: false
      - key: CORS_ORIGINS
        value: '["https://tailorjob.vercel.app"]'
EOF
```

### Step 2: Push to GitHub

```bash
git add render.yaml
git commit -m "feat: add Render deployment config"
git push origin main
```

### Step 3: Deploy on Render

1. Go to: **https://render.com/**
2. Sign up/Login with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect your repository: **tomercohen/tailorjob**
5. Render will detect `render.yaml` automatically
6. Click **"Apply"**
7. Add environment variable values in dashboard:
   - `SUPABASE_URL`: `https://sdclmjzsepnxuhhruazg.supabase.co`
   - `SUPABASE_KEY`: Your Supabase service role key
   - `AZ_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
   - `AZ_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZ_OPENAI_DEPLOYMENT_NAME`: Your deployment name
8. Click **"Create Web Service"**

**Done!** Your API will be at: `https://tailorjob-api.onrender.com`

---

## Method 2: Deploy via Render Blueprint (Infrastructure as Code)

### Step 1: Create Dockerfile (Optional but recommended)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 2: Update render.yaml for Docker

```yaml
services:
  - type: web
    name: tailorjob-api
    runtime: docker
    rootDir: backend
    dockerfilePath: ./Dockerfile
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: AZ_OPENAI_ENDPOINT
        sync: false
      - key: AZ_OPENAI_API_KEY
        sync: false
      - key: AZ_OPENAI_API_VERSION
        value: 2024-08-01-preview
      - key: AZ_OPENAI_DEPLOYMENT_NAME
        sync: false
      - key: CORS_ORIGINS
        value: '["https://tailorjob.vercel.app"]'
    plan: free  # or 'starter' for $7/month
```

---

## Method 3: Manual CLI Deployment (Using Git)

While Render doesn't have a traditional CLI, you can deploy by connecting Git:

```bash
# 1. Ensure your code is committed
git add -A
git commit -m "prepare for Render deployment"
git push origin main

# 2. Go to Render Dashboard and link repository
# 3. Render auto-deploys on every push to main branch
```

---

## Pricing Comparison

### Free Tier ($0/month)
- ✅ 750 hours/month
- ⚠️ Spins down after 15 min inactivity (cold start ~30 sec)
- ✅ 100 GB bandwidth
- ✅ Good for testing/development

### Starter Tier ($7/month)
- ✅ Always-on (no spin down)
- ✅ 100 GB bandwidth
- ✅ Faster builds
- ✅ Good for production

### Pro Tier ($25/month)
- ✅ More resources
- ✅ Auto-scaling
- ✅ Priority support

**Recommendation**: Start with **Free tier** for testing, upgrade to **Starter ($7/month)** for production

---

## After Deployment

### 1. Get Your API URL

After deployment completes, Render gives you a URL like:
```
https://tailorjob-api.onrender.com
```

### 2. Update Frontend API URL

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.PROD
  ? 'https://tailorjob-api.onrender.com/api'  // Render production URL
  : 'http://localhost:8000/api';              // Local development
```

Or use environment variable in Vercel:
```bash
# In Vercel Dashboard → Settings → Environment Variables
VITE_API_URL=https://tailorjob-api.onrender.com/api
```

### 3. Update CORS in Backend

Make sure backend allows Vercel domain:

```python
# backend/app/main.py (already configured)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allows all Vercel domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Test Deployment

```bash
# Test health endpoint
curl https://tailorjob-api.onrender.com/health

# Test API (with Supabase token)
curl https://tailorjob-api.onrender.com/api/cv/list \
  -H "Authorization: Bearer YOUR_SUPABASE_TOKEN"
```

---

## Dealing with Free Tier Spin-Down

If using free tier, the app spins down after 15 minutes of inactivity. Solutions:

### Option 1: Keep-Alive Ping Service
Use a free service to ping your app every 10 minutes:

1. **Cron-job.org**: https://cron-job.org/
   - Set URL: `https://tailorjob-api.onrender.com/health`
   - Interval: Every 10 minutes

2. **UptimeRobot**: https://uptimerobot.com/
   - Free tier monitors every 5 minutes
   - Keeps your app warm

### Option 2: Upgrade to Starter ($7/month)
- No spin-down
- Faster response times
- Better for production

---

## Environment Variables

Set these in Render Dashboard → Environment tab:

```bash
# Required
SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
SUPABASE_KEY=your_service_role_key

# Azure OpenAI
AZ_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZ_OPENAI_API_KEY=your_key
AZ_OPENAI_API_VERSION=2024-08-01-preview
AZ_OPENAI_DEPLOYMENT_NAME=your_deployment

# Optional (for production)
CORS_ORIGINS=["https://tailorjob.vercel.app"]
REDIS_URL=redis://...  # If using Redis
```

---

## Monitoring & Logs

### View Logs:
1. Go to Render Dashboard
2. Click on your service
3. Click **"Logs"** tab
4. Real-time logs appear here

### Monitor Health:
```bash
# Add health check endpoint (already exists in your backend)
curl https://tailorjob-api.onrender.com/health
```

---

## Auto-Deploy Setup

Render automatically deploys when you push to GitHub:

```bash
# Make changes to backend
cd backend
# ... edit files ...

# Commit and push
git add -A
git commit -m "fix: update API endpoint"
git push origin main

# Render automatically detects push and redeploys (takes 2-5 minutes)
```

---

## Troubleshooting

### Issue: Build fails
**Solution**: Check Render logs for Python dependency errors. May need to update `requirements.txt`

### Issue: App crashes on startup
**Solution**: Check environment variables are set correctly in Render dashboard

### Issue: 502 Bad Gateway
**Solution**: App is spinning down (free tier). Wait 30 seconds for cold start, or upgrade to Starter plan

### Issue: CORS errors from frontend
**Solution**: Verify `CORS_ORIGINS` includes your Vercel domain

---

## Quick Start Commands

```bash
# 1. Create render.yaml
cat > render.yaml << 'EOF'
services:
  - type: web
    name: tailorjob-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    plan: free
EOF

# 2. Commit and push
git add render.yaml
git commit -m "feat: add Render deployment config"
git push origin main

# 3. Go to render.com and create new web service from repo
# 4. Add environment variables
# 5. Deploy!
```

**Total time**: ~10 minutes
**Cost**: $0 (free tier) or $7/month (starter)

---

## Comparison: Render vs Others

| Platform | Free Tier | Paid | Setup Time | Ease |
|----------|-----------|------|------------|------|
| **Render** | ✅ $0 (spins down) | $7/month | 10 min | ⭐⭐⭐⭐⭐ |
| Railway | $5 credit | $5-20/month | 5 min | ⭐⭐⭐⭐⭐ |
| Heroku | ❌ None | $7/month | 15 min | ⭐⭐⭐⭐ |
| Azure App Service | ❌ None | $13/month | 30 min | ⭐⭐⭐ |

**Verdict**: Render is best for budget + simplicity!