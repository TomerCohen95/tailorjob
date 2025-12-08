"""
List all users in the database
"""

from app.utils.supabase_client import supabase


def list_users():
    """List all users"""
    print("🔍 Fetching all users...")
    
    try:
        result = supabase.table('profiles').select('id, email, full_name, subscription_tier, subscription_status').execute()
        
        if not result or not result.data:
            print("❌ No users found")
            return
        
        users = result.data
        print(f"\n✅ Found {len(users)} users:\n")
        
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.get('full_name', 'N/A')} ({user.get('email', 'N/A')})")
            print(f"   ID: {user['id']}")
            print(f"   Tier: {user.get('subscription_tier', 'free')}")
            print(f"   Status: {user.get('subscription_status', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    list_users()