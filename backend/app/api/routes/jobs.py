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
    result = supabase.table("jobs").insert({
        "user_id": user.id,
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "url": job.url
    }).execute()
    
    return result.data[0]

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
    Scrape job details from a URL.
    Uses BeautifulSoup + Azure OpenAI for cost-effective extraction.
    """
    try:
        job_data = await job_scraper_service.scrape_job(request.url)
        return job_data
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to scrape job: {str(e)}"
        )