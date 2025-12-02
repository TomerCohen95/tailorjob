"""
Payment API endpoints.
Handles subscription creation, management, and webhook processing.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import json

from app.services.paypal_service import paypal_service
from app.services.subscription_service import subscription_service
from app.utils.usage_limiter import get_usage_info
from app.config import settings



# Quick access dependency
from app.api.deps import get_current_user

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateSubscriptionRequest(BaseModel):
    """Request to create a new subscription"""
    plan_id: str  # 'basic_monthly', 'basic_yearly', 'pro_monthly', 'pro_yearly'
    return_url: str
    cancel_url: str


class CreateSubscriptionResponse(BaseModel):
    """Response from subscription creation"""
    subscription_id: str
    approval_url: str
    status: str


class SubscriptionWebhookEvent(BaseModel):
    """PayPal webhook event"""
    id: str
    event_type: str
    resource: Dict[str, Any]


# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

@router.get("/usage")
async def get_usage(user = Depends(get_current_user)):
    """
    Get current usage statistics for the authenticated user.
    Returns usage data compatible with the frontend Pricing page.
    """
    # Extract user_id from user object
    if hasattr(user, 'id'):
        user_id = user.id
    elif isinstance(user, dict):
        user_id = user.get('id') or user.get('user_id')
    else:
        raise HTTPException(status_code=400, detail="Invalid user object")
    
    # Get subscription with usage data
    subscription = await subscription_service.get_user_subscription(user_id)
    
    # Format response for frontend - flat structure matching UsageData interface
    usage_data = {
        "user_id": user_id,
        "tier": subscription.get('tier', 'free'),
        "period_start": subscription.get('current_period_start', datetime.utcnow().isoformat()),
        "period_end": subscription.get('current_period_end', datetime.utcnow().isoformat()),
        "cv_uploads": subscription['usage'].get('cvs', 0),
        "cv_limit": subscription['limits'].get('cvs', 3),
        "job_matches": subscription['usage'].get('matches', 0),
        "match_limit": subscription['limits'].get('matches', 5),
        "tailored_cvs": subscription['usage'].get('tailored', 0),
        "tailor_limit": subscription['limits'].get('tailored', 0)
    }
    
    return usage_data



@router.post("/subscriptions/create", response_model=CreateSubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user = Depends(get_current_user)
):
    """
    Create a new PayPal subscription.
    User must approve via returned approval_url.
    
    Returns approval URL for user to complete subscription on PayPal.
    """
    try:
        # Extract user_id from user object
        if hasattr(user, 'id'):
            user_id = user.id
        elif isinstance(user, dict):
            user_id = user.get('id') or user.get('user_id')
        else:
            raise HTTPException(status_code=400, detail="Invalid user object")
        
        # Get user info for email (optional)
        from app.utils.supabase_client import supabase
        user_result = supabase.table('profiles').select('email').eq('id', user_id).single().execute()
        user_email = user_result.data.get('email') if user_result.data else None
        
        # Create subscription with PayPal
        paypal_response = paypal_service.create_subscription(
            plan_id=request.plan_id,
            return_url=request.return_url,
            cancel_url=request.cancel_url,
            user_email=user_email
        )
        
        # Extract approval URL
        approval_url = None
        for link in paypal_response.get('links', []):
            if link['rel'] == 'approve':
                approval_url = link['href']
                break
        
        if not approval_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get PayPal approval URL"
            )
        
        return CreateSubscriptionResponse(
            subscription_id=paypal_response['id'],
            approval_url=approval_url,
            status=paypal_response['status']
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Subscription creation error: {str(e)}")
        print(f"📝 Full traceback:\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )


class ActivateSubscriptionRequest(BaseModel):
    """Request to activate a subscription"""
    subscription_id: str


@router.post("/subscriptions/activate")
async def activate_subscription(
    request: ActivateSubscriptionRequest,
    user = Depends(get_current_user)
):
    """
    Activate subscription after user approves on PayPal.
    Called by frontend after PayPal redirects back.
    """
    subscription_id = request.subscription_id
    try:
        # Extract user_id from user object
        if hasattr(user, 'id'):
            user_id = user.id
        elif isinstance(user, dict):
            user_id = user.get('id') or user.get('user_id')
        else:
            raise HTTPException(status_code=400, detail="Invalid user object")
        
        # Get subscription details from PayPal
        paypal_subscription = paypal_service.get_subscription(subscription_id)
        
        if paypal_subscription['status'] != 'ACTIVE':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription not active: {paypal_subscription['status']}"
            )
        
        # Extract tier from plan_id by looking up in PLAN_IDS
        plan_id = paypal_subscription['plan_id']
        
        # Reverse lookup: find which tier this plan_id belongs to
        tier = 'basic'  # default
        for plan_key, plan_value in paypal_service.PLAN_IDS.items():
            if plan_value == plan_id:
                # Extract tier from plan_key (e.g., 'basic_monthly' -> 'basic')
                tier = plan_key.split('_')[0]
                break
        
        # Get billing info
        billing_info = paypal_subscription.get('billing_info', {})
        last_payment = billing_info.get('last_payment', {})
        amount = float(last_payment.get('amount', {}).get('value', 0))
        currency = last_payment.get('amount', {}).get('currency_code', 'USD')
        
        # Determine billing cycle
        billing_cycle = 'yearly' if 'YEARLY' in plan_id else 'monthly'
        
        # Create subscription in our database
        subscription = await subscription_service.create_subscription(
            user_id=user_id,
            paypal_subscription_id=subscription_id,
            paypal_plan_id=plan_id,
            tier=tier,
            amount=amount,
            currency=currency,
            billing_cycle=billing_cycle
        )
        
        return {
            "success": True,
            "subscription": subscription,
            "message": f"Welcome to TailorJob {tier.title()}!"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate subscription: {str(e)}"
        )


@router.get("/subscriptions/me")
async def get_my_subscription(user = Depends(get_current_user)):
    """Get current user's subscription details with usage"""
    try:
        # Extract user_id from user object
        if hasattr(user, 'id'):
            user_id = user.id
        elif isinstance(user, dict):
            user_id = user.get('id') or user.get('user_id')
        else:
            raise HTTPException(status_code=400, detail="Invalid user object")
        
        subscription = await subscription_service.get_user_subscription(user_id)
        usage_info = await get_usage_info(user_id)
        
        return {
            **subscription,
            **usage_info
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription: {str(e)}"
        )


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    reason: Optional[str] = "User requested cancellation",
    user = Depends(get_current_user)
):
    """
    Cancel user's subscription.
    Subscription remains active until end of billing period.
    """
    try:
        # Extract user_id from user object
        if hasattr(user, 'id'):
            user_id = user.id
        elif isinstance(user, dict):
            user_id = user.get('id') or user.get('user_id')
        else:
            raise HTTPException(status_code=400, detail="Invalid user object")
        
        # Get user's subscription
        subscription = await subscription_service.get_user_subscription(user_id)
        
        if not subscription.get('subscription_id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        # Cancel with PayPal
        paypal_service.cancel_subscription(
            subscription_id=subscription['subscription_id'],
            reason=reason
        )
        
        # Update status in database
        await subscription_service.update_subscription_status(
            paypal_subscription_id=subscription['subscription_id'],
            status='cancelled',
            cancelled_at=datetime.utcnow()
        )
        
        return {
            "success": True,
            "message": "Subscription cancelled. You can continue using until end of billing period.",
            "period_end": subscription.get('current_period_end')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


class UpgradeSubscriptionRequest(BaseModel):
    """Request to upgrade subscription"""
    new_tier: str


@router.post("/subscriptions/upgrade")
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    user = Depends(get_current_user)
):
    """
    Upgrade to a higher tier.
    Changes take effect immediately with prorated billing.
    
    Note: In production, this should update the PayPal subscription plan.
    For now, it creates a new subscription (user must approve).
    """
    new_tier = request.new_tier
    try:
        # Extract user_id from user object
        if hasattr(user, 'id'):
            user_id = user.id
        elif isinstance(user, dict):
            user_id = user.get('id') or user.get('user_id')
        else:
            raise HTTPException(status_code=400, detail="Invalid user object")
        
        # Validate tier
        if new_tier not in ['basic', 'pro', 'enterprise']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tier"
            )
        
        # Get current subscription
        current_sub = await subscription_service.get_user_subscription(user_id)
        
        if current_sub['tier'] == new_tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already on this tier"
            )
        
        # Determine the plan_id for the new tier
        plan_key = f"{new_tier}_monthly"  # e.g., 'pro_monthly'
        
        # Get the actual PayPal plan ID
        paypal_plan_id = paypal_service.PLAN_IDS.get(plan_key)
        if not paypal_plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan: {plan_key}"
            )
        
        # Get user info for email (optional)
        from app.utils.supabase_client import supabase
        user_result = supabase.table('profiles').select('email').eq('id', user_id).single().execute()
        user_email = user_result.data.get('email') if user_result.data else None
        
        # Get current URL for return/cancel URLs
        # Use FRONTEND_URL from settings, fallback to localhost:8080 for dev
        base_url = settings.FRONTEND_URL or "http://localhost:8080"
        
        # Create new subscription with PayPal (upgrade flow)
        paypal_response = paypal_service.create_subscription(
            plan_id=plan_key,
            return_url=f"{base_url}/account?success=true",
            cancel_url=f"{base_url}/pricing?cancelled=true",
            user_email=user_email
        )
        
        # Extract approval URL
        approval_url = None
        for link in paypal_response.get('links', []):
            if link['rel'] == 'approve':
                approval_url = link['href']
                break
        
        if not approval_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get PayPal approval URL"
            )
        
        return CreateSubscriptionResponse(
            subscription_id=paypal_response['id'],
            approval_url=approval_url,
            status=paypal_response['status']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade subscription: {str(e)}"
        )




# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

@router.post("/webhooks/paypal")
async def handle_paypal_webhook(
    request: Request,
    paypal_transmission_id: str = Header(..., alias="Paypal-Transmission-Id"),
    paypal_transmission_time: str = Header(..., alias="Paypal-Transmission-Time"),
    paypal_cert_url: str = Header(..., alias="Paypal-Cert-Url"),
    paypal_auth_algo: str = Header(..., alias="Paypal-Auth-Algo"),
    paypal_transmission_sig: str = Header(..., alias="Paypal-Transmission-Sig")
):
    """
    Handle PayPal webhook events.
    
    Events handled:
    - BILLING.SUBSCRIPTION.ACTIVATED
    - BILLING.SUBSCRIPTION.CANCELLED
    - BILLING.SUBSCRIPTION.SUSPENDED
    - BILLING.SUBSCRIPTION.EXPIRED
    - PAYMENT.SALE.COMPLETED
    - PAYMENT.SALE.REFUNDED
    """
    try:
        # Get webhook body
        body = await request.body()
        webhook_event = json.loads(body)
        
        # Verify webhook signature
        is_valid = paypal_service.verify_webhook_signature(
            transmission_id=paypal_transmission_id,
            transmission_time=paypal_transmission_time,
            cert_url=paypal_cert_url,
            auth_algo=paypal_auth_algo,
            transmission_sig=paypal_transmission_sig,
            webhook_event=webhook_event
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Store webhook event for audit
        from app.utils.supabase_client import supabase
        supabase.table('webhook_events').insert({
            'paypal_event_id': webhook_event['id'],
            'event_type': webhook_event['event_type'],
            'resource_type': webhook_event.get('resource_type'),
            'payload': webhook_event,
            'processed': False
        }).execute()
        
        # Process event based on type
        event_type = webhook_event['event_type']
        resource = webhook_event.get('resource', {})
        
        if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            await _handle_subscription_activated(resource)
        
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            await _handle_subscription_cancelled(resource)
        
        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            await _handle_subscription_suspended(resource)
        
        elif event_type == 'BILLING.SUBSCRIPTION.EXPIRED':
            await _handle_subscription_expired(resource)
        
        elif event_type == 'PAYMENT.SALE.COMPLETED':
            await _handle_payment_completed(resource)
        
        elif event_type == 'PAYMENT.SALE.REFUNDED':
            await _handle_payment_refunded(resource)
        
        # Mark webhook as processed
        supabase.table('webhook_events').update({
            'processed': True,
            'processed_at': datetime.utcnow().isoformat()
        }).eq('paypal_event_id', webhook_event['id']).execute()
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

async def _handle_subscription_activated(resource: Dict):
    """Handle subscription activation"""
    subscription_id = resource.get('id')
    if subscription_id:
        await subscription_service.update_subscription_status(
            paypal_subscription_id=subscription_id,
            status='active'
        )


async def _handle_subscription_cancelled(resource: Dict):
    """Handle subscription cancellation"""
    subscription_id = resource.get('id')
    if subscription_id:
        await subscription_service.update_subscription_status(
            paypal_subscription_id=subscription_id,
            status='cancelled',
            cancelled_at=datetime.utcnow()
        )


async def _handle_subscription_suspended(resource: Dict):
    """Handle subscription suspension (payment failed)"""
    subscription_id = resource.get('id')
    if subscription_id:
        await subscription_service.update_subscription_status(
            paypal_subscription_id=subscription_id,
            status='suspended'
        )


async def _handle_subscription_expired(resource: Dict):
    """Handle subscription expiration"""
    subscription_id = resource.get('id')
    if subscription_id:
        await subscription_service.update_subscription_status(
            paypal_subscription_id=subscription_id,
            status='expired'
        )


async def _handle_payment_completed(resource: Dict):
    """Handle successful payment"""
    # Extract payment details
    sale_id = resource.get('id')
    amount = float(resource.get('amount', {}).get('total', 0))
    currency = resource.get('amount', {}).get('currency', 'USD')
    
    # Get subscription info
    billing_agreement_id = resource.get('billing_agreement_id')
    
    if billing_agreement_id:
        # Get subscription from database
        subscription = await subscription_service.get_subscription_by_paypal_id(billing_agreement_id)
        
        if subscription:
            # Record payment
            await subscription_service.record_payment(
                user_id=subscription['user_id'],
                subscription_id=subscription['id'],
                paypal_payment_id=sale_id,
                paypal_order_id=None,
                amount=amount,
                currency=currency,
                status='completed',
                payment_type='subscription'
            )


async def _handle_payment_refunded(resource: Dict):
    """Handle payment refund"""
    sale_id = resource.get('sale_id')
    
    if sale_id:
        # Update payment status
        from app.utils.supabase_client import supabase
        supabase.table('payments').update({
            'status': 'refunded'
        }).eq('paypal_payment_id', sale_id).execute()