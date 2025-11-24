# Architect Mode Rules (Non-Obvious Only)

## Architectural Constraints

- **Backend tied to `backend/` directory** - all imports use `from app.` prefix, can't relocate (backend/app/main.py:6-8)
- **Worker runs in FastAPI process** - not separate container/service (backend/app/main.py:18-34)
- **Redis optional by design** - app degrades gracefully without async processing (backend/app/services/queue.py:11-22)
- **CV sections stored as JSON strings** - intentional design, not JSONB (backend/app/workers/cv_worker.py:60-63)

## Hidden Coupling

- **Worker depends on Redis blocking call** - uses `brpop` with 5s timeout (backend/app/services/queue.py:48)
- **Frontend tightly coupled to localhost** - API_BASE_URL hardcoded (src/lib/api.ts:3)
- **Auth token fetched per request** - no caching layer (src/lib/api.ts:8-11)
- **CORS config parsed at runtime** - stored as JSON string in env (backend/app/config.py:24-32)

## Design Decisions

- **Settings ignore extra env vars** - flexibility over strict validation (backend/app/config.py:9)
- **SSL disabled for Redis** - development convenience trade-off (backend/app/services/queue.py:18)
- **Worker supports reparse** - checks existing sections before insert (backend/app/workers/cv_worker.py:52-76)
- **FormData uploads omit Content-Type** - rely on browser behavior (src/lib/api.ts:28-31)

## Scalability Considerations

- **Single worker process** - background task in FastAPI lifespan, not horizontally scalable
- **Job status has TTL** - 1-hour expiry in Redis, no persistent job history (backend/app/services/queue.py:36)
- **Blocking queue reads** - worker polls Redis with blocking `brpop`, not pub/sub
- **Task cancellation requires explicit handling** - both `cancel()` and `CancelledError` catch (backend/app/workers/cv_worker.py:131-135)