"""
Update user email in profiles table
"""

import sys
from app.utils.supabase_client import supabase


def update_user_email(user_id: str, new_email: str):
    """Update user's email in profiles table"""
    
    print(f"🔍 Updating email for user ID: {user_id}")
    print(f"📧 New email: {new_email}")
    
    try:
        # Update profile
        result = supabase.table('profiles').update({
            'email': new_email
        }).eq('id', user_id).execute()
        
        if result and result.data:
            print(f"✅ Email updated successfully!")
            print(f"   User: {result.data[0].get('full_name', 'N/A')}")
            print(f"   New Email: {result.data[0].get('email')}")
        else:
            print("❌ Failed to update email")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_user_email.py <user_id> <new_email>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    new_email = sys.argv[2]
    update_user_email(user_id, new_email)