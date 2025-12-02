#!/usr/bin/env python3
"""Check subscriptions in the database."""
import os
import sys
from supabase import create_client

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings

def main():
    """Query and display subscriptions."""
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    print("Querying subscriptions table...\n")
    
    result = supabase.table('subscriptions') \
        .select('tier, status, paypal_subscription_id, created_at, updated_at, user_id') \
        .order('updated_at', desc=True) \
        .limit(5) \
        .execute()
    
    if not result.data:
        print("No subscriptions found.")
        return
    
    print(f"Found {len(result.data)} subscription(s):\n")
    print(f"{'Tier':<10} {'Status':<12} {'PayPal ID':<25} {'Created':<20} {'Updated':<20}")
    print("-" * 100)
    
    for sub in result.data:
        print(f"{sub['tier']:<10} {sub['status']:<12} {sub['paypal_subscription_id'][:24]:<25} "
              f"{sub['created_at'][:19]:<20} {sub['updated_at'][:19]:<20}")
    
    print("\nFull subscription details:")
    for i, sub in enumerate(result.data, 1):
        print(f"\n{i}. Subscription:")
        for key, value in sub.items():
            print(f"   {key}: {value}")

if __name__ == '__main__':
    main()