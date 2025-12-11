from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api.deps import get_current_user
from app.services.storage import storage_service
from app.services.queue import queue_service
from app.services.cv_parser import cv_parser_service
from app.utils.supabase_client import supabase
from app.utils.usage_limiter import require_feature_dependency
from app.middleware.metrics_helpers import track_feature_usage, track_cv_parse, track_cv_parse_error
import hashlib
import json
import time
import logging
from functools import partial

logger = logging.getLogger(__name__)

router = APIRouter()

# Create a dependency function for cv_uploads
async def check_cv_upload_access(user = Depends(get_current_user)):
    return await require_feature_dependency("cv_uploads", user)

@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    _feature_check: bool = Depends(check_cv_upload_access)
):
    """
    Upload a CV file.
    
    - Validates file type (PDF/DOCX)
    - Validates file size (max 10MB)
    - Uploads to Supabase Storage
    - Creates database record
    - Enqueues parsing job
    """
    logger.info(f"📤 CV upload started: user={user.id}, filename={file.filename}, size={file.size}b")
    
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx')):
        logger.warning(f"❌ Invalid file type rejected: user={user.id}, filename={file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )
    
    # Validate file size
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB
        logger.warning(f"❌ File too large rejected: user={user.id}, size={file.size}b")
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
        logger.info(f"📋 Duplicate CV detected: user={user.id}, cv_id={existing['id']}, status={existing_status}, hash={file_hash[:12]}...")
        
        # If the existing CV hasn't been parsed yet, enqueue a parsing job
        if existing_status in ["uploaded", "error"]:
            logger.info(f"🔄 Re-enqueueing parse job: cv_id={existing['id']}, user={user.id}")
            try:
                job_id = await queue_service.enqueue_cv_parse(existing["id"], user.id)
                logger.info(f"✅ Parse job enqueued: cv_id={existing['id']}, job_id={job_id}")
                message = "CV already exists, re-parsing initiated"
            except Exception as e:
                logger.warning(f"⚠️  Queue unavailable (non-fatal): cv_id={existing['id']}, error={str(e)}")
                job_id = None
                message = "CV already exists. Re-parsing will start when worker reconnects."
            
            return {
                "cv_id": existing["id"],
                "job_id": job_id,
                "status": "uploaded",
                "message": message
            }
        
        # CV already parsed successfully - offer to re-parse
        logger.info(f"ℹ️  CV already parsed successfully: cv_id={existing['id']}, user={user.id}")
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
    logger.info(f"📁 Uploading CV to storage: user={user.id}, filename={file.filename}, hash={file_hash[:12]}...")
    file_path = await storage_service.upload_cv(
        content,
        file.filename,
        user.id
    )
    logger.info(f"✅ CV uploaded to storage: user={user.id}, path={file_path}")
    
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
    logger.info(f"💾 CV record created: cv_id={cv_id}, user={user.id}, filename={file.filename}")
    
    # Track feature usage
    track_feature_usage("cv_upload", user)
    
    # Parse CV immediately (synchronous) for better UX
    logger.info(f"📄 Starting CV parsing: cv_id={cv_id}, user={user.id}")
    start_time = time.time()
    try:
        # Update status to parsing
        supabase.table("cvs").update({
            "status": "parsing"
        }).eq("id", cv_id).execute()
        
        # Parse the CV
        parsed_data = await cv_parser_service.parse_cv_file(content, file.filename)
        
        # Track parsing duration
        duration = time.time() - start_time
        track_cv_parse(duration)
        
        # Save parsed sections to database
        sections_data = {
            "cv_id": cv_id,
            "summary": parsed_data.get("summary", ""),
            "skills": json.dumps(parsed_data.get("skills", [])),
            "experience": json.dumps(parsed_data.get("experience", [])),
            "education": json.dumps(parsed_data.get("education", [])),
            "certifications": json.dumps(parsed_data.get("certifications", []))
        }
        
        supabase.table("cv_sections").insert(sections_data).execute()
        
        # Count sections
        section_counts = {
            'skills': len(parsed_data.get("skills", [])),
            'experience': len(parsed_data.get("experience", [])),
            'education': len(parsed_data.get("education", [])),
            'certifications': len(parsed_data.get("certifications", []))
        }
        
        logger.info(f"📝 CV sections extracted: cv_id={cv_id}, sections={section_counts}, duration={duration:.2f}s")
        
        # Update CV status to parsed
        supabase.table("cvs").update({
            "status": "parsed"
        }).eq("id", cv_id).execute()
        
        logger.info(f"✅ CV parsed successfully: cv_id={cv_id}, user={user.id}, duration={duration:.2f}s")
        
        return {
            "cv_id": cv_id,
            "status": "parsed",
            "message": "CV uploaded and parsed successfully"
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ CV parsing failed: cv_id={cv_id}, user={user.id}, error={str(e)}, duration={duration:.2f}s", exc_info=True)
        
        # Track parsing error
        track_cv_parse_error(type(e).__name__)
        
        # Update CV status to error
        supabase.table("cvs").update({
            "status": "error",
            "error_message": str(e)
        }).eq("id", cv_id).execute()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse CV: {str(e)}"
        )

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
    try:
        await storage_service.delete_cv(cv_result.data["file_path"])
    except Exception as e:
        print(f"⚠️  Failed to delete file from storage: {str(e)}")
        # Continue to delete from DB even if storage delete fails
    
    # Delete from database (cascade will handle related records)
    try:
        supabase.table("cvs")\
            .delete()\
            .eq("id", cv_id)\
            .eq("user_id", user.id)\
            .execute()
    except Exception as e:
        # Ignore postgrest response parsing errors, deletion was successful
        print(f"⚠️  CV deleted but response parsing failed: {str(e)}")
    
    return {"message": "CV deleted successfully"}