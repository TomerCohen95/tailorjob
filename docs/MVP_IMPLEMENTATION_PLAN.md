# TailorJob.ai - Complete MVP Implementation Plan

## 🎯 MVP Goal

Build a **working CV tailoring platform** where users can:
1. ✅ Sign up/Login with Google (Already working)
2. 📄 Upload their CV and get it parsed
3. 💼 Add job descriptions
4. 🤖 Get AI-tailored CV versions
5. 💬 Chat with AI to refine CVs
6. 📥 Export tailored CVs as PDF

**Timeline**: 2-3 weeks (10-15 days)  
**Budget**: $0-30/month (free tiers + Azure credits)

---

## 📊 Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| **Frontend** | React + Vite + TypeScript ✅ | Free (Vercel) |
| **Backend** | Python + FastAPI | Free (Render 750hrs) |
| **Database** | PostgreSQL | Free (Supabase 500MB) |
| **Auth** | OAuth | Free (Supabase) ✅ |
| **Storage** | File storage | Free (Supabase 1GB) |
| **Queue** | Redis | Free (Upstash 10k/day) |
| **AI** | GPT-4 | $20-30 (Azure credits) |

---

## 🗓️ Implementation Phases

```
Phase 1: Database & Infrastructure (Days 1-2)
  ├─ Database migrations
  ├─ Supabase Storage setup
  └─ External services (Upstash, Azure OpenAI)

Phase 2: Backend Core (Days 3-5)
  ├─ FastAPI project structure
  ├─ Authentication middleware
  ├─ Core services setup
  └─ Queue infrastructure

Phase 3: CV Processing (Days 6-8)
  ├─ File upload endpoint
  ├─ Storage service
  ├─ CV parser (PDF/DOCX)
  └─ Background worker

Phase 4: Job Management (Days 9-10)
  ├─ CRUD endpoints
  └─ Frontend integration

Phase 5: AI Tailoring (Days 11-13)
  ├─ AI tailoring service
  ├─ Chat functionality
  └─ Revision tracking

Phase 6: Export & Polish (Days 14-15)
  ├─ PDF export
  ├─ Frontend integration
  └─ Testing & deployment
```

---

## 📋 Detailed Implementation

---

## **PHASE 1: Database & Infrastructure** (Days 1-2)

### **Day 1 Morning: Database Schema**

Create: `supabase/migrations/20240122000000_add_cv_tables.sql`

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- CVs Table (File Metadata)
CREATE TABLE cvs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  original_filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size INTEGER,
  mime_type TEXT,
  status TEXT NOT NULL DEFAULT 'uploaded',
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  parsed_at TIMESTAMPTZ,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CV Sections (Parsed Data)
CREATE TABLE cv_sections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
  summary TEXT,
  skills JSONB DEFAULT '[]'::jsonb,
  experience JSONB DEFAULT '[]'::jsonb,
  education JSONB DEFAULT '[]'::jsonb,
  certifications JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(cv_id)
);

-- Jobs Table
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  description TEXT NOT NULL,
  url TEXT,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tailored CVs
CREATE TABLE tailored_cvs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  format TEXT DEFAULT 'markdown',
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CV Revisions
CREATE TABLE cv_revisions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tailored_cv_id UUID NOT NULL REFERENCES tailored_cvs(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  revision_type TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tailored_cv_id UUID NOT NULL REFERENCES tailored_cvs(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cvs_user_id ON cvs(user_id);
CREATE INDEX idx_cvs_status ON cvs(status);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_tailored_cvs_user_id ON tailored_cvs(user_id);
CREATE INDEX idx_tailored_cvs_cv_job ON tailored_cvs(cv_id, job_id);
CREATE INDEX idx_chat_messages_tailored_cv ON chat_messages(tailored_cv_id);

-- Enable RLS
ALTER TABLE cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE tailored_cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage own CVs"
  ON cvs FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage own CV sections"
  ON cv_sections FOR ALL
  USING (EXISTS (
    SELECT 1 FROM cvs WHERE cvs.id = cv_sections.cv_id AND cvs.user_id = auth.uid()
  ));

CREATE POLICY "Users can manage own jobs"
  ON jobs FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage own tailored CVs"
  ON tailored_cvs FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own revisions"
  ON cv_revisions FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM tailored_cvs 
    WHERE tailored_cvs.id = cv_revisions.tailored_cv_id 
    AND tailored_cvs.user_id = auth.uid()
  ));

