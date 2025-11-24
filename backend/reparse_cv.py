#!/usr/bin/env python3
"""
Script to reparse a CV that was already uploaded.
This is useful after updating the CV parsing logic.
"""
import asyncio
import sys
from app.services.queue import queue_service

async def reparse_cv(cv_id: str, user_id: str):
    """Enqueue a CV for reparsing"""
    try:
        job_id = await queue_service.enqueue_cv_parse(cv_id, user_id)
        print(f"✅ CV {cv_id} enqueued for reparsing with job ID: {job_id}")
        print(f"📊 Check the backend logs to monitor parsing progress")
    except Exception as e:
        print(f"❌ Failed to enqueue CV for reparsing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reparse_cv.py <cv_id> <user_id>")
        print("\nExample:")
        print("  python reparse_cv.py 87872e28-8276-4a69-9e96-ee34e5640ae0 12601009-4532-4c5f-89f5-1f1685d13fea")
        sys.exit(1)
    
    cv_id = sys.argv[1]
    user_id = sys.argv[2]
    
    asyncio.run(reparse_cv(cv_id, user_id))