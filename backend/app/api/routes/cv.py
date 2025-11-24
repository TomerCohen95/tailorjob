from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api.deps import get_current_user
from app.services.storage import storage_service
from app.services.queue import queue_service
from app.utils.supabase_client import supabase
import hashlib

router = APIRouter()

@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Upload a CV file.
    
    - Validates file type (PDF/DOCX)
    - Validates file size (max 10MB)
    - Uploads to Supabase Storage
    - Creates database record
    - Enqueues parsing job
    """
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )
    
    # Validate file size
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 10MB"
        )
    
    # Read file content
    content = await file.read()
    
    # Compute file hash for duplicate detection
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check if this exact file already exists for this user
    existing_cv = supabase.table("cvs")\
        .select("*")\
        .eq("user_id", user.id)\
        .eq("file_hash", file_hash)\
        .execute()
    
    if existing_cv.data:
        # File already exists
        existing = existing_cv.data[0]
        existing_status = existing["status"]
        print(f"📋 Duplicate detected: CV {existing['id'][:8]}... status={existing_status}")
        
        # If the existing CV hasn't been parsed yet, enqueue a parsing job
        if existing_status in ["uploaded", "error"]:
            print(f"🔄 Re-enqueueing parse job for existing CV: {existing['id']}")
            try:
                job_id = await queue_service.enqueue_cv_parse(existing["id"], user.id)
                print(f"✅ Job enqueued with ID: {job_id}")
                message = "CV already exists, re-parsing initiated"
            except Exception as e:
                print(f"⚠️  Queue error (non-fatal): {str(e)}")
                job_id = None
                message = "CV already exists. Re-parsing will start when worker reconnects."
            
            return {
                "cv_id": existing["id"],
                "job_id": job_id,
                "status": "uploaded",
                "message": message
            }
        
        # CV already parsed successfully - offer to re-parse
        print(f"⚠️  CV already parsed. Returning duplicate response.")
        return {
            "cv_id": existing["id"],
            "status": "duplicate",
            "message": "This CV already exists and is parsed",
            "existing_cv": {
                "id": existing["id"],
                "original_filename": existing["original_filename"],
                "created_at": existing["created_at"],
                "status": existing["status"]
            }
        }
    
    # Upload to storage (new file)
    file_path = await storage_service.upload_cv(
        content,
        file.filename,
        user.id
    )
    
    # Create database record with file hash and set as primary
    result = supabase.table("cvs").insert({
        "user_id": user.id,
        "original_filename": file.filename,
        "file_path": file_path,
        "file_size": file.size,
        "mime_type": file.content_type,
        "status": "uploaded",
        "file_hash": file_hash,
        "is_primary": True  # New uploads are automatically set as primary
    }).execute()
    
    cv_id = result.data[0]["id"]
    
    # Enqueue parsing job with error handling
    print(f"🔄 Enqueueing CV parse job for CV: {cv_id}, user: {user.id}")
    try:
        job_id = await queue_service.enqueue_cv_parse(cv_id, user.id)
        print(f"✅ Job enqueued with ID: {job_id}")
        message = "CV uploaded successfully, parsing started"
    except Exception as e:
        print(f"⚠️  Queue error (non-fatal): {str(e)}")
        job_id = None
        message = "CV uploaded successfully. Parsing will start when worker reconnects."
    
    return {
        "cv_id": cv_id,
        "job_id": job_id,
        "status": "uploaded",
        "message": message
    }

@router.get("/status/{job_id}")
async def get_parse_status(
    job_id: str,
    user = Depends(get_current_user)
):
    """Get the status of a CV parsing job"""
    status = await queue_service.get_job_status(job_id)
    return status

@router.get("/list")
async def list_cvs(user = Depends(get_current_user)):
    """List all CVs for the current user"""
    result = supabase.table("cvs")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("created_at", desc=True)\
        .execute()
    
    return result.data

@router.get("/notifications")
async def get_notifications(user = Depends(get_current_user)):
    """Get all unread notifications for the current user"""
    result = supabase.table("cv_notifications")\
        .select("*")\
        .eq("user_id", user.id)\
        .eq("read", False)\
        .order("created_at", desc=True)\
        .execute()
    
    return result.data

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user = Depends(get_current_user)):
    """Mark a notification as read"""
    # Verify notification belongs to user
    notification = supabase.table("cv_notifications")\
        .select("*")\
        .eq("id", notification_id)\
        .eq("user_id", user.id)\
        .single()\
        .execute()
    
    if not notification.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Mark as read
    supabase.table("cv_notifications")\
        .update({"read": True})\
        .eq("id", notification_id)\
        .execute()
    
    return {"message": "Notification marked as read"}

@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, user = Depends(get_current_user)):
    """Delete a notification"""
    # Verify notification belongs to user
    notification = supabase.table("cv_notifications")\
        .select("id")\
        .eq("id", notification_id)\
        .eq("user_id", user.id)\
        .execute()
    
    if not notification.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Delete notification (no need to capture response)
    try:
        supabase.table("cv_notifications")\
            .delete()\
            .eq("id", notification_id)\
            .eq("user_id", user.id)\
            .execute()
    except Exception as e:
        # Ignore postgrest response parsing errors, deletion was successful
        print(f"⚠️  Notification deleted but response parsing failed: {str(e)}")
    
    return {"message": "Notification deleted"}

@router.get("/{cv_id}")
async def get_cv(cv_id: str, user = Depends(get_current_user)):
    """Get a specific CV with its parsed sections"""
    # Get CV metadata
    cv_result = supabase.table("cvs")\
        .select("*")\
        .eq("id", cv_id)\
        .eq("user_id", user.id)\
        .single()\
        .execute()
    
    if not cv_result.data:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Get parsed sections if available
    sections_result = supabase.table("cv_sections")\
        .select("*")\
        .eq("cv_id", cv_id)\
        .execute()
    
    return {
        "cv": cv_result.data,
        "sections": sections_result.data[0] if sections_result.data else None
    }

@router.post("/{cv_id}/reparse")
async def reparse_cv(cv_id: str, user = Depends(get_current_user)):
    """Manually trigger re-parsing of an existing CV"""
    # Verify CV exists and belongs to user
    cv_result = supabase.table("cvs")\
        .select("*")\
        .eq("id", cv_id)\
        .eq("user_id", user.id)\
        .single()\
        .execute()
    
    if not cv_result.data:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Enqueue parsing job
    print(f"🔄 Manual re-parse requested for CV: {cv_id}")
    job_id = await queue_service.enqueue_cv_parse(cv_id, user.id)
    print(f"✅ Job enqueued with ID: {job_id}")
    
    # Update status to uploaded to trigger re-parsing
    supabase.table("cvs").update({
        "status": "uploaded"
    }).eq("id", cv_id).execute()
    
    return {
        "cv_id": cv_id,
        "job_id": job_id,
        "status": "uploaded",
        "message": "Re-parsing initiated"
    }

@router.post("/{cv_id}/set-primary")
async def set_primary_cv(cv_id: str, user = Depends(get_current_user)):
    """Set a CV as the primary/active CV"""
    # Verify CV exists and belongs to user
    cv_result = supabase.table("cvs")\
        .select("*")\
        .eq("id", cv_id)\
        .eq("user_id", user.id)\
        .single()\
        .execute()
    
    if not cv_result.data:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Set as primary (trigger will unset others automatically)
    supabase.table("cvs").update({
        "is_primary": True
    }).eq("id", cv_id).execute()
    
    return {
        "message": "CV set as primary successfully",
        "cv_id": cv_id
    }

@router.delete("/{cv_id}")
async def delete_cv(cv_id: str, user = Depends(get_current_user)):
    """Delete a CV and its associated data"""
    # Get CV to find file path
    cv_result = supabase.table("cvs")\
        .select("file_path")\
        .eq("id", cv_id)\
        .eq("user_id", user.id)\
        .single()\
        .execute()
    
    if not cv_result.data:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Delete from storage
    await storage_service.delete_cv(cv_result.data["file_path"])
    
    # Delete from database (cascade will handle related records)
    supabase.table("cvs")\
        .delete()\
        .eq("id", cv_id)\
        .eq("user_id", user.id)\
        .execute()
    
    return {"message": "CV deleted successfully"}