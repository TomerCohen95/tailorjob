# Debug Mode Rules (Non-Obvious Only)

## Backend Debugging

- **Backend must run from `backend/` directory** - imports fail otherwise due to `from app.` prefix
- **Redis failures are silent** - queue service continues without error (backend/app/services/queue.py:11-22)
- **Worker logs to stdout** - check terminal where uvicorn is running for CV parse status
- **Worker task runs in background** - created in FastAPI lifespan, not visible in request logs (backend/app/main.py:28)

## Database & Queue Debugging

- **CV status field** tracks parse state: uploaded → parsing → parsed/error (backend/app/workers/cv_worker.py:30-32)
- **Queue uses Redis LIST** with `brpop` blocking operation (backend/app/services/queue.py:48)
- **Job status stored in Redis** with 1-hour TTL - check `job:{job_id}:status` key (backend/app/services/queue.py:36)
- **CV sections stored as JSON strings** - need `json.loads()` to read (backend/app/workers/cv_worker.py:60-63)

## Authentication Debugging

- **Auth token from Supabase session** - fetched on every API call (src/lib/api.ts:8-11)
- **401 errors mean** token expired or invalid - check Supabase session state
- **CORS configured with regex** - any localhost port allowed (backend/app/main.py:49)

## Common Issues

- **Worker not processing** - check Redis connection and UPSTASH_REDIS_URL env var
- **Import errors** - ensure running uvicorn from `backend/` directory
- **SSL errors with Redis** - SSL verification disabled for development (backend/app/services/queue.py:18)