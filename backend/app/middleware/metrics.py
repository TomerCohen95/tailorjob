"""
Prometheus Metrics for TailorJob API
"""

from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
import time

# Custom metrics

# CV Processing
cv_parse_duration = Histogram(
    'cv_parse_duration_seconds',
    'Time taken to parse a CV',
    buckets=[1, 2, 5, 10, 30, 60, 120]
)

cv_parse_errors = Counter(
    'cv_parse_errors_total',
    'Total number of CV parsing errors',
    ['error_type']
)

# AI Matching
ai_match_duration = Histogram(
    'ai_match_duration_seconds',
    'Time taken to run AI CV matching',
    buckets=[0.5, 1, 2, 5, 10, 20, 30]
)

ai_match_tokens = Counter(
    'ai_match_tokens_total',
    'Total tokens used in AI matching',
    ['model']
)

ai_match_cost = Counter(
    'ai_match_cost_dollars',
    'Total cost of AI matching in dollars',
    ['model']
)

# PayPal Integration
paypal_api_calls = Counter(
    'paypal_api_calls_total',
    'PayPal API calls',
    ['operation', 'status']
)

paypal_webhooks = Counter(
    'paypal_webhooks_total',
    'PayPal webhooks received',
    ['event_type', 'processed']
)

# Queue Metrics
queue_length = Gauge(
    'queue_length',
    'Number of jobs in the queue'
)

queue_processing_duration = Histogram(
    'queue_processing_duration_seconds',
    'Time to process a queue job',
    ['job_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Redis Metrics
redis_connection_errors = Counter(
    'redis_connection_errors_total',
    'Redis connection errors'
)

# Database Metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

# User Activity Metrics
user_signups = Counter(
    'user_signups_total',
    'Total user signups',
    ['method']  # 'email', 'google', etc.
)

user_logins = Counter(
    'user_logins_total',
    'Total user logins',
    ['method']
)

# Subscription Metrics
subscription_events = Counter(
    'subscription_events_total',
    'Subscription lifecycle events',
    ['event_type', 'tier']  # created, upgraded, cancelled, expired
)

# Feature Usage
feature_usage = Counter(
    'feature_usage_total',
    'Feature usage count',
    ['feature', 'tier']  # cv_upload, job_match, tailor_cv, etc.
)


def setup_metrics(app):
    """
    Set up Prometheus metrics for FastAPI application
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    from prometheus_fastapi_instrumentator import metrics
    
    # Auto-instrument FastAPI
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/docs", "/redoc", "/openapi.json"],
        inprogress_name="fastapi_inprogress_requests",
        inprogress_labels=True,
    )
    
    # Add HTTP request metrics
    instrumentator.add(
        metrics.requests()  # Adds http_requests_total
    ).add(
        metrics.latency()   # Adds http_request_duration_seconds
    ).add(
        metrics.request_size()  # Adds http_request_size_bytes
    ).add(
        metrics.response_size()  # Adds http_response_size_bytes
    )
    
    instrumentator.instrument(app)
    
    # Manually add /metrics endpoint since expose() doesn't work reliably
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    print("✅ Prometheus metrics enabled at /metrics")
    
    return instrumentator