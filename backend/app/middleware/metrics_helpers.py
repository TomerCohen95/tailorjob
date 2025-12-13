"""
Helper functions for instrumenting Prometheus metrics across the application.
"""
from app.middleware.metrics import (
    feature_usage,
    user_signups,
    user_logins,
    cv_parse_duration,
    cv_parse_errors,
    ai_match_duration,
    ai_match_tokens,
    ai_match_cost,
    paypal_api_calls,
    paypal_webhooks,
    subscription_events
)
import time
from functools import wraps
from typing import Optional


def get_user_tier(user) -> str:
    """Get user's subscription tier"""
    # Check if user has active subscription
    # Handle both dict and Supabase User object
    if hasattr(user, 'id'):
        # Supabase User object - check user_metadata
        user_metadata = getattr(user, 'user_metadata', {}) or {}
        if user_metadata.get("subscription_tier"):
            return user_metadata["subscription_tier"]
    elif isinstance(user, dict):
        # Dict user object
        if user.get("subscription_tier"):
            return user["subscription_tier"]
    return "free"


def track_feature_usage(feature: str, user):
    """Track feature usage with user's tier"""
    tier = get_user_tier(user)
    feature_usage.labels(feature=feature, tier=tier).inc()


def track_user_signup(method: str = "email"):
    """Track user signup"""
    user_signups.labels(method=method).inc()


def track_user_login(method: str = "email"):
    """Track user login"""
    user_logins.labels(method=method).inc()


def track_cv_parse(duration: float):
    """Track CV parsing duration"""
    cv_parse_duration.observe(duration)


def track_cv_parse_error(error_type: str):
    """Track CV parsing error"""
    cv_parse_errors.labels(error_type=error_type).inc()


def track_ai_match(duration: float, model: str = "gpt-4", tokens: int = 0, cost: float = 0.0):
    """Track AI matching metrics"""
    ai_match_duration.observe(duration)
    if tokens > 0:
        ai_match_tokens.labels(model=model).inc(tokens)
    if cost > 0:
        ai_match_cost.labels(model=model).inc(cost)


def track_paypal_api_call(operation: str, status: str):
    """Track PayPal API call"""
    paypal_api_calls.labels(operation=operation, status=status).inc()


def track_paypal_webhook(event_type: str, processed: bool = True):
    """Track PayPal webhook"""
    paypal_webhooks.labels(event_type=event_type, processed=str(processed).lower()).inc()


def track_subscription_event(event_type: str, tier: str):
    """Track subscription lifecycle event"""
    subscription_events.labels(event_type=event_type, tier=tier).inc()


def timed_operation(metric_func):
    """
    Decorator to time an operation and record it to a metric
    
    Usage:
        @timed_operation(track_cv_parse)
        async def parse_cv():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metric_func(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                # Still record duration even on error
                metric_func(duration)
                raise
        return wrapper
    return decorator