CREATE POLICY "Users can view own chat messages"
  ON chat_messages FOR ALL
  USING (EXISTS (
    SELECT 1 FROM tailored_cvs 
    WHERE tailored_cvs.id = chat_messages.tailored_cv_id 
    AND tailored_cvs.user_id = auth.uid()
  ));

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cvs_updated_at
  BEFORE UPDATE ON cvs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cv_sections_updated_at
  BEFORE UPDATE ON cv_sections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tailored_cvs_updated_at
  BEFORE UPDATE ON tailored_cvs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Apply migration**:
```bash
cd supabase
supabase db push
```

### **Day 1 Afternoon: Supabase Storage**

1. Go to Supabase Dashboard → Storage
2. Create bucket: `cv-uploads`
3. Set to `private`
4. Add storage policies:

```sql
CREATE POLICY "Users can upload own CVs"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'cv-uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can read own CVs"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'cv-uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can delete own CVs"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'cv-uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

### **Day 2: External Services**

#### **Setup Upstash Redis** (5 min)
1. Sign up at https://upstash.com
2. Create database (free tier)
3. Copy `UPSTASH_REDIS_URL`

#### **Setup Azure OpenAI** (15 min)
```bash
# Create resource
az cognitiveservices account create \
  --name tailorjob-openai \
  --resource-group tailorjob-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4
az cognitiveservices account deployment create \
  --name tailorjob-openai \
  --resource-group tailorjob-rg \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613"
```

Save:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`

---

## **PHASE 2: Backend Core** (Days 3-5)

### **Day 3: Project Setup**

```bash
# Create backend directory
mkdir backend
cd backend

# Python virtual environment
python -m venv venv
source venv/bin/activate

# Project structure
mkdir -p app/{api/{routes},services,models,workers,utils}
touch app/__init__.py
touch app/{main,config}.py
touch app/api/__init__.py
touch app/api/deps.py
```

**requirements.txt**:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Supabase
supabase==2.3.4

# Redis
redis==5.0.1

# Azure OpenAI
openai==1.10.0

# Document processing
PyPDF2==3.0.1
python-docx==1.1.0
python-multipart==0.0.6

# PDF generation
weasyprint==60.2

# Utilities
httpx==0.26.0
python-jose[cryptography]==3.3.0
```

```bash
pip install -r requirements.txt
```

**app/config.py**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_TITLE: str = "TailorJob API"
    API_VERSION: str = "1.0.0"
    
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    UPSTASH_REDIS_URL: str
    
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4"
    
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**.env**:
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_service_role_key
UPSTASH_REDIS_URL=redis://xxx
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_KEY=xxx
```

### **Day 4: Core Services**

**app/utils/supabase_client.py**:
```python
from supabase import create_client, Client
from app.config import settings

def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

supabase = get_supabase()
```

**app/api/deps.py**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.supabase_client import supabase

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        return user_response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
```

**app/services/queue.py**:
```python
import redis.asyncio as redis
import json
import uuid
from typing import Dict, Any, Optional
from app.config import settings

