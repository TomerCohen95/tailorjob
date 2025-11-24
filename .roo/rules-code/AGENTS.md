# Code Mode Rules (Non-Obvious Only)

## Backend Python Patterns

- **Always import with `from app.`** prefix - relative imports fail (backend/app/main.py:6-8)
- **Config Settings uses `extra="ignore"`** - adding new env vars won't break startup (backend/app/config.py:9)
- **CORS_ORIGINS must be JSON string** in .env, not array - parsed at runtime (backend/app/config.py:24-32)
- **Redis connection disables SSL verification** for development (backend/app/services/queue.py:18)
- **Queue operations are no-ops** when Redis not configured - no errors thrown (backend/app/services/queue.py:31-40)

## Frontend TypeScript Patterns

- **API client omits Content-Type for FormData** - browser auto-sets with boundary (src/lib/api.ts:28-31)
- **Auth token fetched on every API call** from Supabase session (src/lib/api.ts:8-11)
- **API_BASE_URL hardcoded** to localhost:8000 - must change for production (src/lib/api.ts:3)

## Database Patterns

- **CV sections stored as JSON.dumps() strings** not JSONB columns (backend/app/workers/cv_worker.py:60-63)
- **Worker checks for existing sections** before insert to support reparse (backend/app/workers/cv_worker.py:52-76)

## Worker Patterns

- **Background worker auto-starts** in FastAPI lifespan, not manual start (backend/app/main.py:28)
- **Worker uses blocking `brpop`** with 5s timeout, not polling (backend/app/services/queue.py:48)
- **Task cancellation needs both** `cancel()` and catching `CancelledError` (backend/app/workers/cv_worker.py:131-135)