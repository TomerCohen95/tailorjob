from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.utils.supabase_client import supabase
from app.services.job_scraper import job_scraper_service

router = APIRouter()

# Request/Response models
class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    url: str | None = None
    job_id: str | None = None

class JobScrapeRequest(BaseModel):
    url: str

class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str | None = None
    url: str | None = None
    status: str | None = None

@router.post("/")
async def create_job(job: JobCreate, user = Depends(get_current_user)):
    """Create a new job description"""
    try:
        result = supabase.table("jobs").insert({
            "user_id": user.id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "url": job.url,
            "job_id": job.job_id
        }).execute()
        
        return result.data[0]
    except Exception as e:
        error_msg = str(e).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg:
            raise HTTPException(
                status_code=409,
                detail="You've already added this job. Check your jobs list."
            )
        raise

@router.get("/")
async def list_jobs(user = Depends(get_current_user)):
    """List all jobs for the current user"""
    result = supabase.table("jobs")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("created_at", desc=True)\
        .execute()
    
    return result.data

@router.get("/{job_id}")
async def get_job(job_id: str, user = Depends(get_current_user)):
    """Get a specific job"""
    result = supabase.table("jobs")\
        .select("*")\
        .eq("id", job_id)\
        .eq("user_id", user.id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return result.data

@router.put("/{job_id}")
async def update_job(
    job_id: str,
    job: JobUpdate,
    user = Depends(get_current_user)
):
    """Update a job"""
    # Build update dict (exclude None values)
    update_data = {k: v for k, v in job.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = supabase.table("jobs")\
        .update(update_data)\
        .eq("id", job_id)\
        .eq("user_id", user.id)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return result.data[0]

@router.delete("/{job_id}")
async def delete_job(job_id: str, user = Depends(get_current_user)):
    """Delete a job"""
    result = supabase.table("jobs")\
        .delete()\
        .eq("id", job_id)\
        .eq("user_id", user.id)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": "Job deleted successfully"}

@router.post("/scrape")
async def scrape_job(
    request: JobScrapeRequest,
    user = Depends(get_current_user)
):
    """
    Scrape job details from a URL and save to database.
    Uses BeautifulSoup + Azure OpenAI for cost-effective extraction.
    """
    try:
        import json
        job_data = await job_scraper_service.scrape_job(request.url)
        
        # Store description as JSON string if it's structured, otherwise as plain text
        description = job_data.get('description', '')
        if isinstance(description, dict):
            description_json = json.dumps(description)
        else:
            description_json = description
        
        # Save to database with job_id for deduplication
        try:
            result = supabase.table("jobs").insert({
                "user_id": user.id,
                "title": job_data.get('title', ''),
                "company": job_data.get('company', ''),
                "description": description_json,
                "url": request.url,
                "job_id": job_data.get('job_id')
            }).execute()
            
            # Return both scraped data and saved job
            return {
                **job_data,
                "id": result.data[0]["id"],
                "saved": True,
                "duplicate": False
            }
        except Exception as db_error:
            error_msg = str(db_error).lower()
            if 'unique' in error_msg or 'duplicate' in error_msg:
                # Find the existing job and return its ID
                existing_job = None
                
                # Try to find by URL first
                if request.url:
                    result = supabase.table("jobs")\
                        .select("id")\
                        .eq("user_id", user.id)\
                        .eq("url", request.url)\
                        .limit(1)\
                        .execute()
                    if result.data:
                        existing_job = result.data[0]
                
                # If not found by URL, try by job_id
                if not existing_job and job_data.get('job_id'):
                    result = supabase.table("jobs")\
                        .select("id")\
                        .eq("user_id", user.id)\
                        .eq("job_id", job_data.get('job_id'))\
                        .limit(1)\
                        .execute()
                    if result.data:
                        existing_job = result.data[0]
                
                # If still not found, try by company + title
                if not existing_job:
                    result = supabase.table("jobs")\
                        .select("id")\
                        .eq("user_id", user.id)\
                        .ilike("company", job_data.get('company', ''))\
                        .ilike("title", job_data.get('title', ''))\
                        .limit(1)\
                        .execute()
                    if result.data:
                        existing_job = result.data[0]
                
                if existing_job:
                    # Return the existing job ID so frontend can redirect
                    raise HTTPException(
                        status_code=409,
                        detail=f"DUPLICATE:{existing_job['id']}"
                    )
                else:
                    # Couldn't find existing job, just return generic message
                    raise HTTPException(
                        status_code=409,
                        detail="You've already added this job. Check your jobs list."
                    )
            raise
            
    except HTTPException:
        # Re-raise HTTP exceptions (including our duplicate error)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to scrape job: {str(e)}"
        )