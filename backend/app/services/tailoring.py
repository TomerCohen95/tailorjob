import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
import io
import hashlib
import json
from enum import Enum
import redis

from app.services.container import container
from app.services.cv_extractor import CVExtractor
from app.services.cv_tailor import CVTailor
from app.services.pdf_generator import generate_pdf_from_data
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class TemplateEnum(str, Enum):
    """Enumeration for the available PDF templates."""
    modern = "cv_template_modern.html"
    classic = "cv_template_classic.html"

class TailorRequest(BaseModel):
    """
    Defines the request body for the /tailor-cv endpoint.
    """
    cv_text: str = Field(..., description="The full text content of the original CV.")
    analysis: Dict[str, Any] = Field(..., description="The full analysis object from the CV Matcher, including job_data and recommendations.")
    template_name: TemplateEnum = Field(default=TemplateEnum.modern, description="The name of the PDF template to use.")


@router.post("/tailor-cv",
             response_class=StreamingResponse,
             summary="Tailor a CV and generate a PDF",
             description="Receives a CV and a match analysis, then returns a tailored version of the CV as a PDF document.",
             responses={
                 200: {
                     "content": {"application/pdf": {}},
                     "description": "A PDF file of the tailored CV.",
                 },
                 400: {"description": "Bad request, e.g., missing 'job_data' in the analysis object."},
                 500: {"description": "Internal server error during tailoring or PDF generation."}
             })
async def tailor_cv_and_generate_pdf(
    payload: TailorRequest = Body(...),
    cv_extractor: CVExtractor = Depends(container.cv_extractor),
    cv_tailor: CVTailor = Depends(container.cv_tailor),
    redis_client: redis.Redis = Depends(container.redis_client)
):
    """
    Orchestrates the full CV tailoring and PDF generation workflow.
    """
    try:
        # Step 1: Extract facts. This is fast and needed for both cache key and merging.
        logger.info("Step 1/6: Extracting facts from original CV.")
        original_cv_facts = await cv_extractor.extract_facts(payload.cv_text)

        # Step 2: Generate a stable cache key from the inputs
        facts_str = json.dumps(original_cv_facts, sort_keys=True)
        analysis_str = json.dumps(payload.analysis, sort_keys=True)
        cache_key_str = f"{facts_str}:{analysis_str}"
        cache_key = f"tailor_cache:{hashlib.sha256(cache_key_str.encode('utf-8')).hexdigest()}"

        # Step 3: Check cache
        logger.info("Step 2/6: Checking cache for tailored CV data.")
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT for tailoring request. Key: {cache_key}")
            tailored_cv_data = json.loads(cached_result)
        else:
            logger.info(f"Cache MISS for tailoring request. Key: {cache_key}")
            if "job_data" not in payload.analysis:
                raise HTTPException(status_code=400, detail="Analysis object must contain 'job_data'.")

            # Step 4: Tailor the CV using the AI service (expensive call)
            logger.info("Step 3/6: Tailoring CV content with AI.")
            tailored_cv_data = await cv_tailor.tailor_cv(
                cv_facts=original_cv_facts,
                job_data=payload.analysis["job_data"],
                analysis=payload.analysis
            )
            
            # Store the result in cache for 1 hour (3600 seconds)
            logger.info(f"Step 4/6: Storing result in cache. Key: {cache_key}")
            redis_client.set(cache_key, json.dumps(tailored_cv_data), ex=3600)

        # Step 5: Merge essential personal details from original CV into the tailored data.
        # The LLM focuses on content and may omit these, so we ensure they are present.
        for key in ['name', 'email', 'phone', 'linkedin']:
            if key in original_cv_facts and original_cv_facts.get(key):
                tailored_cv_data.setdefault(key, original_cv_facts[key])

        # Step 6: Generate the PDF from the tailored data
        logger.info("Step 5/6: Generating PDF from tailored data.")
        pdf_bytes = generate_pdf_from_data(
            cv_data=tailored_cv_data,
            template_name=payload.template_name.value
        )

        # Step 7: Stream the PDF back to the client
        logger.info("Step 6/6: Streaming PDF response.")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Tailored_CV.pdf"}
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred in the tailoring endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")