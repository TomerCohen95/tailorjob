# TailorJob Backend API

Python FastAPI backend for the TailorJob CV tailoring platform.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or later
- Supabase account (for database, auth, storage)
- Upstash account (for Redis queue)
- Azure OpenAI access (for AI features)

### 1. Run Setup Script

```bash
cd backend
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Create `.env` file from template

### 2. Configure Environment Variables

Edit `backend/.env` with your credentials:

```env
# Get from Supabase Dashboard → Settings → API
SUPABASE_URL=https://xxxyyy.supabase.co
SUPABASE_KEY=your_service_role_key

# Get from Upstash Dashboard → Details
UPSTASH_REDIS_URL=redis://default:xxx@xxx.upstash.io:6379

# Get from Azure Portal → OpenAI Resource
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 3. Apply Database Migration

Go to Supabase Dashboard → SQL Editor:
1. Copy content from `supabase/migrations/20240122000000_add_cv_tables.sql`
2. Paste and run

### 4. Set Up Supabase Storage

Go to Supabase Dashboard → Storage:
1. Create bucket: `cv-uploads`
2. Set to `private`
3. Add storage policies (see migration file)

### 5. Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start server with auto-reload
uvicorn app.main:app --reload --port 8000
```

Server will start at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings/configuration
│   ├── api/
│   │   ├── deps.py          # Auth middleware
│   │   └── routes/
│   │       ├── cv.py        # CV endpoints
│   │       ├── jobs.py      # Job endpoints
│   │       └── tailor.py    # Tailoring endpoints
│   ├── services/
│   │   ├── queue.py         # Redis queue service
│   │   └── storage.py       # File storage service
│   └── utils/
│       └── supabase_client.py
├── requirements.txt
├── .env
└── setup.sh
```

## 🔌 API Endpoints

### CV Operations
- `POST /api/cv/upload` - Upload CV file
- `GET /api/cv/` - List all CVs
- `GET /api/cv/{cv_id}` - Get CV details
- `GET /api/cv/status/{job_id}` - Check parsing status
- `DELETE /api/cv/{cv_id}` - Delete CV

### Job Operations
- `POST /api/jobs/` - Create job
- `GET /api/jobs/` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `PUT /api/jobs/{job_id}` - Update job
- `DELETE /api/jobs/{job_id}` - Delete job

### Tailoring Operations
- `POST /api/tailor/create` - Create tailored CV
- `GET /api/tailor/{id}` - Get tailored CV
- `POST /api/tailor/{id}/chat` - Chat with AI

## 🔐 Authentication

All endpoints (except `/health` and `/`) require authentication.

**Get JWT Token:**
1. User signs in through frontend (Google OAuth)
2. Frontend gets JWT from Supabase Auth
3. Frontend sends JWT in `Authorization: Bearer <token>` header

**Test in Swagger UI:**
1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Enter: `Bearer your_token_here`

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload CV (with auth)
```bash
curl -X POST http://localhost:8000/api/cv/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/cv.pdf"
```

### List Jobs
```bash
curl http://localhost:8000/api/jobs/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🐛 Troubleshooting

### Import Error: No module named 'app'
```bash
# Make sure you're in the backend directory
cd backend
python -m app.main
```

### Connection Error: Supabase
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Ensure you're using the **service role key**, not anon key

### Connection Error: Redis
- Check `UPSTASH_REDIS_URL` in `.env`
- Test connection: `redis-cli -u $UPSTASH_REDIS_URL ping`

### CORS Error from Frontend
- Check `CORS_ORIGINS` in `.env` includes `http://localhost:5173`
- Restart backend after changing `.env`

## 📝 Development Notes

### Adding New Endpoints
1. Create route file in `app/api/routes/`
2. Add router to `app/main.py`
3. Docs auto-update at `/docs`

### Environment Variables
- Development: `.env` file
- Production: Set in hosting platform (Render, Railway, etc.)

### Hot Reload
Server auto-reloads on code changes when running with `--reload` flag.

## 🚀 Next Steps

1. ✅ Basic backend structure created
2. ⏳ Implement CV parser service
3. ⏳ Implement AI tailoring service
4. ⏳ Add background workers
5. ⏳ Add PDF export
6. ⏳ Deploy to Render

See `MVP_IMPLEMENTATION_PLAN.md` for full roadmap.