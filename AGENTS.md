# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Critical Architecture Notes

- **Dual Stack**: Frontend (Vite/React/TypeScript) + Backend (FastAPI/Python) are separate codebases
- **Backend runs from `backend/` directory** - must `cd backend` before running uvicorn commands
- **CORS uses regex pattern** in backend/app/main.py: `allow_origin_regex` not `allow_origins` array
- **Config uses `extra="ignore"`** in backend/app/config.py - unknown env vars are silently ignored
- **Background worker auto-starts** with FastAPI lifespan in backend/app/main.py (line 28)

## Commands

**Backend** (must run from `backend/` directory):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend** (run from project root):
```bash
npm run dev  # Development server
npm run build  # Production build
```

## Non-Obvious Patterns

- **API client doesn't set Content-Type for FormData** (src/lib/api.ts:29) - browser sets it with boundary
- **Redis/Queue is optional** - backend continues without it (backend/app/services/queue.py:11-22)
- **Worker uses `brpop` with 5s timeout** (backend/app/services/queue.py:48) - blocking queue read
- **CV sections stored as JSON strings** in database (backend/app/workers/cv_worker.py:60-63)
- **CORS_ORIGINS is JSON string** in .env, parsed at runtime (backend/app/config.py:24-32)
- **SSL cert verification disabled** for Redis in development (backend/app/services/queue.py:18)

## Critical Gotchas

- Backend imports use `from app.` prefix - won't work if not in `backend/` directory
- Frontend API_BASE_URL hardcoded to `http://localhost:8000/api` (src/lib/api.ts:3)
- Worker task cancellation requires both `cancel()` and catching `CancelledError` (backend/app/workers/cv_worker.py:131-135)
- Auth token retrieved from Supabase session on every API call (src/lib/api.ts:8-11)