class QueueService:
    def __init__(self):
        self.redis = redis.from_url(
            settings.UPSTASH_REDIS_URL,
            decode_responses=True
        )
        
        self.CV_PARSE_QUEUE = "queue:cv-parse"
        self.AI_TAILOR_QUEUE = "queue:ai-tailor"
    
    async def enqueue(self, queue_name: str, data: Dict[str, Any]) -> str:
        job_id = data.get("id", str(uuid.uuid4()))
        await self.redis.lpush(queue_name, json.dumps(data))
        await self.redis.setex(f"job:{job_id}:status", 3600, "queued")
        return job_id
    
    async def dequeue(self, queue_name: str, timeout: int = 5) -> Optional[Dict]:
        result = await self.redis.brpop(queue_name, timeout=timeout)
        if result:
            _, job_data = result
            return json.loads(job_data)
        return None
    
    async def set_job_status(self, job_id: str, status: str, result: Any = None):
        await self.redis.setex(f"job:{job_id}:status", 3600, status)
        if result:
            await self.redis.setex(f"job:{job_id}:result", 3600, json.dumps(result))
    
    async def get_job_status(self, job_id: str) -> Dict:
        status = await self.redis.get(f"job:{job_id}:status")
        result = await self.redis.get(f"job:{job_id}:result")
        return {
            "status": status or "not_found",
            "result": json.loads(result) if result else None
        }
    
    async def enqueue_cv_parse(self, cv_id: str, user_id: str) -> str:
        return await self.enqueue(self.CV_PARSE_QUEUE, {
            "id": cv_id,
            "cv_id": cv_id,
            "user_id": user_id
        })
    
    async def enqueue_ai_tailor(self, cv_id: str, job_id: str, user_id: str) -> str:
        job_key = f"{cv_id}:{job_id}"
        return await self.enqueue(self.AI_TAILOR_QUEUE, {
            "id": job_key,
            "cv_id": cv_id,
            "job_id": job_id,
            "user_id": user_id
        })

queue_service = QueueService()
```

### **Day 5: Main Application**

**app/main.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.api.routes import cv, jobs, tailor
from app.workers.tasks import start_background_workers

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(start_background_workers())
    print("✓ Background workers started")
    yield
    worker_task.cancel()

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Include routers (will create next)
from app.api.routes import cv, jobs, tailor
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(tailor.router, prefix="/api/tailor", tags=["Tailor"])
```

**Test**:
```bash
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

---

## **PHASE 3: CV Processing** (Days 6-8)

### **Day 6: Storage & Upload**

**app/services/storage.py**:
```python
from app.utils.supabase_client import supabase
import uuid

class StorageService:
    BUCKET = "cv-uploads"
    
    async def upload_cv(self, content: bytes, filename: str, user_id: str) -> str:
        ext = filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        path = f"{user_id}/{unique_name}"
        
        supabase.storage.from_(self.BUCKET).upload(
            path, content,
            {"content-type": f"application/{ext}"}
        )
        return path
    
    async def download_cv(self, path: str) -> bytes:
        return supabase.storage.from_(self.BUCKET).download(path)
    
    async def delete_cv(self, path: str):
        supabase.storage.from_(self.BUCKET).remove([path])

storage_service = StorageService()
```

**app/api/routes/cv.py**:
```python
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api.deps import get_current_user
from app.services.storage import storage_service
from app.services.queue import queue_service
from app.utils.supabase_client import supabase

router = APIRouter()

@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(400, "Only PDF/DOCX allowed")
    
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(400, "Max 10MB")
    
    content = await file.read()
    file_path = await storage_service.upload_cv(content, file.filename, user.id)
    
    result = supabase.table("cvs").insert({
        "user_id": user.id,
        "original_filename": file.filename,
        "file_path": file_path,
        "file_size": file.size,
        "mime_type": file.content_type,
        "status": "uploaded"
    }).execute()
    
    cv_id = result.data[0]["id"]
    
    job_id = await queue_service.enqueue_cv_parse(cv_id, user.id)
    
    return {
        "cv_id": cv_id,
        "job_id": job_id,
        "status": "uploaded",
        "message": "CV uploaded, parsing started"
    }

@router.get("/status/{job_id}")
async def get_status(job_id: str, user = Depends(get_current_user)):
    return await queue_service.get_job_status(job_id)

@router.get("/")
async def list_cvs(user = Depends(get_current_user)):
    result = supabase.table("cvs").select("*").eq("user_id", user.id).execute()
    return result.data

@router.get("/{cv_id}")
async def get_cv(cv_id: str, user = Depends(get_current_user)):
    cv = supabase.table("cvs").select("*").eq("id", cv_id).single().execute()
    sections = supabase.table("cv_sections").select("*").eq("cv_id", cv_id).single().execute()
    
    return {
        "cv": cv.data,
        "sections": sections.data if sections.data else None
    }
```

### **Day 7-8: CV Parser**

**app/services/cv_parser.py**:
```python
from openai import AzureOpenAI
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import json
from app.config import settings

