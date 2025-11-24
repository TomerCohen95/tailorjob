# Testing Guide - TailorJob Backend

## 🧪 How to Test the Functionality

This guide walks you through testing the backend functionality step-by-step.

---

## Prerequisites

Before testing, make sure you've completed:

1. ✅ Applied database migrations (done)
2. ⏳ Configured `backend/.env` with credentials
3. ⏳ Created `cv-uploads` storage bucket in Supabase
4. ⏳ Started the backend server

---

## Quick Setup for Testing

### 1. Get Your Supabase Credentials

```bash
# Go to: https://supabase.com/dashboard
# Select your project → Settings → API

# You need:
# - Project URL (e.g., https://xxxyyy.supabase.co)
# - service_role key (NOT the anon key!)
```

### 2. Set Minimal .env for Testing

For basic testing, you only need Supabase credentials:

```bash
# Edit backend/.env
code backend/.env
```

Add:
```env
# Required for basic testing
SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Optional for now (can test without these)
UPSTASH_REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 3. Create Storage Bucket

**Option A: Via Supabase Dashboard**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **Storage** in left sidebar
4. Click **New Bucket**
5. Name: `cv-uploads`
6. **Public**: Unchecked (keep private)
7. Click **Create**

**Option B: Via SQL (faster)**
```bash
supabase db query "
INSERT INTO storage.buckets (id, name, public)
VALUES ('cv-uploads', 'cv-uploads', false)
ON CONFLICT DO NOTHING;
"
```

### 4. Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
🚀 Starting TailorJob API...
✓ Background workers started (placeholder)
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## Testing Methods

You have 4 ways to test:

### Method 1: Swagger UI (Easiest - Visual Interface)
### Method 2: curl Commands (Terminal)
### Method 3: Python Script (Automated)
### Method 4: Frontend Integration (Real Use Case)

---

## Method 1: Swagger UI Testing (Recommended for Beginners)

### Step 1: Open Swagger UI

Visit: **http://localhost:8000/docs**

You'll see all API endpoints with "Try it out" buttons.

### Step 2: Test Unauthenticated Endpoint

1. Find `/health` endpoint
2. Click **"Try it out"**
3. Click **"Execute"**
4. You should see:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0"
   }
   ```

### Step 3: Get Authentication Token

**Option A: From Frontend (if running)**
1. Open your frontend: http://localhost:5173
2. Sign in with Google
3. Open browser console (F12)
4. Run:
   ```javascript
   const { data } = await supabase.auth.getSession()
   console.log(data.session.access_token)
   ```
5. Copy the token

**Option B: Create Test Token via Supabase**
```bash
# Get a test user token
supabase db query "
SELECT auth.sign(
  json_build_object(
    'sub', id::text,
    'role', 'authenticated',
    'exp', extract(epoch from now() + interval '1 hour')
  ),
  (SELECT decryption_secret FROM vault.secrets WHERE name = 'jwt_secret')::text
) as token
FROM auth.users LIMIT 1;
"
```

### Step 4: Authorize in Swagger

1. Click the **"Authorize"** button (top right with lock icon)
2. Enter: `Bearer YOUR_TOKEN_HERE`
3. Click **"Authorize"**
4. Click **"Close"**

### Step 5: Test Authenticated Endpoints

**Test: List CVs**
1. Find `GET /api/cv/` endpoint
2. Click **"Try it out"**
3. Click **"Execute"**
4. Should return: `[]` (empty list, no CVs yet)

**Test: Create Job**
1. Find `POST /api/jobs/` endpoint
2. Click **"Try it out"**
3. Edit the request body:
   ```json
   {
     "title": "Senior Software Engineer",
     "company": "TechCorp",
     "description": "Looking for a senior engineer with Python and React experience",
     "url": "https://example.com/jobs/123"
   }
   ```
4. Click **"Execute"**
5. Should return the created job with an `id`

**Test: List Jobs**
1. Find `GET /api/jobs/` endpoint
2. Click **"Try it out"**
3. Click **"Execute"**
4. Should return the job you just created

