# Metrics Not Instrumented - Action Required

## Problem
Your Grafana dashboard shows "No Data" for most panels because the **metrics are defined but never incremented** in the application code.

## Current Status

### ✅ Working
- API health (`up`)
- System metrics (`process_resident_memory_bytes`, `process_cpu_seconds_total`, etc.)
- These work because they're automatically collected by Prometheus

### ❌ Not Working (Never Called)
- `user_signups_total` - Defined but never incremented on signup
- `user_logins_total` - Defined but never incremented on login  
- `feature_usage_total` - Defined but never incremented when features are used
- `cv_parse_duration_seconds` - Defined but never observed during CV parsing
- `ai_match_duration_seconds` - Defined but never observed during matching
- `paypal_api_calls_total` - Defined but never incremented on PayPal calls
- All other custom metrics in [`backend/app/middleware/metrics.py`](../backend/app/middleware/metrics.py)

## Root Cause
The metrics were created in the metrics file but the application code never imports or calls them.

**Example**: When a user logs in, the code should call:
```python
from app.middleware.metrics import user_logins
user_logins.labels(method='email').inc()
```

But this code **doesn't exist anywhere** in the application.

## How to Fix

You need to instrument your API endpoints to increment these metrics. Here are the key locations:

### 1. User Signups/Logins
**File**: Find your auth endpoints (likely in `backend/app/api/routes/`)

```python
from app.middleware.metrics import user_signups, user_logins

# In signup endpoint:
user_signups.labels(method='email').inc()  # or 'google'

# In login endpoint:
user_logins.labels(method='email').inc()  # or 'google'
```

### 2. Feature Usage
**Instrument each feature endpoint**:

```python
from app.middleware.metrics import feature_usage

# In CV upload endpoint:
feature_usage.labels(feature='cv_upload', tier=user_tier).inc()

# In job match endpoint:
feature_usage.labels(feature='job_match', tier=user_tier).inc()

# In CV tailor endpoint:
feature_usage.labels(feature='tailor_cv', tier=user_tier).inc()
```

### 3. CV Parsing
**File**: Likely in `backend/app/workers/cv_worker.py` or CV parsing service

```python
from app.middleware.metrics import cv_parse_duration, cv_parse_errors
import time

# Wrap CV parsing:
start_time = time.time()
try:
    # ... parse CV ...
    duration = time.time() - start_time
    cv_parse_duration.observe(duration)
except Exception as e:
    cv_parse_errors.labels(error_type=type(e).__name__).inc()
    raise
```

### 4. AI Matching
**File**: In your AI matching service

```python
from app.middleware.metrics import ai_match_duration, ai_match_tokens, ai_match_cost
import time

start_time = time.time()
# ... call AI API ...
duration = time.time() - start_time

ai_match_duration.observe(duration)
ai_match_tokens.labels(model='gpt-4').inc(token_count)
ai_match_cost.labels(model='gpt-4').inc(cost_dollars)
```

### 5. PayPal API
**File**: In PayPal integration code

```python
from app.middleware.metrics import paypal_api_calls, paypal_webhooks

# After PayPal API call:
paypal_api_calls.labels(operation='create_subscription', status='success').inc()

# In webhook handler:
paypal_webhooks.labels(event_type=event['event_type'], processed='true').inc()
```

## Quick Win: Add HTTP Request Metrics

The easiest fix is to properly configure the FastAPI instrumentator to track HTTP requests:

**File**: [`backend/app/middleware/metrics.py`](../backend/app/middleware/metrics.py:118-129)

```python
def setup_metrics(app):
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/docs", "/redoc", "/openapi.json"],
        inprogress_name="fastapi_inprogress_requests",
        inprogress_labels=True,
    )
    
    # ADD THESE LINES:
    instrumentator.add(
        metrics.request_size(),
        metrics.response_size(),
        metrics.latency(),
        metrics.requests(),
    )
    
    instrumentator.instrument(app)
    
    @app.get("/metrics")
    async def metrics_endpoint():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    print("✅ Prometheus metrics enabled at /metrics")
    return instrumentator
```

This will automatically add:
- `http_request_duration_seconds` - Request latency
- `http_requests_total` - Request count by method/endpoint/status
- `http_request_size_bytes` - Request sizes
- `http_response_size_bytes` - Response sizes

## Testing After Changes

1. Make the code changes
2. Redeploy to Azure App Service
3. Use the application (login, upload CV, match jobs, etc.)
4. Check `/metrics` endpoint: `curl https://tailorjob-api.azurewebsites.net/metrics | grep user_logins`
5. Wait 15-30 seconds for Prometheus to scrape
6. Refresh Grafana dashboard

## Current Dashboard
Your dashboard at http://20.72.174.253:3000 will show data once you instrument the code.

The monitoring **infrastructure is working perfectly**:
- ✅ Prometheus is scraping the API
- ✅ Grafana is connected to Prometheus  
- ✅ Dashboard queries are correct
- ❌ Application code isn't calling the metrics

## Priority Order

1. **HTTP request metrics** (quick win - just update instrumentator)
2. **User activity** (signups/logins) - shows user engagement
3. **Feature usage** - shows which features are popular
4. **CV processing** - shows performance bottlenecks
5. **AI matching** - shows costs and performance
6. **PayPal** - shows subscription events

## Need Help?

The metrics system is ready to use. You just need to call `.inc()` or `.observe()` at the right places in your code. Start with HTTP metrics (easiest) then gradually add custom metrics as needed.