"""
Grant pro subscription by user ID
Usage: python grant_pro_by_id.py <user_id>
"""

import sys
from datetime import datetime, timedelta
from app.utils.supabase_client import supabase


def grant_pro_subscription(user_id: str):
    """Grant pro subscription to a user by ID"""
    
    # 1. Verify user exists
    print(f"🔍 Looking up user ID: {user_id}")
    
    try:
        result = supabase.table('profiles').select('id, email, full_name').eq('id', user_id).maybe_single().execute()
        
        if not result or not result.data:
            print(f"❌ User not found with ID: {user_id}")
            return
    except Exception as e:
        print(f"❌ Error looking up user: {e}")
        return
    
    user = result.data
    print(f"✅ Found user: {user.get('full_name', 'N/A')} ({user.get('email', 'N/A')})")
    
    # 2. Check existing subscription
    print("\n🔍 Checking existing subscription...")
    try:
        existing = supabase.table('subscriptions').select('*').eq('user_id', user_id).maybe_single().execute()
        
        if existing and existing.data:
            print(f"📋 Existing subscription found:")
            print(f"   Tier: {existing.data['tier']}")
            print(f"   Status: {existing.data['status']}")
            print(f"   PayPal ID: {existing.data.get('paypal_subscription_id', 'N/A')}")
        else:
            print("📋 No existing subscription found")
    except Exception as e:
        print(f"📋 No existing subscription found (or error: {e})")
    
    # 3. Create/Update pro subscription
    print("\n🎁 Granting PRO subscription...")
    now = datetime.utcnow()
    period_end = now + timedelta(days=365)  # 1 year for pro
    
    subscription_data = {
        'user_id': user_id,
        'paypal_subscription_id': f'MANUAL_PRO_{user_id[:8]}',  # Manual subscription ID
        'paypal_plan_id': 'MANUAL_PRO_PLAN',
        'tier': 'pro',
        'status': 'active',
        'amount_decimal': 0.00,  # Complimentary
        'currency': 'USD',
        'billing_cycle': 'yearly',
        'current_period_start': now.isoformat(),
        'current_period_end': period_end.isoformat()
    }
    
    try:
        # Upsert (create or update)
        result = supabase.table('subscriptions').upsert(
            subscription_data,
            on_conflict='user_id'
        ).execute()
        
        if result and result.data:
            print("✅ Subscription created/updated successfully!")
            print(f"   Tier: pro")
            print(f"   Status: active")
            print(f"   Valid until: {period_end.strftime('%Y-%m-%d')}")
        
        # 4. Update profile
        print("\n📝 Updating profile...")
        profile_result = supabase.table('profiles').update({
            'subscription_tier': 'pro',
            'subscription_status': 'active'
        }).eq('id', user_id).execute()
        
        if profile_result and profile_result.data:
            print("✅ Profile updated successfully!")
        
        # 5. Initialize usage for new period
        print("\n📊 Initializing usage tracking...")
        usage_result = supabase.rpc('initialize_usage_period', {
            'p_user_id': user_id,
            'p_period_start': now.isoformat(),
            'p_period_end': period_end.isoformat()
        }).execute()
        
        print("✅ Usage tracking initialized!")
        
        # 6. Verify final state
        print("\n🔍 Verifying final state...")
        final_sub = supabase.table('subscriptions').select('*').eq('user_id', user_id).single().execute()
        final_profile = supabase.table('profiles').select('subscription_tier, subscription_status').eq('id', user_id).single().execute()
        
        print(f"\n✨ SUCCESS! User {user.get('email', 'N/A')} now has:")
        print(f"   Subscription Tier: {final_sub.data['tier']}")
        print(f"   Subscription Status: {final_sub.data['status']}")
        print(f"   Profile Tier: {final_profile.data['subscription_tier']}")
        print(f"   Valid Until: {final_sub.data['current_period_end']}")
        print(f"\n🎉 Pro benefits:")
        print(f"   ✅ Unlimited CV uploads")
        print(f"   ✅ Unlimited job matches")
        print(f"   ✅ Unlimited CV tailoring")
        print(f"   ✅ Unlimited PDF exports")
        print(f"   ✅ Premium v5 matcher")
        
    except Exception as e:
        print(f"❌ Error granting subscription: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grant_pro_by_id.py <user_id>")
        print("\nAvailable users:")
        try:
            result = supabase.table('profiles').select('id, email, full_name').execute()
            if result and result.data:
                for user in result.data:
                    print(f"  - {user.get('full_name', 'N/A')} ({user.get('email', 'N/A')})")
                    print(f"    ID: {user['id']}")
        except Exception as e:
            print(f"Error fetching users: {e}")
        sys.exit(1)
    
    user_id = sys.argv[1]
    grant_pro_subscription(user_id)