**Test: Upload CV** (requires file)
1. Find `POST /api/cv/upload` endpoint
2. Click **"Try it out"**
3. Click **"Choose File"** and select a PDF or DOCX
4. Click **"Execute"**
5. Should return:
   ```json
   {
     "id": "uuid-here",
     "filename": "your-cv.pdf",
     "status": "uploaded",
     "message": "CV uploaded successfully. Parsing queued."
   }
   ```

---

## Method 2: curl Commands Testing

### Test 1: Health Check (No Auth)

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"healthy","version":"1.0.0"}
```

### Test 2: Get JWT Token

First, sign in via frontend and get token:
```bash
# Store your token in a variable
TOKEN="your-jwt-token-here"
```

### Test 3: List CVs

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cv/
```

### Test 4: Create Job

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Backend Developer",
    "company": "StartupXYZ",
    "description": "Python, FastAPI, PostgreSQL experience required",
    "url": "https://example.com/job/456"
  }' \
  http://localhost:8000/api/jobs/
```

### Test 5: Upload CV

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/cv.pdf" \
  http://localhost:8000/api/cv/upload
```

### Test 6: Get Job by ID

```bash
# Replace JOB_ID with actual ID from previous response
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/jobs/JOB_ID
```

---

## Method 3: Automated Python Test Script

Create `backend/test_api.py`:

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token-here"  # Get from frontend

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_health():
    print("\n1. Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200

def test_list_cvs():
    print("\n2. Testing GET /api/cv/...")
    response = requests.get(f"{BASE_URL}/api/cv/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"CVs: {response.json()}")
    assert response.status_code == 200

def test_create_job():
    print("\n3. Testing POST /api/jobs/...")
    job_data = {
        "title": "Test Engineer",
        "company": "Test Corp",
        "description": "Testing the API",
        "url": "https://example.com"
    }
    response = requests.post(
        f"{BASE_URL}/api/jobs/",
        headers=headers,
        json=job_data
    )
    print(f"Status: {response.status_code}")
    print(f"Created Job: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    return response.json()["id"]

def test_list_jobs():
    print("\n4. Testing GET /api/jobs/...")
    response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Jobs: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_get_job(job_id):
    print(f"\n5. Testing GET /api/jobs/{job_id}...")
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Job: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_upload_cv():
    print("\n6. Testing POST /api/cv/upload...")
    # Create a dummy PDF file for testing
    files = {
        'file': ('test-cv.pdf', b'%PDF-1.4 dummy content', 'application/pdf')
    }
    headers_no_content = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        f"{BASE_URL}/api/cv/upload",
        headers=headers_no_content,
        files=files
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

if __name__ == "__main__":
    print("🧪 Starting API Tests...\n")
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {TOKEN[:20]}..." if TOKEN != "your-jwt-token-here" else "⚠️  Please set your JWT token!")
    
    if TOKEN == "your-jwt-token-here":
        print("\n❌ Error: Please set your JWT token in the script")
        exit(1)
    
    try:
        test_health()
        test_list_cvs()
        job_id = test_create_job()
        test_list_jobs()
        test_get_job(job_id)
        test_upload_cv()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
```

Run it:
```bash
cd backend
source venv/bin/activate
pip install requests  # If not already installed
python test_api.py
```

---

## Method 4: Frontend Integration Testing

### Step 1: Update Frontend to Use Real API

Create `src/lib/api.ts`:

```typescript
import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = 'http://localhost:8000';

async function getAuthHeaders() {
  const { data } = await supabase.auth.getSession();
  if (!data.session) throw new Error('Not authenticated');
  
  return {
    'Authorization': `Bearer ${data.session.access_token}`,
    'Content-Type': 'application/json'
  };
}

export async function uploadCV(file: File) {
  const headers = await getAuthHeaders();
  delete headers['Content-Type']; // Let browser set it for FormData
  
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/cv/upload`, {
    method: 'POST',
    headers,
    body: formData
  });
  
  return response.json();
}

export async function listCVs() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/api/cv/`, { headers });
  return response.json();
}

export async function createJob(jobData: {
  title: string;
  company: string;
  description: string;
  url?: string;
}) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/api/jobs/`, {
    method: 'POST',
    headers,
    body: JSON.stringify(jobData)
  });
  return response.json();
}

export async function listJobs() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/api/jobs/`, { headers });
  return response.json();
}
```

### Step 2: Test from Browser Console

Open http://localhost:5173, sign in, then in console:

```javascript
// Test health
fetch('http://localhost:8000/health').then(r => r.json()).then(console.log)

