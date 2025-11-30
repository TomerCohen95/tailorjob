"""
Usage tracking and limiting middleware.
Enforces tier-based limits on API endpoints.
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status

from app.services.subscription_service import subscription_service


def require_feature(feature: str):
    """
    Decorator to enforce feature access based on subscription tier.
    
    Usage:
        @require_feature('cv_upload')
        async def upload_cv(user_id: str, ...):
            # Function body
            pass
    
    Args:
        feature: Feature name ('cv_upload', 'job_match', 'tailor_cv', 'export_pdf')
    
    Raises:
        HTTPException(403): If user doesn't have access to feature
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs
            user_id = kwargs.get('user_id')
            
            if not user_id:
                # Try to find in args (less ideal but fallback)
                for arg in args:
                    if isinstance(arg, str) and '-' in arg:  # UUID-like
                        user_id = arg
                        break
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_id required for feature access check"
                )
            
            # Check if user can use feature
            allowed, error_message = await subscription_service.can_use_feature(user_id, feature)
            
            if not allowed:
                # Get user's subscription for upgrade info
                subscription = await subscription_service.get_user_subscription(user_id)
                tier = subscription['tier']
                
                # Build helpful error message with upgrade CTA
                if tier == 'free':
                    detail = {
                        "error": error_message,
                        "upgrade_to": "basic",
                        "message": "Upgrade to Basic ($9.99/month) to unlock this feature!"
                    }
                elif tier == 'basic':
                    detail = {
                        "error": error_message,
                        "upgrade_to": "pro",
                        "message": "Upgrade to Pro ($19.99/month) for unlimited access!"
                    }
                else:
                    detail = {
                        "error": error_message,
                        "message": "Contact support for assistance."
                    }
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=detail
                )
            
            # Track usage after checking access
            await subscription_service.track_usage(user_id, feature)
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_tier(min_tier: str):
    """
    Decorator to enforce minimum subscription tier.
    
    Usage:
        @require_tier('pro')
        async def premium_feature(user_id: str, ...):
            # Function body
            pass
    
    Args:
        min_tier: Minimum tier required ('basic', 'pro', 'enterprise')
    
    Raises:
        HTTPException(403): If user's tier is below minimum
    """
    tier_order = ['free', 'basic', 'pro', 'enterprise']
    min_tier_index = tier_order.index(min_tier)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id
            user_id = kwargs.get('user_id')
            
            if not user_id:
                for arg in args:
                    if isinstance(arg, str) and '-' in arg:
                        user_id = arg
                        break
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_id required for tier check"
                )
            
            # Get user's subscription
            subscription = await subscription_service.get_user_subscription(user_id)
            user_tier = subscription['tier']
            user_tier_index = tier_order.index(user_tier)
            
            # Check if user meets minimum tier
            if user_tier_index < min_tier_index:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": f"This feature requires {min_tier} tier or higher",
                        "current_tier": user_tier,
                        "required_tier": min_tier,
                        "message": f"Upgrade to {min_tier} to access this feature"
                    }
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def get_usage_info(user_id: str) -> dict:
    """
    Get user's current usage and limits for display.
    
    Returns:
        {
            "tier": "basic",
            "usage": {"cvs": 3, "matches": 10, ...},
            "limits": {"cvs": 10, "matches": 50, ...},
            "percentages": {"cvs": 30, "matches": 20, ...}
        }
    """
    subscription = await subscription_service.get_user_subscription(user_id)
    
    usage = subscription['usage']
    limits = subscription['limits']
    
    # Calculate usage percentages
    percentages = {}
    for key in usage.keys():
        limit = limits.get(key, 0)
        if limit == -1:
            percentages[key] = 0  # Unlimited = 0%
        elif limit == 0:
            percentages[key] = 100  # No access = 100%
        else:
            percentages[key] = min(100, int((usage[key] / limit) * 100))
    
    return {
        "tier": subscription['tier'],
        "status": subscription['status'],
        "usage": usage,
        "limits": limits,
        "percentages": percentages,
        "current_period_end": subscription.get('current_period_end')
    }