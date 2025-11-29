#!/usr/bin/env python3
"""
Clean all CVs, jobs, and match cache from database.
Use before committing v4.0 to ensure fresh testing.
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.utils.supabase_client import get_supabase


def clean_database():
    """Delete all CVs, jobs, and cached matches"""
    supabase = get_supabase()
    
    print("🧹 Cleaning database...")
    print()
    
    # 1. Delete all match cache
    try:
        result = supabase.table('cv_job_matches').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print(f"✅ Deleted {count} cached match scores")
    except Exception as e:
        print(f"⚠️  Error deleting matches: {e}")
    
    # 2. Delete all CV sections
    try:
        result = supabase.table('cv_sections').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print(f"✅ Deleted {count} CV sections")
    except Exception as e:
        print(f"⚠️  Error deleting CV sections: {e}")
    
    # 3. Delete all CVs
    try:
        result = supabase.table('cvs').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print(f"✅ Deleted {count} CVs")
    except Exception as e:
        print(f"⚠️  Error deleting CVs: {e}")
    
    # 4. Delete all jobs
    try:
        result = supabase.table('jobs').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print(f"✅ Deleted {count} jobs")
    except Exception as e:
        print(f"⚠️  Error deleting jobs: {e}")
    
    # 5. Delete all CV notifications
    try:
        result = supabase.table('cv_notifications').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print(f"✅ Deleted {count} CV notifications")
    except Exception as e:
        print(f"⚠️  Error deleting notifications: {e}")
    
    print()
    print("✨ Database cleaned successfully!")
    print()
    print("Next steps:")
    print("1. Upload a fresh CV")
    print("2. Scrape a fresh job")
    print("3. Enable v4.0: Set USE_MATCHER_V4=true in backend/.env")
    print("4. Test the match analysis")


if __name__ == "__main__":
    confirm = input("⚠️  This will delete ALL CVs, jobs, and matches. Continue? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        clean_database()
    else:
        print("❌ Cancelled")