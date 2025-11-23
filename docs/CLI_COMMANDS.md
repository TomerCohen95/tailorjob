# CLI Commands Guide

## What You Can Do With CLI

Since you don't have Supabase CLI installed, here's what you can do with standard CLI tools and what Supabase CLI would enable.

---

## 🟢 Available NOW (No Supabase CLI Required)

### 1. Install Supabase CLI
```bash
# Install via Homebrew (macOS)
brew install supabase/tap/supabase

# Or via npm
npm install -g supabase
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Run automated setup (creates venv, installs dependencies)
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Start backend server
uvicorn app.main:app --reload

# Or with custom port
uvicorn app.main:app --reload --port 8080
```

### 3. Python Package Management
```bash
cd backend

# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Install all dependencies
pip install -r requirements.txt
```

### 4. Database Migration (Manual - Without CLI)
```bash
# Since you don't have Supabase CLI, you have 2 options:

# Option A: Copy-paste SQL in Supabase Dashboard
# 1. Open https://supabase.com/dashboard
# 2. Go to SQL Editor → New Query
# 3. Copy content from: supabase/migrations/20240122000000_add_cv_tables.sql
# 4. Paste and run

# Option B: Use psql directly (if you have it)
psql "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres" \
  -f supabase/migrations/20240122000000_add_cv_tables.sql
```

### 5. Git Commands (for version control)
```bash
# Check status
git status

# Create feature branch
git checkout -b feature/backend-api

# Add all files
git add .

# Commit changes
git commit -m "Add FastAPI backend structure"

# Push to remote
git push origin feature/backend-api

# Create suggested branch (as you requested)
git checkout -b user/tomercohen/backend-foundation
git add .
git commit -m "Add FastAPI backend with CV upload, job management, and queue system"
git push origin user/tomercohen/backend-foundation
```

### 6. File Operations
```bash
# Create directories
mkdir -p backend/app/services backend/app/workers

# Copy files
cp backend/.env.example backend/.env

# View file contents
cat backend/app/config.py

# Edit files
nano backend/.env
# or
code backend/.env  # Opens in VS Code
```

### 7. Check Running Processes
```bash
# See what's running on port 8000
lsof -i :8000

# Kill process on port 8000 (if needed)
kill -9 $(lsof -t -i:8000)

# Check all Python processes
ps aux | grep python

# Check all Node processes
ps aux | grep node
```

### 8. Environment Setup
```bash
# Check Python version
python --version
python3 --version

# Check Node version
node --version
npm --version

# Check installed packages
pip list
npm list -g --depth=0
```

### 9. Test Backend Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with authentication
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/cv/

# Upload CV (example)
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/cv.pdf" \
  http://localhost:8000/api/cv/upload
```

### 10. View Logs
```bash
# View backend logs (if running in background)
tail -f backend/logs/app.log

# View npm dev server logs
# (already running in your terminals)
```

---

## 🟡 Available WITH Supabase CLI (After Installation)

### 1. Initialize Supabase Project
```bash
# Link to existing project
supabase link --project-ref your-project-ref

# This creates supabase/.temp/ with local config
```

### 2. Database Migrations (Automated)
```bash
# Apply pending migrations
supabase db push

# Create new migration
supabase migration new add_new_feature

# Reset database (CAREFUL - deletes all data)
supabase db reset

# Generate TypeScript types from database
supabase gen types typescript --local > src/integrations/supabase/types.ts
```

### 3. Local Development (Optional)
```bash
# Start local Supabase stack (Docker required)
supabase start

# This starts:
# - PostgreSQL database (local)
# - PostgREST API
# - Auth server
# - Storage server
# - Studio UI (http://localhost:54323)

# Stop local stack
supabase stop
```

### 4. Database Inspection
```bash
# Run SQL query
supabase db query "SELECT * FROM profiles LIMIT 10"

# Dump database schema
supabase db dump --schema public

# Generate migration from schema diff
supabase db diff --schema public
```

### 5. Functions (Edge Functions)
```bash
# Create new edge function
supabase functions new my-function

# Deploy function
supabase functions deploy my-function

# View function logs
supabase functions logs my-function
```

### 6. Storage Management
```bash
# List storage buckets
supabase storage ls

# Upload file to storage
supabase storage upload cv-uploads/test.pdf ./test.pdf

# Download file from storage
supabase storage download cv-uploads/test.pdf
```

### 7. Secrets Management
```bash
# Set secret for edge functions
supabase secrets set MY_SECRET=value

# List secrets
supabase secrets list

# Unset secret
supabase secrets unset MY_SECRET
```

---

## 🎯 Recommended CLI Workflow

### Initial Setup (One Time)
```bash
# 1. Install Supabase CLI (optional but recommended)
brew install supabase/tap/supabase

# 2. Set up backend
cd backend
./setup.sh
cp .env.example .env
# Edit .env with your credentials

# 3. Link to Supabase project (if you installed CLI)
supabase link --project-ref YOUR_PROJECT_REF

# 4. Apply migrations
# Option A (with CLI):
supabase db push

# Option B (without CLI):
# Copy SQL from supabase/migrations/20240122000000_add_cv_tables.sql
# Paste in Supabase Dashboard → SQL Editor
```

### Daily Development
```bash
# Terminal 1: Frontend (already running)
npm run dev

# Terminal 2: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Free for commands
git status
git add .
git commit -m "Add new feature"
```

### Before Deploying
```bash
# 1. Create branch
git checkout -b user/tomercohen/feature-name

# 2. Run any tests (when you add them)
cd backend
pytest

# 3. Commit and push
git add .
git commit -m "Descriptive message"
git push origin user/tomercohen/feature-name
```

---

## 🚀 Quick Commands for Your Current Task

### Apply Database Migration
```bash
# Without CLI - Manual method:
# 1. Go to https://supabase.com/dashboard
# 2. Select your project
# 3. SQL Editor → New Query
# 4. Copy/paste from: supabase/migrations/20240122000000_add_cv_tables.sql
# 5. Click Run

# With CLI (after installation):
supabase db push
```

### Start Backend
```bash
cd backend
./setup.sh                    # First time only
source venv/bin/activate
uvicorn app.main:app --reload
```

### Create and Push Branch (as you requested)
```bash
git checkout -b user/tomercohen/backend-foundation
git add .
git commit -m "Add FastAPI backend with CV upload, jobs, and queue system"
git push origin user/tomercohen/backend-foundation
```

### Test Backend
```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

---

## 📚 Additional Resources

- **Supabase CLI Docs**: https://supabase.com/docs/guides/cli
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **uvicorn Options**: https://www.uvicorn.org/settings/

---

## What Should You Do First?

1. **Install Supabase CLI** (optional but helpful):
   ```bash
   brew install supabase/tap/supabase
   ```

2. **Apply Database Migration** (required):
   - Go to Supabase Dashboard → SQL Editor
   - Copy SQL from `supabase/migrations/20240122000000_add_cv_tables.sql`
   - Run it

3. **Set Up Backend** (required):
   ```bash
   cd backend
   ./setup.sh
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Start Backend** (to test):
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

5. **Create Branch** (as you prefer):
   ```bash
   git checkout -b user/tomercohen/backend-foundation
   git add .
   git commit -m "Add backend structure"
   git push origin user/tomercohen/backend-foundation