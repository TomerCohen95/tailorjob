# Getting Started with TailorJob Backend

## 🎯 What We've Built So Far

✅ **Database Schema** - 6 tables for CVs, jobs, tailored versions  
✅ **FastAPI Backend** - REST API with authentication  
✅ **File Upload** - CV upload to Supabase Storage  
✅ **Job Management** - CRUD operations for job descriptions  
✅ **Queue System** - Redis-based background jobs (structure ready)  

⏳ **Coming Next**: CV parser, AI tailoring, background workers

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Apply Database Migration

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **SQL Editor** → **New Query**
4. Copy content from `supabase/migrations/20240122000000_add_cv_tables.sql`
5. Paste and click **Run**

### Step 2: Create Storage Bucket

In Supabase Dashboard → **Storage**:
1. Click **New Bucket**
2. Name: `cv-uploads`
3. Set to **Private**
4. Click **Create**

### Step 3: Set Up Backend

```bash
cd backend
./setup.sh
```

### Step 4: Get Your Credentials

#### Supabase (Database, Auth, Storage)
- Go to Supabase Dashboard → **Settings** → **API**
- Copy:
  - `URL` → `SUPABASE_URL`
  - `service_role` key → `SUPABASE_KEY` (⚠️ Not the anon key!)

#### Upstash (Redis Queue)
1. Sign up at https://upstash.com (free)
2. Create Redis database
3. Copy connection URL → `UPSTASH_REDIS_URL`

#### Azure OpenAI (AI Features)
1. Go to Azure Portal
2. Create OpenAI resource (or use existing)
3. Copy:
   - Endpoint → `AZURE_OPENAI_ENDPOINT`
   - Key → `AZURE_OPENAI_KEY`

### Step 5: Configure .env

Edit `backend/.env`:

```env
SUPABASE_URL=https://xxxyyy.supabase.co
SUPABASE_KEY=eyJhbG...  # service_role key
UPSTASH_REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=abc123...
```

### Step 6: Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

You should see:
```
🚀 Starting TailorJob API...
✓ Background workers started (placeholder)
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Test It!

Open http://localhost:8000/docs

You should see the Swagger UI with all API endpoints.

---

## 📊 Current Architecture

```
┌─────────────────────┐
│  Frontend (5173)    │  ← Already running
│  React + Vite       │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Backend (8000)     │  ← Just created!
│  FastAPI            │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────────────────┐
│  External Services (Cloud)      │
│  ├─ Supabase (DB + Auth)        │
│  ├─ Upstash (Redis)             │
│  └─ Azure OpenAI (AI)           │
└─────────────────────────────────┘
```

---

## 🧪 Testing the API

### 1. Health Check (No Auth)

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status": "healthy", "version": "1.0.0"}
```

### 2. Get JWT Token

In your frontend (http://localhost:5173):
1. Sign in with Google
2. Open browser DevTools → Console
3. Run:
```javascript
const { data } = await supabase.auth.getSession()
console.log(data.session.access_token)
```
4. Copy the token

### 3. Test Upload Endpoint

In Swagger UI (http://localhost:8000/docs):
1. Click **Authorize** button
2. Enter: `Bearer YOUR_TOKEN_HERE`
3. Try `/api/cv/upload` endpoint with a PDF

---

## 📁 What Files Were Created

```
backend/
├── app/
│   ├── main.py                    ✅ FastAPI app
│   ├── config.py                  ✅ Settings
│   ├── api/
│   │   ├── deps.py                ✅ Auth middleware
│   │   └── routes/
│   │       ├── cv.py              ✅ CV endpoints
│   │       ├── jobs.py            ✅ Job endpoints
│   │       └── tailor.py          ✅ Tailoring (placeholder)
│   ├── services/
│   │   ├── queue.py               ✅ Redis queue
│   │   └── storage.py             ✅ File storage
│   └── utils/
│       └── supabase_client.py     ✅ DB client
├── requirements.txt               ✅ Dependencies
├── .env.example                   ✅ Config template
├── setup.sh                       ✅ Setup script
└── README.md                      ✅ Documentation

supabase/migrations/
└── 20240122000000_add_cv_tables.sql  ✅ Database schema
```

---

## 🎯 What Works Right Now

### ✅ Working Endpoints

**CV Management**
- `POST /api/cv/upload` - Upload CV file
- `GET /api/cv/` - List all CVs
- `GET /api/cv/{id}` - Get CV details
- `DELETE /api/cv/{id}` - Delete CV

**Job Management**
- `POST /api/jobs/` - Create job
- `GET /api/jobs/` - List jobs
- `GET /api/jobs/{id}` - Get job
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### ⏳ Not Implemented Yet

- CV Parsing (file uploads but doesn't parse)
- AI Tailoring (endpoint exists but placeholder)
- Background Workers (structure ready)
- Chat functionality (placeholder)
- PDF Export (not yet)

---

## 🐛 Common Issues

### "Command not found: uvicorn"
```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate
```

### "Cannot connect to Supabase"
- Check you're using **service_role** key, not anon key
- Verify `SUPABASE_URL` format: `https://xxx.supabase.co`

### "CORS error from frontend"
- Make sure backend is running on port 8000
- Check `CORS_ORIGINS` in `.env` includes `http://localhost:5173`

### "Module 'app' not found"
```bash
# Run from backend directory
cd backend
python -m uvicorn app.main:app --reload
```

---

## 📝 Next Steps

Now that basic backend is running, we need to implement:

1. **CV Parser** - Extract text from PDFs/DOCX → Send to Azure OpenAI → Structure data
2. **Background Workers** - Process uploaded CVs asynchronously
3. **AI Tailoring** - Match CV to job description → Generate tailored version
4. **Frontend Integration** - Update frontend to use real API instead of mock data

Would you like me to implement any of these next? I recommend starting with the CV parser since it's foundational for everything else.

---

## 🔗 Useful Links

- **API Docs**: http://localhost:8000/docs
- **Backend README**: `backend/README.md`
- **MVP Plan**: `MVP_IMPLEMENTATION_PLAN.md`
- **Database Schema**: `DATABASE_SCHEMA_EXPLAINED.md`
- **Architecture**: `FREE_TIER_ARCHITECTURE.md`