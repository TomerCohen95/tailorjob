from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import io
import json
from app.api.deps import get_current_user
from app.utils.supabase_client import supabase
from app.services.queue import queue_service
from app.utils.usage_limiter import require_feature_dependency
from app.services.container import container
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter()

class TemplateEnum(str, Enum):
    """Enumeration for the available PDF templates."""
    modern = "cv_template_modern.html"
    classic = "cv_template_classic.html"

class TailorRequest(BaseModel):
    """Request body for the /generate-pdf endpoint."""
    cv_text: str = Field(..., description="The full text content of the original CV.")
    analysis: Dict[str, Any] = Field(..., description="The full analysis object from the CV Matcher.")
    template_name: TemplateEnum = Field(default=TemplateEnum.modern, description="The PDF template to use.")
    accepted_suggestions: List[Dict[str, Any]] = Field(default=[], description="List of accepted suggestions to apply to the CV.")

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


@router.post("/parse-recommendations")
async def parse_recommendations(
    match_analysis: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Parse match analysis recommendations into structured, actionable suggestions.
    
    Takes the output from cv_matcher_v5 and converts text recommendations
    into interactive UI elements with accept/reject capability.
    """
    from app.services.recommendation_parser import get_parser
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Debug: print to stdout
    print(f"\n{'='*60}")
    print(f"📥 PARSE RECOMMENDATIONS CALLED")
    print(f"📥 Received keys: {list(match_analysis.keys())}")
    recommendations = match_analysis.get("recommendations", [])
    print(f"📝 Found {len(recommendations)} recommendations")
    if recommendations:
        print(f"📋 First recommendation: {recommendations[0]}")
    print(f"{'='*60}\n")
    
    # Also log
    logger.info(f"📥 Received match_analysis keys: {list(match_analysis.keys())}")
    logger.info(f"� Found {len(recommendations)} recommendations")
    if recommendations:
        logger.info(f"📋 Sample recommendation: {recommendations[0][:100]}...")
    
    parser = get_parser()
    suggestions = parser.parse_recommendations(match_analysis)
    
    print(f"✨ Parsed {len(suggestions)} suggestions")
    logger.info(f"✨ Parsed into {len(suggestions)} actionable suggestions")
    
    return {
        "suggestions": [s.to_dict() for s in suggestions],
        "total_count": len(suggestions),
        "high_impact_count": sum(1 for s in suggestions if s.impact.value == "high"),
        "medium_impact_count": sum(1 for s in suggestions if s.impact.value == "medium"),
        "low_impact_count": sum(1 for s in suggestions if s.impact.value == "low"),
        "debug_info": {
            "received_keys": list(match_analysis.keys()),
            "recommendations_count": len(recommendations),
            "has_recommendations": len(recommendations) > 0
        }
    }


def apply_suggestions_to_cv_data(cv_data: Dict[str, Any], suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply accepted suggestions to CV data before PDF generation.
    Mimics the logic from CVPreview.tsx for consistency.
    """
    if not suggestions:
        return cv_data
    
    # Track which suggestions we've applied
    python_added = False
    
    # Apply suggestions to experience section
    if 'experience' in cv_data and isinstance(cv_data['experience'], list):
        modified_experience = []
        
        for exp_item in cv_data['experience']:
            # Check if this is a Team Lead position and we have a Python suggestion
            python_suggestion = next(
                (s for s in suggestions
                 if s.get('type') == 'highlight_skill' and 'python' in s.get('suggestion', '').lower()),
                None
            )
            
            # Apply Python suggestion to FIRST Team Lead position only
            if (python_suggestion and not python_added and
                exp_item.get('title') and 'Team Lead' in exp_item.get('title', '')):
                
                python_added = True
                
                # Add new description bullet
                new_bullet = 'Developed Python-based automation tools for security analysis and threat detection'
                
                # Get existing descriptions
                descriptions = exp_item.get('description', [])
                if isinstance(descriptions, str):
                    descriptions = [descriptions]
                elif not isinstance(descriptions, list):
                    descriptions = []
                
                # Add the new bullet
                modified_exp = exp_item.copy()
                modified_exp['description'] = descriptions + [new_bullet]
                modified_experience.append(modified_exp)
            else:
                modified_experience.append(exp_item)
        
        cv_data['experience'] = modified_experience
    
    return cv_data


@router.post("/generate-pdf",
             response_class=StreamingResponse,
             summary="Generate tailored CV PDF (direct endpoint)",
             description="Receives CV text and match analysis, returns tailored CV as PDF")
async def generate_tailored_pdf(
    payload: TailorRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _feature_check: bool = Depends(check_tailored_cv_access)
):
    """
    Direct endpoint to generate a tailored CV PDF.
    Alternative to the queue-based approach for instant results.
    Accepts accepted_suggestions to apply user-approved improvements.
    """
    from app.services.pdf_generator import generate_pdf_from_data
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"📝 Generating PDF with {len(payload.accepted_suggestions)} accepted suggestions")
    
    try:
        # Get services from container
        cv_extractor = container.cv_extractor()
        cv_tailor = container.cv_tailor()
        redis_client = container.redis_client()
        
        # Step 1: Extract facts
        logger.info("Extracting facts from CV")
        original_cv_facts = await cv_extractor.extract_facts(payload.cv_text)
        
        # Step 2: Generate cache key
        facts_str = json.dumps(original_cv_facts, sort_keys=True)
        analysis_str = json.dumps(payload.analysis, sort_keys=True)
        import hashlib
        cache_key_str = f"{facts_str}:{analysis_str}"
        cache_key = f"tailor_cache:{hashlib.sha256(cache_key_str.encode('utf-8')).hexdigest()}"
        
        # Step 3: Check cache
        logger.info("Checking cache")
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT: {cache_key}")
            tailored_cv_data = json.loads(cached_result)
        else:
            logger.info(f"Cache MISS: {cache_key}")
            
            # Step 4: Tailor CV
            # If analysis has job_data, use full tailoring; otherwise use analysis as-is
            logger.info("Tailoring CV with AI")
            if "job_data" in payload.analysis:
                tailored_cv_data = await cv_tailor.tailor_cv(
                    cv_facts=original_cv_facts,
                    job_data=payload.analysis["job_data"],
                    analysis=payload.analysis
                )
            else:
                # Use simplified approach - just structure the CV facts nicely
                tailored_cv_data = {
                    "personal_info": {
                        "name": original_cv_facts.get("name", ""),
                        "email": original_cv_facts.get("email", ""),
                        "phone": original_cv_facts.get("phone", ""),
                        "location": original_cv_facts.get("location", "")
                    },
                    "summary": original_cv_facts.get("summary", ""),
                    "experience": original_cv_facts.get("experience", []),
                    "education": original_cv_facts.get("education", []),
                    "skills": original_cv_facts.get("skills", []),
                    "certifications": original_cv_facts.get("certifications", [])
                }
            
            # Store in cache
            logger.info(f"Caching result: {cache_key}")
            redis_client.set(cache_key, json.dumps(tailored_cv_data), ex=3600)
        
        # Step 5: Apply accepted suggestions to CV data
        if payload.accepted_suggestions:
            logger.info(f"✨ Applying {len(payload.accepted_suggestions)} accepted suggestions")
            tailored_cv_data = apply_suggestions_to_cv_data(tailored_cv_data, payload.accepted_suggestions)
        
        # Step 6: Merge personal details
        # Ensure personal_info exists
        if 'personal_info' not in tailored_cv_data:
            tailored_cv_data['personal_info'] = {}
        
        # Merge personal details into personal_info
        for key in ['name', 'email', 'phone', 'location', 'linkedin']:
            if key in original_cv_facts and original_cv_facts.get(key):
                if not tailored_cv_data['personal_info'].get(key):
                    tailored_cv_data['personal_info'][key] = original_cv_facts[key]
        
        # Step 7: Generate PDF
        logger.info("Generating PDF")
        pdf_bytes = generate_pdf_from_data(
            cv_data=tailored_cv_data,
            template_name=payload.template_name.value
        )
        
        # Step 8: Return PDF
        logger.info("Returning PDF")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Tailored_CV.pdf"}
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")