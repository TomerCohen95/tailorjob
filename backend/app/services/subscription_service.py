"""
Subscription business logic service.
Handles subscription lifecycle, upgrades, downgrades, and usage tracking.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.utils.supabase_client import supabase


class SubscriptionService:
    """Service for managing user subscriptions and usage limits"""
    
    # Tier usage limits (-1 = unlimited)
    TIER_LIMITS = {
        'free': {
            'cvs': 3,
            'matches': 5,
            'tailored': 0,
            'exports': 0,
            'matcher_version': 'v3'  # Basic matching
        },
        'basic': {
            'cvs': 10,
            'matches': 50,
            'tailored': 5,
            'exports': 5,
            'matcher_version': 'v3'  # Advanced matching
        },
        'pro': {
            'cvs': -1,  # unlimited
            'matches': -1,
            'tailored': -1,
            'exports': -1,
            'matcher_version': 'v5'  # Premium matching
        },
        'enterprise': {
            'cvs': -1,
            'matches': -1,
            'tailored': -1,
            'exports': -1,
            'matcher_version': 'v5',
            'api_access': True,
            'team_collaboration': True
        }
    }
    
    # Feature to database column mapping
    FEATURE_COLUMNS = {
        'cv_upload': 'cvs_uploaded',
        'job_match': 'jobs_matched',
        'tailor_cv': 'cvs_tailored',
        'export_pdf': 'pdfs_exported'
    }
    
    async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's current subscription with usage data.
        
        Returns:
            {
                "tier": "free",
                "status": "active",
                "usage": {"cvs": 1, "matches": 3, ...},
                "limits": {"cvs": 3, "matches": 5, ...},
                "subscription_id": "...",
                "current_period_end": "2025-02-01T00:00:00Z"
            }
        """
        # Get subscription from database
        result = supabase.table('subscriptions').select('*').eq('user_id', user_id).maybe_single().execute()
        
        if not result or not result.data:
            # No subscription = free tier
            return {
                "tier": "free",
                "status": "active",
                "usage": await self.get_current_usage(user_id),
                "limits": self.TIER_LIMITS['free'],
                "subscription_id": None,
                "current_period_end": None
            }
        
        subscription = result.data
        
        # If subscription is cancelled or expired, use free tier limits
        tier = subscription['tier']
        status = subscription['status']
        if status in ['cancelled', 'expired']:
            tier = 'free'
        
        return {
            "tier": tier,
            "status": status,
            "usage": await self.get_current_usage(user_id),
            "limits": self.TIER_LIMITS[tier],
            "subscription_id": subscription['paypal_subscription_id'],
            "current_period_end": subscription['current_period_end'],
            "cancelled_at": subscription.get('cancelled_at')
        }
    
    async def get_current_usage(self, user_id: str) -> Dict[str, int]:
        """
        Get current billing period usage for user.
        
        Returns:
            {"cvs": 1, "matches": 3, "tailored": 0, "exports": 0}
        """
        # Use PostgreSQL function for efficiency
        result = supabase.rpc('get_current_usage', {'p_user_id': user_id}).execute()
        
        if not result.data or not result.data[0]:
            return {
                'cvs': 0,
                'matches': 0,
                'tailored': 0,
                'exports': 0
            }
        
        usage = result.data[0]
        return {
            'cvs': usage['cvs_uploaded'],
            'matches': usage['jobs_matched'],
            'tailored': usage['cvs_tailored'],
            'exports': usage['pdfs_exported']
        }
    
    async def can_use_feature(self, user_id: str, feature: str) -> tuple[bool, Optional[str]]:
        """
        Check if user can use a feature based on their tier and usage.
        
        Args:
            user_id: User UUID
            feature: Feature name ('cv_uploads', 'job_matches', 'tailored_cvs', 'export_pdf')
        
        Returns:
            (allowed: bool, error_message: Optional[str])
        """
        subscription = await self.get_user_subscription(user_id)
        
        # Map feature to usage key
        usage_key = feature.replace('cv_uploads', 'cvs').replace('job_matches', 'matches').replace('tailored_cvs', 'tailored').replace('export_pdf', 'exports')
        
        limit = subscription['limits'].get(usage_key, 0)
        current_usage = subscription['usage'].get(usage_key, 0)
        
        print(f"📊 Feature: {feature} -> {usage_key}")
        print(f"📊 Current usage: {current_usage} / {limit}")
        print(f"📊 Tier: {subscription['tier']}")
        
        # -1 means unlimited
        if limit == -1:
            print(f"✅ Unlimited access")
            return True, None
        
        # Check if under limit
        if current_usage < limit:
            print(f"✅ Under limit: {current_usage} < {limit}")
            return True, None
        
        # Over limit
        tier = subscription['tier']
        if tier == 'free':
            return False, f"Free tier limit reached ({limit} {usage_key}). Upgrade to Basic for more!"
        elif tier == 'basic':
            return False, f"Basic tier limit reached ({limit} {usage_key}). Upgrade to Pro for unlimited!"
        else:
            return False, f"Usage limit reached. Contact support."
    
    async def track_usage(self, user_id: str, feature: str, amount: int = 1) -> bool:
        """
        Increment usage counter for a feature.
        
        Args:
            user_id: User UUID
            feature: Feature name ('cv_uploads', 'job_matches', 'tailored_cvs', 'export_pdf')
            amount: Amount to increment (default: 1)
        
        Returns:
            True if successful
        """
        # Map decorator feature names to database column names
        feature_map = {
            'cv_uploads': 'cv_upload',
            'job_matches': 'job_match',
            'tailored_cvs': 'tailor_cv',
            'export_pdf': 'export_pdf'
        }
        
        db_feature = feature_map.get(feature, feature)
        
        try:
            # Use PostgreSQL function for atomic increment
            result = supabase.rpc('increment_usage', {
                'p_user_id': user_id,
                'p_feature': db_feature,
                'p_amount': amount
            }).execute()
            print(f"✅ Usage tracked: {feature} -> {db_feature} for user {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error tracking usage for {feature}: {e}")
            return False
    
    async def create_subscription(
        self,
        user_id: str,
        paypal_subscription_id: str,
        paypal_plan_id: str,
        tier: str,
        amount: float,
        currency: str = 'USD',
        billing_cycle: str = 'monthly'
    ) -> Dict[str, Any]:
        """
        Create a new subscription in database after PayPal approval.
        
        Returns:
            Created subscription record
        """
        now = datetime.utcnow()
        period_end = now + timedelta(days=30 if billing_cycle == 'monthly' else 365)
        
        subscription_data = {
            'user_id': user_id,
            'paypal_subscription_id': paypal_subscription_id,
            'paypal_plan_id': paypal_plan_id,
            'tier': tier,
            'status': 'active',
            'amount_decimal': amount,
            'currency': currency,
            'billing_cycle': billing_cycle,
            'current_period_start': now.isoformat(),
            'current_period_end': period_end.isoformat()
        }
        
        # Upsert (create or update)
        result = supabase.table('subscriptions').upsert(
            subscription_data,
            on_conflict='user_id'
        ).execute()
        
        # Update profile tier
        supabase.table('profiles').update({
            'subscription_tier': tier,
            'subscription_status': 'active'
        }).eq('id', user_id).execute()
        
        # Initialize usage for new period
        supabase.rpc('initialize_usage_period', {
            'p_user_id': user_id,
            'p_period_start': now.isoformat(),
            'p_period_end': period_end.isoformat()
        }).execute()
        
        return result.data[0] if result.data else None
    
    async def update_subscription_status(
        self,
        paypal_subscription_id: str,
        status: str,
        cancelled_at: Optional[datetime] = None
    ) -> bool:
        """
        Update subscription status (from webhook).
        
        Args:
            paypal_subscription_id: PayPal subscription ID
            status: New status ('active', 'cancelled', 'expired', 'suspended')
            cancelled_at: Cancellation timestamp if status is 'cancelled'
        """
        update_data = {'status': status}
        
        if cancelled_at:
            update_data['cancelled_at'] = cancelled_at.isoformat()
        
        # If cancelling or expiring, also downgrade to free tier
        if status in ['cancelled', 'expired']:
            update_data['tier'] = 'free'
        
        result = supabase.table('subscriptions').update(
            update_data
        ).eq('paypal_subscription_id', paypal_subscription_id).execute()
        
        # Also update profile status and tier
        if result.data:
            user_id = result.data[0]['user_id']
            profile_update = {'subscription_status': status}
            
            # Update profile tier to free if cancelled/expired
            if status in ['cancelled', 'expired']:
                profile_update['subscription_tier'] = 'free'
            
            supabase.table('profiles').update(profile_update).eq('id', user_id).execute()
        
        return bool(result.data)
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_tier: str,
        new_plan_id: str
    ) -> Dict[str, Any]:
        """
        Upgrade user to a higher tier.
        Changes take effect immediately, prorated billing handled by PayPal.
        
        Returns:
            Updated subscription
        """
        # Get current subscription
        result = supabase.table('subscriptions').select('*').eq('user_id', user_id).single().execute()
        
        if not result.data:
            raise ValueError("No subscription found")
        
        current_sub = result.data
        
        # Validate upgrade path
        tier_order = ['free', 'basic', 'pro', 'enterprise']
        if tier_order.index(new_tier) <= tier_order.index(current_sub['tier']):
            raise ValueError("Can only upgrade to higher tier")
        
        # Update subscription
        update_data = {
            'tier': new_tier,
            'paypal_plan_id': new_plan_id
        }
        
        result = supabase.table('subscriptions').update(
            update_data
        ).eq('user_id', user_id).execute()
        
        # Update profile
        supabase.table('profiles').update({
            'subscription_tier': new_tier
        }).eq('id', user_id).execute()
        
        return result.data[0] if result.data else None
    
    async def downgrade_subscription(
        self,
        user_id: str,
        new_tier: str
    ) -> Dict[str, Any]:
        """
        Downgrade user to a lower tier.
        Takes effect at end of current billing period.
        
        Note: Actual PayPal plan change should be handled via PayPal API
        This just records the pending change.
        """
        # Get current subscription
        result = supabase.table('subscriptions').select('*').eq('user_id', user_id).single().execute()
        
        if not result.data:
            raise ValueError("No subscription found")
        
        # For now, just mark as pending change
        # In production, you'd create a separate "pending_changes" table
        # or add columns like 'pending_tier', 'pending_at'
        
        return result.data
    
    async def record_payment(
        self,
        user_id: str,
        subscription_id: Optional[str],
        paypal_payment_id: str,
        paypal_order_id: Optional[str],
        amount: float,
        currency: str,
        status: str,
        payment_type: str = 'subscription'
    ) -> Dict[str, Any]:
        """
        Record a payment transaction.
        
        Args:
            user_id: User UUID
            subscription_id: Subscription UUID (from our DB)
            paypal_payment_id: PayPal payment/capture ID
            paypal_order_id: PayPal order ID
            amount: Payment amount
            currency: Currency code
            status: Payment status ('pending', 'completed', 'failed', 'refunded')
            payment_type: 'subscription' or 'one_time'
        """
        payment_data = {
            'user_id': user_id,
            'subscription_id': subscription_id,
            'paypal_payment_id': paypal_payment_id,
            'paypal_order_id': paypal_order_id,
            'amount_decimal': amount,
            'currency': currency,
            'status': status,
            'payment_type': payment_type
        }
        
        result = supabase.table('payments').insert(payment_data).execute()
        
        return result.data[0] if result.data else None
    
    async def get_subscription_by_paypal_id(self, paypal_subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by PayPal subscription ID"""
        result = supabase.table('subscriptions').select('*').eq(
            'paypal_subscription_id',
            paypal_subscription_id
        ).single().execute()
        
        return result.data if result.data else None


# Singleton instance
subscription_service = SubscriptionService()