class CVParserService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
    
    async def parse_cv(self, content: bytes, filename: str) -> dict:
        if filename.endswith('.pdf'):
            text = self._extract_pdf(content)
        elif filename.endswith('.docx'):
            text = self._extract_docx(content)
        else:
            raise ValueError("Unsupported format")
        
        return await self._structure_with_ai(text)
    
    def _extract_pdf(self, content: bytes) -> str:
        pdf = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() for page in pdf.pages)
    
    def _extract_docx(self, content: bytes) -> str:
        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    
    async def _structure_with_ai(self, text: str) -> dict:
        system_prompt = """Extract CV information as JSON with:
        - summary (string)
        - skills (array of strings)
        - experience (array: {title, company, period, description[]})
        - education (array: {degree, institution, year})
        - certifications (array of strings, optional)
        """
        
        response = self.client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse:\n\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)

cv_parser_service = CVParserService()
```

**app/workers/tasks.py**:
```python
import asyncio
import traceback
from app.services.queue import queue_service
from app.services.cv_parser import cv_parser_service
from app.services.storage import storage_service
from app.utils.supabase_client import supabase

async def process_cv_parse_worker():
    print("✓ CV Parse Worker started")
    
    while True:
        try:
            job = await queue_service.dequeue(queue_service.CV_PARSE_QUEUE, timeout=5)
            
            if job:
                cv_id = job["cv_id"]
                print(f"Processing CV: {cv_id}")
                
                await queue_service.set_job_status(cv_id, "processing")
                
                # Get CV
                cv = supabase.table("cvs").select("*").eq("id", cv_id).single().execute()
                
                # Download file
                content = await storage_service.download_cv(cv.data["file_path"])
                
                # Parse
                parsed = await cv_parser_service.parse_cv(
                    content,
                    cv.data["original_filename"]
                )
                
                # Save
                supabase.table("cv_sections").insert({
                    "cv_id": cv_id,
                    **parsed
                }).execute()
                
                supabase.table("cvs").update({
                    "status": "parsed",
                    "parsed_at": "now()"
                }).eq("id", cv_id).execute()
                
                await queue_service.set_job_status(cv_id, "completed", parsed)
                print(f"✓ Completed: {cv_id}")
            
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)

async def start_background_workers():
    await asyncio.gather(
        process_cv_parse_worker(),
        return_exceptions=True
    )
```

---

## **PHASE 4: Job Management** (Days 9-10)

**app/api/routes/jobs.py**:
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.utils.supabase_client import supabase

router = APIRouter()

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    url: str | None = None

class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str | None = None
    url: str | None = None
    status: str | None = None

@router.post("/")
async def create_job(job: JobCreate, user = Depends(get_current_user)):
    result = supabase.table("jobs").insert({
        "user_id": user.id,
        **job.model_dump()
    }).execute()
    return result.data[0]

@router.get("/")
async def list_jobs(user = Depends(get_current_user)):
    result = supabase.table("jobs").select("*").eq("user_id", user.id).execute()
    return result.data

@router.get("/{job_id}")
async def get_job(job_id: str, user = Depends(get_current_user)):
    result = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
    return result.data

@router.put("/{job_id}")
async def update_job(job_id: str, job: JobUpdate, user = Depends(get_current_user)):
    result = supabase.table("jobs").update(
        job.model_dump(exclude_none=True)
    ).eq("id", job_id).eq("user_id", user.id).execute()
    return result.data[0]

@router.delete("/{job_id}")
async def delete_job(job_id: str, user = Depends(get_current_user)):
    supabase.table("jobs").delete().eq("id", job_id).eq("user_id", user.id).execute()
    return {"message": "Job deleted"}
```

---

## **PHASE 5: AI Tailoring** (Days 11-13)

**app/services/ai_tailor.py**:
```python
from openai import AzureOpenAI
import json
from app.config import settings

class AITailorService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
    
    async def tailor_cv(self, cv_data: dict, job_description: str) -> str:
        system_prompt = """You are a professional CV writer.
        Tailor the CV to match the job description.
        - Emphasize relevant skills
        - Use job keywords
        - Maintain truthfulness
        - Optimize for ATS
        Return markdown format."""
        
        user_prompt = f"""Job Description:
{job_description}

CV Data:
{json.dumps(cv_data, indent=2)}

Create tailored CV in markdown."""
        
        response = self.client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    async def chat_refinement(self, current_cv: str, history: list, message: str) -> str:
        messages = [
            {"role": "system", "content": "Help refine the CV based on user feedback."},
            {"role": "user", "content": f"Current CV:\n{current_cv}"}
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content

ai_tailor_service = AITailorService()
```

