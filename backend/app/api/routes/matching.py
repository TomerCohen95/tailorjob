from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.services.cv_matcher_v5 import CVMatcherV5
from app.services.cv_extractor_v5 import CVExtractorV5
from app.config import settings
from app.utils.supabase_client import get_supabase
from app.utils.usage_limiter import require_feature_dependency
from app.middleware.metrics_helpers import track_feature_usage, track_ai_match
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from openai import AsyncAzureOpenAI
import json
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["matching"])

# Initialize v5.0 services (required when enabled)
cv_matcher_v5 = None
if settings.USE_MATCHER_V5:
    # Validate required config upfront
    if not settings.AZURE_OPENAI_ENDPOINT:
        logger.error("❌ USE_MATCHER_V5=true but AZURE_OPENAI_ENDPOINT is not configured")
        raise ValueError("AZURE_OPENAI_ENDPOINT required when USE_MATCHER_V5=true")
    if not settings.AZURE_OPENAI_KEY:
        logger.error("❌ USE_MATCHER_V5=true but AZURE_OPENAI_KEY is not configured")
        raise ValueError("AZURE_OPENAI_KEY required when USE_MATCHER_V5=true")
    
    try:
        logger.info(f"🔧 Initializing Matcher v5.1: endpoint={settings.AZURE_OPENAI_ENDPOINT}, mini={settings.AZURE_OPENAI_DEPLOYMENT_MINI}, gpt4={settings.AZURE_OPENAI_DEPLOYMENT_GPT4}")
        
        # Create Azure OpenAI clients
        mini_client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        gpt4_client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        # Create extractor and matcher
        extractor_v5 = CVExtractorV5(
            client=mini_client,
            deployment=settings.AZURE_OPENAI_DEPLOYMENT_MINI
        )
        
        cv_matcher_v5 = CVMatcherV5(
            extractor=extractor_v5,
            gpt4_client=gpt4_client,
            gpt4_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4
        )
        logger.info("✅ Matcher v5.1 initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize v5.0 matcher: {e}", exc_info=True)
        raise RuntimeError(f"Matcher v5 initialization failed: {e}") from e
else:
    logger.info("ℹ️  Matcher v5 disabled (USE_MATCHER_V5=false)")


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


# Create dependency function for job matches
async def check_job_match_access(user = Depends(get_current_user)):
    return await require_feature_dependency("job_matches", user)

@router.post("/analyze", response_model=MatchResponse)
async def analyze_match(
    request: MatchRequest,
    user = Depends(get_current_user),
    _feature_check: bool = Depends(check_job_match_access)
):
    """
    Analyze CV-to-job match. Returns cached result if available and fresh (< 7 days).
    
    This endpoint:
    1. Checks for cached match score
    2. If not found or expired, performs AI analysis
    3. Stores result with 7-day expiry
    4. Returns detailed match breakdown
    """
    logger.info(f"🔍 Match analysis requested: cv_id={request.cv_id}, job_id={request.job_id}, user={user.id}")
    
    # Track feature usage
    track_feature_usage("job_match", user)
    
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
            logger.info(f"💾 Returning cached match: cv_id={request.cv_id}, job_id={request.job_id}, score={match['overall_score']}%, age={(datetime.utcnow() - datetime.fromisoformat(match['created_at'])).days}d")
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
        logger.warning(f"⚠️  Cache check failed (non-fatal): cv_id={request.cv_id}, job_id={request.job_id}, error={str(e)}")
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
        logger.error(f"❌ Failed to fetch CV: cv_id={request.cv_id}, user={user.id}, error={str(e)}")
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
        logger.error(f"❌ Failed to fetch job: job_id={request.job_id}, user={user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job data: {str(e)}")
    
    # Perform AI analysis (route to appropriate matcher version)
    logger.info(f"🤖 Starting AI match analysis: cv_id={request.cv_id}, job_id={request.job_id}")
    
    # Default to v3 if no version specified
    matcher_version = "v3.0"
    start_time = time.time()
    tokens_used = 0
    estimated_cost = 0.0
    
    try:
        # v5 is now the only supported matcher
        if not cv_matcher_v5:
            logger.error(f"❌ Matcher v5 not available: USE_MATCHER_V5={settings.USE_MATCHER_V5}")
            raise HTTPException(
                status_code=503,
                detail="CV matching service not available. Please contact support."
            )
        
        logger.info(f"🚀 Using Matcher v5.1: cv_id={request.cv_id}, job_id={request.job_id}")
        matcher_version = "v5.1"
        
        # Build CV text from sections
        cv_text = f"""
SUMMARY:
{cv_data.get('summary', 'Not provided')}

SKILLS:
{cv_data.get('skills', 'Not provided')}

EXPERIENCE:
{cv_data.get('experience', 'Not provided')}

EDUCATION:
{cv_data.get('education', 'Not provided')}

CERTIFICATIONS:
{cv_data.get('certifications', 'Not provided')}
"""
        analysis = await cv_matcher_v5.analyze_match(cv_text, job_data)
        
        # Extract token usage if available in response
        if 'token_usage' in analysis:
            tokens_used = analysis['token_usage'].get('total_tokens', 0)
            estimated_cost = analysis.get('estimated_cost', 0.0)
        
        # Track AI matching metrics
        duration = time.time() - start_time
        track_ai_match(duration, matcher_version, tokens_used, estimated_cost)
        
        logger.info(f"✅ Match analysis complete: cv_id={request.cv_id}, job_id={request.job_id}, score={analysis['overall_score']}%, version={matcher_version}, tokens={tokens_used}, cost=${estimated_cost:.4f}, duration={duration:.2f}s")
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ AI match analysis failed: cv_id={request.cv_id}, job_id={request.job_id}, version={matcher_version}, duration={duration:.2f}s, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    # Add matcher version to analysis
    analysis["matcher_version"] = matcher_version
    
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
        logger.info(f"💾 Match score cached: cv_id={request.cv_id}, job_id={request.job_id}, score={analysis['overall_score']}%, expires_in=7d")
    except Exception as e:
        logger.warning(f"⚠️  Failed to cache match score (non-fatal): cv_id={request.cv_id}, job_id={request.job_id}, error={str(e)}")
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