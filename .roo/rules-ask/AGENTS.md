# Ask Mode Rules (Non-Obvious Only)

## Project Structure Context

- **Two separate codebases** - frontend (root) and backend (backend/) with different runtimes
- **Backend must run from `backend/` dir** - all `from app.` imports depend on this (backend/app/main.py:6-8)
- **Frontend API calls hardcoded** to localhost:8000 - not configurable via env (src/lib/api.ts:3)

## Architecture Context

- **Background worker in FastAPI lifespan** - not a separate process/container (backend/app/main.py:18-34)
- **Redis is optional dependency** - app works without it but no async processing (backend/app/services/queue.py:11-22)
- **CV sections in database as JSON strings** - not JSONB columns (backend/app/workers/cv_worker.py:60-63)

## Configuration Context

- **CORS_ORIGINS is JSON string** in .env file, not array - parsed at runtime (backend/app/config.py:24-32)
- **Settings use `extra="ignore"`** - unknown env vars don't cause errors (backend/app/config.py:9)
- **SSL disabled for Redis** in development environment (backend/app/services/queue.py:18)

## Authentication Context

- **Supabase session checked on every API call** - no token caching (src/lib/api.ts:8-11)
- **FormData uploads skip Content-Type header** - browser sets it with boundary (src/lib/api.ts:28-31)
- **Service role key required** for backend Supabase client - not anon key

## Queue & Worker Context

- **Worker uses blocking Redis `brpop`** - not polling with sleep (backend/app/services/queue.py:48)
- **Job status has 1-hour TTL** in Redis - expires automatically (backend/app/services/queue.py:36)
- **Worker checks for existing sections** before insert - supports reparse (backend/app/workers/cv_worker.py:52-76)