**app/api/routes/tailor.py**:
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.services.queue import queue_service
from app.utils.supabase_client import supabase

router = APIRouter()

class TailorRequest(BaseModel):
    cv_id: str
    job_id: str

class ChatMessage(BaseModel):
    message: str

@router.post("/create")
async def create_tailored_cv(req: TailorRequest, user = Depends(get_current_user)):
    job_id = await queue_service.enqueue_ai_tailor(req.cv_id, req.job_id, user.id)
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Tailoring started"
    }

@router.get("/{tailored_cv_id}")
async def get_tailored_cv(tailored_cv_id: str, user = Depends(get_current_user)):
    result = supabase.table("tailored_cvs").select("*").eq("id", tailored_cv_id).single().execute()
    return result.data

@router.post("/{tailored_cv_id}/chat")
async def chat_with_ai(
    tailored_cv_id: str,
    msg: ChatMessage,
    user = Depends(get_current_user)
):
    # Save user message
    supabase.table("chat_messages").insert({
        "tailored_cv_id": tailored_cv_id,
        "role": "user",
        "content": msg.message
    }).execute()
    
    # Get current CV
    cv = supabase.table("tailored_cvs").select("*").eq("id", tailored_cv_id).single().execute()
    
    # Get chat history
    history = supabase.table("chat_messages").select("*").eq(
        "tailored_cv_id", tailored_cv_id
    ).order("created_at").execute()
    
    # Generate response (add to worker for production)
    from app.services.ai_tailor import ai_tailor_service
    response = await ai_tailor_service.chat_refinement(
        cv.data["content"],
        [{"role": h["role"], "content": h["content"]} for h in history.data],
        msg.message
    )
    
    # Save assistant message
    supabase.table("chat_messages").insert({
        "tailored_cv_id": tailored_cv_id,
        "role": "assistant",
        "content": response
    }).execute()
    
    return {"response": response}
```

---

## **PHASE 6: Deployment** (Days 14-15)

### **Deploy to Render**

**render.yaml**:
```yaml
services:
  - type: web
    name: tailorjob-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: UPSTASH_REDIS_URL
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: AZURE_OPENAI_ENDPOINT
        sync: false
      - key: AZURE_OPENAI_KEY
        sync: false
```

**Deploy**:
1. Push to GitHub
2. Connect repo to Render
3. Add environment variables
4. Deploy

---

## ✅ Checklist

### Infrastructure
- [ ] Run database migrations
- [ ] Set up Supabase Storage bucket
- [ ] Create Upstash Redis account
- [ ] Set up Azure OpenAI resource

### Backend
- [ ] Create Python project
- [ ] Install dependencies
- [ ] Set up configuration
- [ ] Implement authentication
- [ ] Build CV upload endpoint
- [ ] Create CV parser service
- [ ] Set up background workers
- [ ] Implement job CRUD
- [ ] Build AI tailoring service
- [ ] Add chat functionality
- [ ] Deploy to Render

### Frontend Integration
- [ ] Update API URLs
- [ ] Replace mock data calls
- [ ] Test file upload
- [ ] Test job management
- [ ] Test CV tailoring
- [ ] Test chat interface

### Testing
- [ ] Test authentication flow
- [ ] Test CV upload & parsing
- [ ] Test job CRUD operations
- [ ] Test AI tailoring
- [ ] Test chat refinement
- [ ] End-to-end testing

---

## 🚀 Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (already working)
npm run dev
```

---

## 📊 Success Metrics

- [ ] User can upload CV
- [ ] CV gets parsed automatically
- [ ] User can add jobs
- [ ] AI generates tailored CV
- [ ] User can chat with AI
- [ ] All data persists
- [ ] Works on free tier

**Total Timeline**: 15 days  
**Total Cost**: $0-30/month