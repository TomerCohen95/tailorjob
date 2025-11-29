
# Cheap/Free Backend Deployment Options

## 🏆 Best Free/Cheap Options (2024)

### 1. **Railway** - FREE $5/month credit (Recommended)
**Cost:** FREE (with $5 credit), then ~$5-8/month
**Setup Time:** < 5 minutes

```bash
# Steps:
1. Go to railway.app
2. Sign in with GitHub
3. New Project → Deploy from GitHub repo
4. Select: backend/ directory
5. Add env vars
6. Deploy!
```

**Pros:**
- ✅ $5/month free credit (covers light usage)
- ✅ Easiest setup
- ✅ Built-in Redis
- ✅ Auto-deploys from GitHub
- ✅ No credit card for free tier

**URL:** `https://tailorjob-production.up.railway.app`

---

### 2. **Render** - FREE tier
**Cost:** FREE (with limitations), or $7/month
**Setup Time:** ~10 minutes

```bash
# Steps:
1. Go to render.com
2. Sign in with GitHub
3. New → Web Service
4. Connect repo
5. Root: backend/
6. Build: pip install -r requirements.txt
7. Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
8. Deploy!
```

**Pros:**
- ✅ Completely FREE tier
- ✅ Good for side projects
- ✅ Auto-SSL
- ✅ Simple setup

**Cons:**
- ⚠️ Spins down after 15 min inactivity (slow cold start)
- ⚠️ 750 hours/month limit on free tier

**URL:** `https://tailorjob.onrender.com`

---

### 3. **Fly.io** - FREE $5/month credit
**Cost:** FREE (with $5 credit), then pay-as-you-go
**Setup Time:** ~10 minutes

```bash
# 1. Install flyctl
brew install flyctl  # macOS
# or: https://fly.io/docs/hands-on/install-flyctl/

# 2. Login
flyctl auth signup

# 3. Launch app
cd backend
flyctl launch --name tailorjob-api

# 4. Deploy
flyctl deploy
```

**Pros:**
- ✅ $5/month free allowance
- ✅ Fast global edge network
- ✅ No sleep/cold starts
- ✅ Modern platform

**URL:** `https://tailorjob-api.fly.dev`

---

### 4. **Koyeb** - FREE tier
**Cost:** FREE forever (with limits)
**Setup Time:** ~5 minutes

```bash
# Steps:
1. Go to koyeb.com
2. Sign in with GitHub  
3. Create Service → Deploy from GitHub
4. Select repo and backend/ directory
5. Set PORT=8000
6. Deploy!
```

**Pros:**
- ✅ FREE forever tier
- ✅ No sleep/cold starts
- ✅ Global edge network
- ✅ Simple setup

**Cons:**
- ⚠️ Limited to 2 services on free tier

**URL:** `https://tailorjob-api-yourorg.koyeb.app`

---

### 5. **Google Cloud Run** - Generous free tier
**Cost:** FREE for first 2M requests/month
**Setup Time:** ~15 minutes

```bash
# 1. Create backend/Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 2. Deploy
cd backend
gcloud run deploy tailorjob-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

**Pros:**
- ✅ 2M requests/month FREE
- ✅ Scales to zero (no cost when idle)
- ✅ Fast cold starts
- ✅ Google infrastructure

**URL:** `https://tailorjob-api-xyz.run.app`

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid (if needed) | Cold Starts | Setup |
|----------|-----------|------------------|-------------|-------|
| **Railway** | $5 credit/mo | ~$5-8/mo | No | 5 min |
| **Render** | Yes (limited) | $7/mo | Yes (15min) | 10 min |
| **Fly.io** | $5 credit/mo | Pay-as-you-go | No | 10 min |
| **Koyeb** | Forever free | $5/mo | No | 5 min |
| **Cloud Run** | 2M req/mo | Pay-per-use | Minimal | 15 min |

---

## 🎯 My Recommendation for Your App

### **Use Koyeb** (Best value)

**Why:**
1. ✅ **FREE forever** (not just a trial)
2. ✅ **No cold starts** (always running)
3. ✅ **Easy setup** (< 5 minutes)
4. ✅ **Auto-deploys** from GitHub
5. ✅ **Fast** (edge network)

### Quick Setup (Koyeb):

```bash
1. Go to: https://www.koyeb.com/
2. Sign in with GitHub
3. Click "Create Service"
4. Choose "GitHub" as source
5. Select repository: tomercohen/tailorjob
6. Builder: Dockerfile
7. Set working directory: backend
8. Environment variables:
   - SUPABASE_URL
   - SUPABASE_KEY
   - AZ_OPENAI_ENDPOINT
   - AZ_OPENAI_API_KEY
9. Click "Deploy"
10. Done! Get your URL: https://tailorjob-api-yourorg.koyeb.app
```

---

## Alternative: Deploy Backend on Vercel (NEW!)

**Vercel now supports Python!**

Create `api/index.py` in root:
```python
from backend.app.main import app

# Vercel serverless function
def handler(request):
    return app(request)
```

Add `vercel.json`:
```json
{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

**Pros:**
- ✅ FREE (same account as frontend)
- ✅ Same domain
- ✅ Serverless
- ✅ Auto-deploys

**Cons:**
- ⚠️ 10s timeout (may be tight for CV parsing)
- ⚠️ Serverless (no background workers)

---

## Redis Considerations

Most CV processing needs background jobs (Redis). Here's what each platform offers:

| Platform | Redis | Cost |
|----------|-------|------|
| **Railway** | ✅ Built-in | FREE (in credit) |
| **Render** | ✅ Add-on | $7/mo |
| **Fly.io** | ✅ Upstash | FREE tier |
| **Koyeb** | ❌ Use external | Upstash FREE |
| **Cloud Run** | ❌ Use external | Upstash FREE |

**Free Redis Option:** [Upstash](https://upstash.com/)
- 10,000 commands/day FREE
- Perfect for background jobs
- Easy setup

---

## Final Recommendation

### For Your App (with CV parsing workers):

**Best Option: Railway**
- $5/month credit covers backend + Redis
- No cold starts
- Perfect for background workers
- Auto-deploys from GitHub
- Super simple setup

### If Budget is Zero:

**Best Option: Koyeb + Upstash Redis**
- Koyeb: FREE forever (backend)
- Upstash: FREE tier (Redis)
- Total: $0/month
- Good performance
- No cold starts

---

## Setup Railway (Recommended)

```bash
1. Go to: https://railway.app/
2. "Start a New Project"
3. "Deploy from GitHub repo"
4. Select: tomercohen/tailorjob
5. Set root directory: backend
6. Add services:
   - Web (FastAPI) - auto-detected
   - Redis - click "Add Redis"
7. Environment variables (in FastAPI service):
   SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
   SUPABASE_KEY=your_key
   AZ_OPENAI_ENDPOINT=your_endpoint
   AZ_OPENAI_API_KEY=your_key
   REDIS_URL=${{Redis.REDIS_URL}}  # Auto-linked!
8. Deploy!
```

**Result:** 
- Backend URL: `https://tailorjob-production.up.railway.app`
- Cost: $0/month (covered by free credit for small usage)

---

## Update Frontend

After deployment, update [`src/lib/api.ts`](../src/lib/api.ts:3):

```typescript
const API_BASE_URL = import.meta.env.PROD
  ? 'https://tailorjob-production.up.railway.app/api'
  : 'http://localhost:8000/api';
```

Or use Vercel environment variable:
```bash
# Vercel Dashboard → Settings → Environment Variables
VITE_API_URL=https://tailorjob-production.up.railway.app/api
```

Then:
```typescript
