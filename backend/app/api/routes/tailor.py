from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.api.deps import get_current_user
from app.utils.supabase_client import supabase
from app.services.queue import queue_service
from app.utils.usage_limiter import require_feature_dependency

router = APIRouter()

# Dependency function for tailored CV access check
async def check_tailored_cv_access(user = Depends(get_current_user)):
    """Check if user can create tailored CVs"""
    return await require_feature_dependency("tailored_cvs", user)

@router.post("/tailor/{cv_id}/{job_id}")
async def tailor_cv(
    cv_id: str,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _feature_check: bool = Depends(check_tailored_cv_access)
):
    """
    Tailor a CV for a specific job posting
    This queues an AI job to generate a tailored version
    """
    user_id = current_user["id"]
    
    # Verify CV belongs to user
    cv_response = supabase.table("cvs").select("*").eq("id", cv_id).eq("user_id", user_id).execute()
    if not cv_response.data:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Verify job belongs to user
    job_response = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).execute()
    if not job_response.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if tailored version already exists
    existing = supabase.table("tailored_cvs").select("*").eq("cv_id", cv_id).eq("job_id", job_id).execute()
    if existing.data:
        return {
            "message": "Tailored CV already exists",
            "tailored_cv_id": existing.data[0]["id"]
        }
    
    # Create placeholder tailored CV record
    tailored_cv = supabase.table("tailored_cvs").insert({
        "cv_id": cv_id,
        "job_id": job_id,
        "user_id": user_id,
        "status": "queued"
    }).execute()
    
    # Enqueue AI tailoring job
    job_key = await queue_service.enqueue_ai_tailor(cv_id, job_id, user_id)
    
    return {
        "message": "CV tailoring job queued",
        "tailored_cv_id": tailored_cv.data[0]["id"],
        "job_id": job_key
    }


@router.get("/tailor/{cv_id}/{job_id}")
async def get_tailored_cv(
    cv_id: str,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a tailored CV"""
    user_id = current_user["id"]
    
    response = supabase.table("tailored_cvs").select("*").eq(
        "cv_id", cv_id
    ).eq("job_id", job_id).eq("user_id", user_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Tailored CV not found")
    
    return response.data[0]


@router.get("/tailor/{cv_id}/{job_id}/status")
async def get_tailoring_status(
    cv_id: str,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the status of a CV tailoring job"""
    user_id = current_user["id"]
    
    # Get tailored CV record
    response = supabase.table("tailored_cvs").select("*").eq(
        "cv_id", cv_id
    ).eq("job_id", job_id).eq("user_id", user_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Tailored CV not found")
    
    tailored_cv = response.data[0]
    job_key = f"{cv_id}:{job_id}"
    
    # Get job status from queue
    job_status = await queue_service.get_job_status(job_key)
    
    return {
        "tailored_cv_id": tailored_cv["id"],
        "status": tailored_cv["status"],
        "queue_status": job_status["status"],
        "created_at": tailored_cv["created_at"],
        "updated_at": tailored_cv["updated_at"]
    }


@router.post("/chat/{cv_id}/{job_id}")
async def send_chat_message(
    cv_id: str,
    job_id: str,
    message: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send a chat message for CV tailoring guidance
    Placeholder - will integrate with Azure OpenAI
    """
    user_id = current_user["id"]
    
    # Verify tailored CV exists
    tailored_response = supabase.table("tailored_cvs").select("id").eq(
        "cv_id", cv_id
    ).eq("job_id", job_id).eq("user_id", user_id).execute()
    
    if not tailored_response.data:
        raise HTTPException(status_code=404, detail="Tailored CV not found")
    
    tailored_cv_id = tailored_response.data[0]["id"]
    
    # Save user message
    user_msg = supabase.table("chat_messages").insert({
        "tailored_cv_id": tailored_cv_id,
        "role": "user",
        "content": message.get("content", "")
    }).execute()
    
    # TODO: Call Azure OpenAI for AI response
    # For now, return a placeholder response
    ai_response_content = "This is a placeholder response. Azure OpenAI integration coming soon!"
    
    # Save AI response
    ai_msg = supabase.table("chat_messages").insert({
        "tailored_cv_id": tailored_cv_id,
        "role": "assistant",
        "content": ai_response_content
    }).execute()
    
    return {
        "user_message": user_msg.data[0],
        "ai_response": ai_msg.data[0]
    }


@router.get("/chat/{cv_id}/{job_id}/history")
async def get_chat_history(
    cv_id: str,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get chat history for a tailored CV"""
    user_id = current_user["id"]
    
    # Get tailored CV
    tailored_response = supabase.table("tailored_cvs").select("id").eq(
        "cv_id", cv_id
    ).eq("job_id", job_id).eq("user_id", user_id).execute()
    
    if not tailored_response.data:
        raise HTTPException(status_code=404, detail="Tailored CV not found")
    
    tailored_cv_id = tailored_response.data[0]["id"]
    
    # Get chat messages
    messages = supabase.table("chat_messages").select("*").eq(
        "tailored_cv_id", tailored_cv_id
    ).order("created_at").execute()
    
    return {
        "tailored_cv_id": tailored_cv_id,
        "messages": messages.data
    }