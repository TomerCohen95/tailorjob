#!/usr/bin/env python3
"""Check for CV upload errors for a specific user."""

import asyncio
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def check_cv_errors(email: str):
    """Check for CV upload errors."""
    print(f"\n{'='*70}")
    print(f"Checking CV Upload Errors for: {email}")
    print(f"{'='*70}\n")

    # 1. Get user ID
    profiles_response = supabase.table("profiles").select("*").eq("email", email).execute()
    
    if not profiles_response.data:
        print(f"❌ User not found: {email}")
        return
    
    user_id = profiles_response.data[0].get('id')
    print(f"User ID: {user_id}\n")

    # 2. Check ALL CVs (including failed ones)
    print("📄 Checking ALL CV records (including failed)...")
    try:
        all_cvs = supabase.table("cvs").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute()
        
        if all_cvs.data:
            print(f"Found {len(all_cvs.data)} CV record(s):\n")
            for idx, cv in enumerate(all_cvs.data, 1):
                print(f"CV #{idx}:")
                print(f"  ID: {cv.get('id')}")
                print(f"  Filename: {cv.get('original_filename', cv.get('file_name', 'N/A'))}")
                print(f"  Status: {cv.get('status')}")
                print(f"  File Path: {cv.get('file_path')}")
                print(f"  Uploaded: {cv.get('uploaded_at')}")
                print(f"  Parsed: {cv.get('parsed_at', 'Not parsed')}")
                
                error_msg = cv.get('error_message')
                if error_msg:
                    print(f"  ⚠️  ERROR MESSAGE: {error_msg}")
                
                # Check if file exists in storage
                file_path = cv.get('file_path')
                if file_path:
                    try:
                        # Try to get file info from storage
                        bucket_name = "cvs"
                        storage_path = file_path.replace(f"{bucket_name}/", "")
                        file_info = supabase.storage.from_(bucket_name).list(path=storage_path)
                        print(f"  📁 Storage Status: File exists")
                    except Exception as e:
                        print(f"  📁 Storage Status: Error checking - {str(e)[:100]}")
                
                print()
        else:
            print("  No CV records found")
    except Exception as e:
        print(f"  ✗ Error checking CVs: {e}")

    # 3. Check CV sections for any parsed data
    print("\n📋 Checking CV Sections (parsed data)...")
    try:
        sections = supabase.table("cv_sections").select("*, cvs!inner(user_id, original_filename, status)").eq("cvs.user_id", user_id).execute()
        
        if sections.data:
            print(f"Found {len(sections.data)} parsed CV section(s)")
        else:
            print("  No CV sections found (no successful parsing)")
    except Exception as e:
        print(f"  ✗ Error checking CV sections: {e}")

    # 4. Check storage bucket directly
    print("\n🗄️  Checking Storage Bucket...")
    try:
        bucket_name = "cvs"
        user_folder = f"{user_id}/"
        files = supabase.storage.from_(bucket_name).list(path=user_id)
        
        if files:
            print(f"  Found {len(files)} file(s) in storage:")
            for file in files:
                print(f"    - {file.get('name')} ({file.get('metadata', {}).get('size', 'unknown')} bytes)")
        else:
            print("  No files found in user's storage folder")
    except Exception as e:
        print(f"  ✗ Error checking storage: {str(e)[:200]}")

    # 5. Summary
    print(f"\n{'='*70}")
    print("DIAGNOSIS")
    print(f"{'='*70}")
    
    if all_cvs.data:
        failed_cvs = [cv for cv in all_cvs.data if cv.get('status') in ['failed', 'error']]
        pending_cvs = [cv for cv in all_cvs.data if cv.get('status') in ['uploaded', 'pending', 'processing']]
        success_cvs = [cv for cv in all_cvs.data if cv.get('status') == 'parsed']
        
        if failed_cvs:
            print(f"\n❌ {len(failed_cvs)} FAILED CV(s) found:")
            for cv in failed_cvs:
                print(f"\n  Filename: {cv.get('original_filename', 'N/A')}")
                print(f"  Error: {cv.get('error_message', 'No error message stored')}")
                print(f"  Uploaded: {cv.get('uploaded_at')}")
        
        if pending_cvs:
            print(f"\n⏳ {len(pending_cvs)} PENDING CV(s) found:")
            for cv in pending_cvs:
                print(f"  - {cv.get('original_filename', 'N/A')} (Status: {cv.get('status')})")
        
        if success_cvs:
            print(f"\n✅ {len(success_cvs)} SUCCESSFUL CV(s)")
        
        if not failed_cvs and not pending_cvs and not success_cvs:
            print("\n⚠️  CVs exist but have unknown status")
    else:
        print("\n✅ No failed uploads found - User may not have attempted upload yet")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "amirfel4@gmail.com"
    
    check_cv_errors(email)