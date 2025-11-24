#!/usr/bin/env python3
"""
Script to re-queue failed CV parsing jobs.
Run this to retry parsing for CVs stuck in 'uploaded' or 'error' status.
"""
import asyncio
from app.utils.supabase_client import supabase
from app.services.queue import queue_service

async def requeue_failed_cvs():
    """Find and re-queue failed CV parsing jobs"""
    print("🔍 Searching for CVs that need re-parsing...")
    
    # Find CVs with 'uploaded' or 'error' status
    result = supabase.table("cvs")\
        .select("*")\
        .in_("status", ["uploaded", "error"])\
        .execute()
    
    if not result.data:
        print("✅ No CVs need re-parsing!")
        return
    
    print(f"📋 Found {len(result.data)} CV(s) to re-queue:")
    for cv in result.data:
        print(f"  - {cv['id'][:8]}... | {cv['original_filename']} | Status: {cv['status']}")
    
    print("\n🔄 Re-queueing jobs...")
    success_count = 0
    fail_count = 0
    
    for cv in result.data:
        try:
            job_id = await queue_service.enqueue_cv_parse(cv["id"], cv["user_id"])
            print(f"✅ Queued: {cv['id'][:8]}... (job_id: {job_id})")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to queue {cv['id'][:8]}...: {str(e)}")
            fail_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Successfully queued: {success_count}")
    print(f"  ❌ Failed: {fail_count}")

if __name__ == "__main__":
    asyncio.run(requeue_failed_cvs())