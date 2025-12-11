# Logging Coverage Analysis

## Current Logging Status

### ✅ What's Currently Logged

#### 1. HTTP Requests (via Request Logging Middleware)
**File**: `backend/app/middleware/request_logging.py`
**Coverage**: ALL HTTP endpoints
```
✅ Every API request is logged with:
- Method (GET, POST, PUT, DELETE)
- Path (/api/cv/upload, /api/matching/analyze, etc.)
- Client IP
- Response status code
- Duration in seconds
- Error messages (if 4xx or 5xx)
```

**Example logs**:
```
INFO - uvicorn.access - GET /api/health - Client: 52.146.70.94
INFO - uvicorn.access - GET /api/health - Status: 200 - Duration: 0.003s
WARNING - uvicorn.access - HTTP 404 error: GET /api/nonexistent
ERROR - uvicorn.access - POST /api/cv/upload - Error: File too large - Duration: 0.102s
```

#### 2. PayPal Operations
**File**: `backend/app/services/paypal_monitor.py`
**Coverage**: Payment health checks, webhook processing
```
✅ Logged:
- Payment success rate warnings
- Webhook processing rate warnings
- Subscription health checks
- Monitor start/stop
- Health check summaries
```

#### 3. Application Startup
**File**: `backend/app/main.py`
**Coverage**: Server initialization
```
✅ Logged:
- Loki logging setup
- Background worker startup
- Configuration status
```

### ❌ What's NOT Currently Logged

#### Critical Gaps - These SHOULD be added:

1. **CV Upload & Parsing**
   - ❌ CV file received (size, format)
   - ❌ CV enqueued for parsing
   - ❌ Parsing started/completed
   - ❌ Parsing errors (PDF extraction failures, etc.)
   - ❌ Section extraction results

2. **Job Matching**
   - ❌ Match analysis requested (CV ID, Job ID)
   - ❌ AI model called (tokens used, cost)
   - ❌ Match score calculated
   - ❌ Requirements matrix generated
   - ❌ Match saved to database

3. **CV Tailoring**
   - ❌ Tailoring requested
   - ❌ AI recommendations generated
   - ❌ User applied changes
   - ❌ Diff generated
   - ❌ PDF export requested

4. **Authentication**
   - ❌ User logged in
   - ❌ Token refreshed
   - ❌ Authentication failed
   - ❌ User logged out

5. **Subscription Management**
   - ❌ Subscription created
   - ❌ Subscription activated
   - ❌ Subscription upgraded/cancelled
   - ❌ Usage limits checked
   - ❌ Usage limits exceeded

6. **Background Workers**
   - ❌ Worker task started
   - ❌ Worker task completed
   - ❌ Worker task failed
   - ❌ Queue depth

7. **Database Operations**
   - ❌ CV created/updated/deleted
   - ❌ Job created/updated/deleted
   - ❌ Match score saved
   - ❌ Database errors

## Recommended Logging Strategy

### Principle: Log Business Events, Not Just HTTP

**Current**: Only HTTP requests are logged
**Should Be**: Business operations are logged with context

### Logging Levels

```python
logging.DEBUG    # Development only - verbose details
logging.INFO     # Normal operations (CV uploaded, match completed)
logging.WARNING  # Something unusual (low match score, rate limits)
logging.ERROR    # Operation failed (parsing error, AI timeout)
logging.CRITICAL # System failure (database down, queue full)
```

### What to Log for Each Flow

#### 1. CV Upload Flow
```python
logger.info(f"CV upload started: user={user_id}, filename={filename}, size={size_bytes}b")
logger.info(f"CV enqueued for parsing: cv_id={cv_id}, job_id={job_id}")
logger.info(f"CV parsing completed: cv_id={cv_id}, sections={len(sections)}, duration={duration}s")
logger.error(f"CV parsing failed: cv_id={cv_id}, error={str(e)}")
```

#### 2. Job Matching Flow
```python
logger.info(f"Match analysis requested: cv_id={cv_id}, job_id={job_id}, user={user_id}")
logger.info(f"AI match analysis: model={model}, tokens={tokens}, cost=${cost:.4f}, duration={duration}s")
logger.info(f"Match score calculated: cv_id={cv_id}, job_id={job_id}, score={score}, tier={tier}")
logger.warning(f"Low match score: cv_id={cv_id}, job_id={job_id}, score={score}")
logger.error(f"Match analysis failed: cv_id={cv_id}, job_id={job_id}, error={str(e)}")
```

#### 3. CV Tailoring Flow
```python
logger.info(f"Tailoring requested: cv_id={cv_id}, job_id={job_id}, user={user_id}")
logger.info(f"AI recommendations generated: cv_id={cv_id}, recommendations={len(recs)}, tokens={tokens}")
logger.info(f"User applied changes: cv_id={cv_id}, sections_modified={count}")
logger.info(f"PDF exported: cv_id={cv_id}, job_id={job_id}, size={size_kb}kb")
```

#### 4. Authentication Flow
```python
logger.info(f"User logged in: user_id={user_id}, email={email}, provider=google")
logger.warning(f"Authentication failed: email={email}, reason=invalid_token")
logger.info(f"User logged out: user_id={user_id}")
```