// Test authenticated endpoint
const { data } = await supabase.auth.getSession()
const token = data.session.access_token

fetch('http://localhost:8000/api/cv/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(console.log)
```

---

## Checking Results in Database

### View Created Data

```bash
# List all CVs
supabase db query "SELECT * FROM cvs;"

# List all jobs
supabase db query "SELECT * FROM jobs;"

# List all CV sections (parsed data)
supabase db query "SELECT * FROM cv_sections;"

# Check storage files
supabase db query "SELECT * FROM storage.objects WHERE bucket_id = 'cv-uploads';"
```

---

## Common Issues & Solutions

### Issue 1: "Unauthorized" Error

**Problem**: API returns 401 Unauthorized

**Solutions**:
- Check token is valid (not expired)
- Verify you're using `Bearer TOKEN` format
- Make sure you're using service_role key in backend .env
- Regenerate token from frontend

### Issue 2: "CORS Error"

**Problem**: Browser blocks request

**Solution**: Backend already has CORS enabled for localhost:5173. If using different port:
```python
# backend/app/main.py
origins = [
    "http://localhost:5173",
    "http://localhost:3000",  # Add your port
]
```

### Issue 3: "Storage bucket not found"

**Problem**: CV upload fails with bucket error

**Solution**:
```bash
# Create bucket via SQL
supabase db query "
INSERT INTO storage.buckets (id, name, public)
VALUES ('cv-uploads', 'cv-uploads', false);
"
```

### Issue 4: "Connection refused"

**Problem**: Can't connect to localhost:8000

**Solutions**:
- Make sure backend is running: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
- Check port 8000 isn't used: `lsof -i :8000`
- Try different port: `uvicorn app.main:app --reload --port 8080`

---

## Testing Checklist

Use this checklist to verify everything works:

- [ ] Backend server starts without errors
- [ ] `/health` endpoint returns 200
- [ ] Can get JWT token from frontend
- [ ] `GET /api/cv/` returns empty list (first time)
- [ ] `POST /api/jobs/` creates job successfully
- [ ] `GET /api/jobs/` returns created job
- [ ] `GET /api/jobs/{id}` returns specific job
- [ ] `PUT /api/jobs/{id}` updates job
- [ ] `POST /api/cv/upload` uploads file to storage
- [ ] `GET /api/cv/` returns uploaded CV
- [ ] Can see data in Supabase dashboard
- [ ] Can see uploaded file in Storage bucket

---

## Next: Full Integration Testing

Once basic endpoints work, you can test:

1. **CV Parsing** (after implementing parser):
   - Upload PDF → Check status changes to 'parsing' → 'completed'
   - Verify cv_sections table has parsed data

2. **AI Tailoring** (after implementing AI service):
   - Create tailored CV from existing CV + job
   - Check tailored_cvs table

3. **Chat Feature** (after implementing chat):
   - Send chat message
   - Receive AI response
   - Check chat_messages table

---

## Performance Testing

```bash
# Install Apache Bench (if not installed)
brew install httpd  # macOS

# Test health endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health

# Test authenticated endpoint (with token)
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/cv/
```

---

## Summary

**Quick Start Testing:**
1. Configure `.env` with Supabase credentials
2. Create `cv-uploads` storage bucket
3. Start backend: `uvicorn app.main:app --reload`
4. Open Swagger UI: http://localhost:8000/docs
5. Get token from frontend console
6. Click "Authorize" in Swagger
7. Try endpoints with "Try it out" button

**Best practices:**
- Start with Swagger UI (easiest)
- Use curl for automation
- Use Python script for CI/CD
- Test frontend integration last