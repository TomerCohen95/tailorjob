from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.services.cv_matcher import cv_matcher_service
from app.services.cv_matcher_v3 import cv_matcher_service_v3
from app.config import settings
from app.utils.supabase_client import get_supabase
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/matching", tags=["matching"])


class MatchRequest(BaseModel):
    cv_id: str
    job_id: str


class MatchResponse(BaseModel):
    overall_score: int
    skills_score: Optional[int] = None
    experience_score: Optional[int] = None
    qualifications_score: Optional[int] = None
    analysis: Dict[str, Any]
    cached: bool
    created_at: str


@router.post("/analyze", response_model=MatchResponse)
async def analyze_match(
    request: MatchRequest,
    user = Depends(get_current_user)
):
    """
    Analyze CV-to-job match. Returns cached result if available and fresh (< 7 days).
    
    This endpoint:
    1. Checks for cached match score
    2. If not found or expired, performs AI analysis
    3. Stores result with 7-day expiry
    4. Returns detailed match breakdown
    """
    supabase = get_supabase()
    
    # Check for cached match (not expired)
    try:
        cached = supabase.table('cv_job_matches') \
            .select('*') \
            .eq('cv_id', request.cv_id) \
            .eq('job_id', request.job_id) \
            .eq('user_id', user.id) \
            .gt('expires_at', datetime.utcnow().isoformat()) \
            .execute()
        
        if cached.data and len(cached.data) > 0:
            match = cached.data[0]
            print(f"✅ Returning cached match score: {match['overall_score']}%")
            return MatchResponse(
                overall_score=match['overall_score'],
                skills_score=match.get('skills_score'),
                experience_score=match.get('experience_score'),
                qualifications_score=match.get('qualifications_score'),
                analysis=match['analysis'],
                cached=True,
                created_at=match['created_at']
            )
    except Exception as e:
        print(f"⚠️ Error checking cache: {e}")
        # Continue to fresh analysis if cache check fails
    
    # Fetch CV data
    try:
        cv_response = supabase.table('cv_sections') \
            .select('*') \
            .eq('cv_id', request.cv_id) \
            .execute()
        
        if not cv_response.data or len(cv_response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="CV not found or not parsed yet. Please upload and parse a CV first."
            )
        
        cv_data = cv_response.data[0]
        
        # Parse JSON strings stored in database (AGENTS.md: CV sections stored as JSON.dumps() strings)
        import json
        for field in ['skills', 'experience', 'education', 'certifications']:
            if cv_data.get(field) and isinstance(cv_data[field], str):
                try:
                    cv_data[field] = json.loads(cv_data[field])
                except json.JSONDecodeError:
                    cv_data[field] = []
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching CV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch CV data: {str(e)}")
    
    # Fetch job data
    try:
        job_response = supabase.table('jobs') \
            .select('*') \
            .eq('id', request.job_id) \
            .eq('user_id', user.id) \
            .execute()
        
        if not job_response.data or len(job_response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Job not found or you don't have permission to access it."
            )
        
        job_data = job_response.data[0]
        
        # Parse description if it's stored as JSON string
        if job_data.get('description') and isinstance(job_data['description'], str):
            try:
                # Try to parse as JSON (structured description)
                job_data['description'] = json.loads(job_data['description'])
                
                # Extract requirements_matrix if embedded in description
                if isinstance(job_data['description'], dict) and 'requirements_matrix' in job_data['description']:
                    job_data['requirements_matrix'] = job_data['description']['requirements_matrix']
                    
            except json.JSONDecodeError:
                # Keep as plain text if not valid JSON
                pass
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job data: {str(e)}")
    
    # Perform AI analysis (use v3.0 if enabled)
    try:
        if settings.USE_MATCHER_V3:
            print(f"🆕 Using Matcher v3.0 (AI-first)")
            analysis = await cv_matcher_service_v3.analyze_match(cv_data, job_data)
        else:
            print(f"📊 Using Matcher v2.x (rule-based)")
            analysis = await cv_matcher_service.analyze_match(cv_data, job_data)
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Store result with 7-day expiry
    try:
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        match_record = {
            'cv_id': request.cv_id,
            'job_id': request.job_id,
            'user_id': user.id,
            'overall_score': analysis['overall_score'],
            'skills_score': analysis.get('skills_score'),
            'experience_score': analysis.get('experience_score'),
            'qualifications_score': analysis.get('qualifications_score'),
            'analysis': analysis,
            'expires_at': expires_at.isoformat()
        }
        
        # Upsert (insert or update if exists)
        supabase.table('cv_job_matches').upsert(match_record).execute()
        print(f"💾 Match score stored successfully")
    except Exception as e:
        print(f"⚠️ Failed to store match score: {e}")
        # Continue even if storage fails - return the analysis
    
    return MatchResponse(
        overall_score=analysis['overall_score'],
        skills_score=analysis.get('skills_score'),
        experience_score=analysis.get('experience_score'),
        qualifications_score=analysis.get('qualifications_score'),
        analysis=analysis,
        cached=False,
        created_at=datetime.utcnow().isoformat()
    )


@router.get("/score/{cv_id}/{job_id}")
async def get_match_score(
    cv_id: str,
    job_id: str,
    user = Depends(get_current_user)
):
    """
    Get cached match score if available (for displaying badges on job listings).
    Returns null if not analyzed yet or expired.
    
    Use this for quick lookups when displaying job lists with match indicators.
    """
    supabase = get_supabase()
    
    try:
        result = supabase.table('cv_job_matches') \
            .select('*') \
            .eq('cv_id', cv_id) \
            .eq('job_id', job_id) \
            .eq('user_id', user.id) \
            .gt('expires_at', datetime.utcnow().isoformat()) \
            .execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        match = result.data[0]
        return MatchResponse(
            overall_score=match['overall_score'],
            skills_score=match.get('skills_score'),
            experience_score=match.get('experience_score'),
            qualifications_score=match.get('qualifications_score'),
            analysis=match['analysis'],
            cached=True,
            created_at=match['created_at']
        )
    except Exception as e:
        print(f"❌ Error fetching match score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch match score: {str(e)}")


@router.delete("/score/{cv_id}/{job_id}")
async def delete_match_score(
    cv_id: str,
    job_id: str,
    user = Depends(get_current_user)
):
    """
    Delete a cached match score (forces re-analysis on next request).
    Useful when CV or job has been significantly updated.
    """
    supabase = get_supabase()
    
    try:
        result = supabase.table('cv_job_matches') \
            .delete() \
            .eq('cv_id', cv_id) \
            .eq('job_id', job_id) \
            .eq('user_id', user.id) \
            .execute()
        
        return {"message": "Match score deleted successfully", "deleted": len(result.data) > 0}
    except Exception as e:
        print(f"❌ Error deleting match score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete match score: {str(e)}")