#### 5. Subscription Flow
```python
logger.info(f"Subscription created: user={user_id}, plan={plan_id}, status=APPROVAL_PENDING")
logger.info(f"Subscription activated: user={user_id}, plan={plan_id}, subscription_id={sub_id}")
logger.warning(f"Usage limit checked: user={user_id}, feature={feature}, used={used}/{limit}")
logger.error(f"Usage limit exceeded: user={user_id}, feature={feature}, limit={limit}")
```

## Implementation Plan

### Phase 1: Critical Business Operations (HIGH PRIORITY)
Add logging to these files:
1. `backend/app/api/routes/cv.py` - CV upload, parsing status
2. `backend/app/api/routes/matching.py` - Match analysis, scores
3. `backend/app/api/routes/tailor.py` - Tailoring operations
4. `backend/app/workers/cv_worker.py` - Background parsing

### Phase 2: User Operations (MEDIUM PRIORITY)
5. `backend/app/api/routes/payments.py` - Subscription events
6. `backend/app/middleware/auth.py` - Authentication events
7. `backend/app/api/routes/jobs.py` - Job operations

### Phase 3: System Operations (LOW PRIORITY)
8. Database layer - Query performance
9. Queue operations - Depth, failures
10. External API calls - Response times

## Example: Adding Logging to CV Upload

### Before (current):
```python
@router.post("/upload")
async def upload_cv(file: UploadFile, user = Depends(get_current_user)):
    # Process file
    cv_id = await save_cv(file, user.id)
    return {"cv_id": cv_id}
```

### After (with logging):
```python
import logging
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_cv(file: UploadFile, user = Depends(get_current_user)):
    logger.info(f"📤 CV upload started: user={user.id}, filename={file.filename}, size={file.size}b")
    
    try:
        cv_id = await save_cv(file, user.id)
        logger.info(f"✅ CV saved: cv_id={cv_id}, user={user.id}")
        return {"cv_id": cv_id}
    except Exception as e:
        logger.error(f"❌ CV upload failed: user={user.id}, filename={file.filename}, error={str(e)}")
        raise
```

## Benefits of Comprehensive Logging

### 1. Debugging Production Issues
**Without logging**:
- "User says matching isn't working" → ❌ No idea what happened

**With logging**:
- Search logs for user_id → See exact error: "AI timeout after 30s"

### 2. Performance Monitoring
- Track slow operations: "CV parsing taking >5s"
- Identify bottlenecks: "AI matching using 10k tokens per request"
- Monitor costs: "Total AI cost today: $45.67"

### 3. Business Analytics
- CV uploads per day
- Most common parsing errors
- Average match scores
- Feature usage by subscription tier

### 4. Security Auditing
- Failed login attempts
- Suspicious activity patterns
- Usage abuse detection

## Current Coverage Summary

| Category | Coverage | Status |
|----------|----------|--------|
| **HTTP Requests** | 100% | ✅ Complete |
| **CV Upload** | 20% | ⚠️ Minimal |
| **CV Parsing** | 0% | ❌ None |
| **Job Matching** | 0% | ❌ None |
| **CV Tailoring** | 0% | ❌ None |
| **Authentication** | 0% | ❌ None |
| **Subscriptions** | 10% | ⚠️ Minimal |
| **Background Workers** | 0% | ❌ None |
| **Database Ops** | 0% | ❌ None |

**Overall Coverage**: ~15% of business operations

## Next Steps

### Option 1: Quick Win (1-2 hours)
Add logging to the top 3 critical paths:
1. CV upload (`backend/app/api/routes/cv.py`)
2. Match analysis (`backend/app/api/routes/matching.py`)
3. CV worker (`backend/app/workers/cv_worker.py`)

**Result**: Coverage improves from 15% → 60%

### Option 2: Comprehensive (4-6 hours)
Add logging to all business operations listed above.

**Result**: Coverage improves from 15% → 90%

### Option 3: Current State
Keep only HTTP request logging.

**Result**: Can see WHAT requests happened, but not WHY they failed or WHAT they did

## Recommendation

**Do Option 1 (Quick Win)** - Add logging to critical paths.

This gives you:
- ✅ Visibility into CV processing pipeline
- ✅ Ability to debug AI matching issues
- ✅ Understanding of worker performance
- ✅ Cost tracking for AI operations

**Time investment**: 1-2 hours
**Value**: High - covers 80% of common issues

---

## Testing Logging

After adding logs, verify with:

```bash
# 1. Generate test traffic
curl -X POST https://tailorjob-api.azurewebsites.net/api/cv/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"

# 2. Wait 10s for logs to be indexed

# 3. Query Loki
curl -G "http://tailorjob-loki.eastus.azurecontainer.io:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="tailorjob-api"} |= "CV upload"' \
  --data-urlencode "start=$(($(date -u '+%s') - 300))000000000" \
  --data-urlencode "end=$(date -u '+%s')000000000"

# 4. Or use Grafana Explore:
# http://20.72.174.253:3000/explore
# Query: {job="tailorjob-api"} |= "CV upload"
```

## Conclusion

**Current State**:
- ✅ HTTP requests are logged (GOOD)
- ✅ Logs are persisted in Azure File Share (GOOD)
- ❌ Business operations are NOT logged (GAP)

**To get full visibility**:
1. Add logging to critical business operations
2. Deploy updated code
3. Verify logs appear in Grafana

This will let you explore "what happened" in your system, not just "what requests were made".