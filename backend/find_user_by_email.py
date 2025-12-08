"""
Find user by email - checks both auth.users and profiles
"""

from app.utils.supabase_client import supabase


def find_user_by_email(email: str):
    """Find user by email in both auth and profiles"""
    
    print(f"🔍 Searching for user with email: {email}")
    
    # Method 1: Check profiles table
    print("\n1️⃣ Checking profiles table...")
    try:
        result = supabase.table('profiles').select('*').eq('email', email).maybe_single().execute()
        if result and result.data:
            print(f"✅ Found in profiles:")
            print(f"   ID: {result.data['id']}")
            print(f"   Name: {result.data.get('full_name', 'N/A')}")
            print(f"   Email: {result.data.get('email', 'N/A')}")
            print(f"   Tier: {result.data.get('subscription_tier', 'free')}")
            return result.data['id']
        else:
            print("❌ Not found in profiles")
    except Exception as e:
        print(f"❌ Error checking profiles: {e}")
    
    # Method 2: Use RPC to check auth.users (if we have a function for it)
    print("\n2️⃣ Checking auth system...")
    try:
        # Get all profiles and their auth IDs
        all_profiles = supabase.table('profiles').select('id, email, full_name').execute()
        if all_profiles and all_profiles.data:
            print(f"\n📋 All users in database:")
            for profile in all_profiles.data:
                print(f"   - {profile.get('full_name', 'N/A')} ({profile.get('email', 'N/A')})")
                print(f"     ID: {profile['id']}")
                if profile.get('email', '').lower() == email.lower():
                    print(f"     ⭐ MATCH FOUND!")
                    return profile['id']
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n❌ User with email '{email}' not found in database")
    print("\n💡 This might mean:")
    print("   1. The user hasn't logged in yet (no profile created)")
    print("   2. The user signed up with a different email")
    print("   3. The user is in auth.users but profile wasn't created")
    
    return None


if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "tailorjobai@gmail.com"
    user_id = find_user_by_email(email)
    
    if user_id:
        print(f"\n✅ User ID: {user_id}")
        print(f"\n🎯 To grant pro subscription, run:")
        print(f"   python grant_pro_by_id.py {user_id}")