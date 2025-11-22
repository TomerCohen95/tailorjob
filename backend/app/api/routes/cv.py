from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.api.deps import get_current_user
from app.services.storage import storage_service
from app.services.queue import queue_service
from app.utils.supabase_client import supabase

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
    
    # Upload to storage
    file_path = await storage_service.upload_cv(
        content,
        file.filename,
        user.id
    )
    
    # Create database record
    result = supabase.table("cvs").insert({
        "user_id": user.id,
        "original_filename": file.filename,
        "file_path": file_path,
        "file_size": file.size,
        "mime_type": file.content_type,
        "status": "uploaded"
    }).execute()
    
    cv_id = result.data[0]["id"]
    
    # Enqueue parsing job
    job_id = await queue_service.enqueue_cv_parse(cv_id, user.id)
    
    return {
        "cv_id": cv_id,
        "job_id": job_id,
        "status": "uploaded",
        "message": "CV uploaded successfully, parsing started"
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