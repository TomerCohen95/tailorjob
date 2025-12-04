#!/usr/bin/env python3
"""Check if a user is properly signed up in the system."""

import asyncio
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def check_user_signup(email: str):
    """Check if user is properly signed up."""
    print(f"\n{'='*60}")
    print(f"Checking signup status for: {email}")
    print(f"{'='*60}\n")

    # 1. Check auth.users table
    print("1. Checking auth.users table...")
    try:
        # Note: We can't directly query auth.users with regular Supabase client
        # We'll check through profiles table which should have user_id from auth
        profiles_response = supabase.table("profiles").select("*").eq("email", email).execute()
        
        if profiles_response.data:
            profile = profiles_response.data[0]
            print(f"   ✓ Profile found:")
            print(f"     - User ID: {profile.get('id')}")
            print(f"     - Email: {profile.get('email')}")
            print(f"     - Full Name: {profile.get('full_name')}")
            print(f"     - Created: {profile.get('created_at')}")
            print(f"     - Updated: {profile.get('updated_at')}")
            user_id = profile.get('id')
        else:
            print(f"   ✗ No profile found for {email}")
            user_id = None
    except Exception as e:
        print(f"   ✗ Error checking profile: {e}")
        user_id = None

    if not user_id:
        print("\n❌ User not found in system")
        return

    # 2. Check CVs
    print("\n2. Checking CVs...")
    try:
        cvs_response = supabase.table("cvs").select("*").eq("user_id", user_id).execute()
        if cvs_response.data:
            print(f"   ✓ Found {len(cvs_response.data)} CV(s):")
            for cv in cvs_response.data:
                print(f"     - CV ID: {cv.get('id')}")
                print(f"       File: {cv.get('file_name')}")
                print(f"       Status: {cv.get('status')}")
                print(f"       Primary: {cv.get('is_primary', False)}")
                print(f"       Created: {cv.get('created_at')}")
        else:
            print(f"   ℹ No CVs uploaded yet")
    except Exception as e:
        print(f"   ✗ Error checking CVs: {e}")

    # 3. Check CV sections
    print("\n3. Checking CV sections...")
    try:
        # cv_sections links through cv_id, not user_id directly
        sections_response = supabase.table("cv_sections").select("*, cvs!inner(user_id)").eq("cvs.user_id", user_id).execute()
        if sections_response.data:
            print(f"   ✓ Found {len(sections_response.data)} CV section(s) parsed")
        else:
            print(f"   ℹ No CV sections parsed yet")
    except Exception as e:
        print(f"   ✗ Error checking CV sections: {e}")

    # 4. Check jobs
    print("\n4. Checking saved jobs...")
    try:
        jobs_response = supabase.table("jobs").select("*").eq("user_id", user_id).execute()
        if jobs_response.data:
            print(f"   ✓ Found {len(jobs_response.data)} saved job(s)")
            for job in jobs_response.data[:3]:  # Show first 3
                print(f"     - {job.get('title')} at {job.get('company')}")
        else:
            print(f"   ℹ No jobs saved yet")
    except Exception as e:
        print(f"   ✗ Error checking jobs: {e}")

    # 5. Check subscriptions
    print("\n5. Checking subscription status...")
    try:
        subs_response = supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
        if subs_response.data:
            sub = subs_response.data[0]
            print(f"   ✓ Subscription found:")
            print(f"     - Plan: {sub.get('plan_name')}")
            print(f"     - Status: {sub.get('status')}")
            print(f"     - PayPal ID: {sub.get('paypal_subscription_id')}")
            print(f"     - Started: {sub.get('current_period_start')}")
            print(f"     - Ends: {sub.get('current_period_end')}")
        else:
            print(f"   ℹ No active subscription (free tier)")
    except Exception as e:
        print(f"   ✗ Error checking subscription: {e}")

    # 6. Check CV-Job matches
    print("\n6. Checking CV-Job matches...")
    try:
        matches_response = supabase.table("cv_job_matches").select("*").eq("user_id", user_id).execute()
        if matches_response.data:
            print(f"   ✓ Found {len(matches_response.data)} match(es)")
            # Show score distribution
            scores = [m.get('match_score', 0) for m in matches_response.data]
            if scores:
                print(f"     - Avg score: {sum(scores)/len(scores):.1f}")
                print(f"     - Best score: {max(scores):.1f}")
        else:
            print(f"   ℹ No CV-Job matches yet")
    except Exception as e:
        print(f"   ✗ Error checking matches: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if user_id:
        print(f"✓ User account exists")
        print(f"  User ID: {user_id}")
        print(f"  Email: {email}")
        print("\nUser can:")
        print("  - Log in to the application")
        print("  - Upload CVs")
        print("  - Save jobs")
        print("  - Generate CV matches")
    else:
        print("✗ User account NOT found")
        print("\nPossible issues:")
        print("  - User hasn't completed signup")
        print("  - Email verification pending")
        print("  - Account deleted")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "amirfel4@gmail.com"
    
    check_user_signup(email)