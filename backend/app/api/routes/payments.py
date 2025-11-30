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

@router.post("/subscriptions/create", response_model=CreateSubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user_id: str = Header(..., alias="X-User-Id")
):
    """
    Create a new PayPal subscription.
    User must approve via returned approval_url.
    
    Returns approval URL for user to complete subscription on PayPal.
    """
    try:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.post("/subscriptions/activate")
async def activate_subscription(
    subscription_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """
    Activate subscription after user approves on PayPal.
    Called by frontend after PayPal redirects back.
    """
    try:
        # Get subscription details from PayPal
        paypal_subscription = paypal_service.get_subscription(subscription_id)
        
        if paypal_subscription['status'] != 'ACTIVE':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription not active: {paypal_subscription['status']}"
            )
        
        # Extract tier from plan_id
        plan_id = paypal_subscription['plan_id']
        tier = 'basic' if 'BASIC' in plan_id else 'pro' if 'PRO' in plan_id else 'basic'
        
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
async def get_my_subscription(
    user_id: str = Header(..., alias="X-User-Id")
):
    """Get current user's subscription details with usage"""
    try:
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
    user_id: str = Header(..., alias="X-User-Id")
):
    """
    Cancel user's subscription.
    Subscription remains active until end of billing period.
    """
    try:
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


@router.post("/subscriptions/upgrade")
async def upgrade_subscription(
    new_tier: str,
    new_plan_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """
    Upgrade to a higher tier.
    Changes take effect immediately with prorated billing.
    
    Note: In production, this should update the PayPal subscription plan.
    For now, it creates a new subscription (user must approve).
    """
    try:
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
        
        # For now, return instructions to create new subscription
        # In production, use PayPal's revision API to update plan
        return {
            "message": "To upgrade, please create a new subscription",
            "action": "create_new_subscription",
            "plan_id": new_plan_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade subscription: {str(e)}"
        )


@router.get("/usage")
async def get_usage(
    user_id: str = Header(..., alias="X-User-Id")
):
    """Get current usage and limits"""
    try:
        return await get_usage_info(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage: {str(e)}"
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