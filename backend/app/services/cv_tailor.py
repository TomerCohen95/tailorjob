"""
CV Tailor - AI-powered CV tailoring service.
Takes CV facts and job requirements, returns tailored CV content optimized for the job.
"""

from typing import Dict, Any
from openai import AsyncAzureOpenAI
from app.config import settings
import json


class CVTailor:
    """
    Tailor CV content to match specific job requirements.
    Uses GPT-4 for intelligent content optimization.
    """
    
    def __init__(self):
        """Initialize CV tailor with Azure OpenAI client."""
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        # Use GPT-4 for better reasoning
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT_GPT4
    
    async def tailor_cv(
        self,
        cv_facts: Dict[str, Any],
        job_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tailor CV content to highlight relevant experience for the job.
        
        Args:
            cv_facts: Extracted CV facts (from CVExtractor)
            job_data: Job requirements and description
            analysis: Match analysis with strengths/gaps/recommendations
            
        Returns:
            Tailored CV data optimized for the specific job
        """
        prompt = self._build_tailoring_prompt(cv_facts, job_data, analysis)
        
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Slight creativity for rewriting
            response_format={"type": "json_object"}
        )
        
        tailored_cv = json.loads(response.choices[0].message.content)
        return tailored_cv
    
    def _build_tailoring_prompt(
        self,
        cv_facts: Dict[str, Any],
        job_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Build prompt for CV tailoring."""
        
        job_title = job_data.get("title", "Unknown Position")
        job_desc = job_data.get("description", "")
        requirements = job_data.get("requirements", {})
        
        strengths = analysis.get("explanation", {}).get("strengths", [])
        recommendations = analysis.get("explanation", {}).get("recommendations", [])
        
        return f"""You are an expert CV writer. Tailor this CV to maximize fit for the target job.

TARGET JOB:
Title: {job_title}
Description: {job_desc}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

ORIGINAL CV FACTS:
{json.dumps(cv_facts, indent=2)}

MATCH ANALYSIS INSIGHTS:
Strengths: {json.dumps(strengths, indent=2)}
Recommendations: {json.dumps(recommendations, indent=2)}

YOUR TASK:
Create a tailored version of this CV that highlights relevant experience and skills for this specific job.

TAILORING STRATEGY:
1. **Professional Summary**: Rewrite to emphasize skills/experience most relevant to this job
2. **Experience Descriptions**: 
   - Highlight achievements that match job requirements
   - Emphasize transferable skills and relevant technologies
   - Use metrics and quantifiable results where possible (team size, performance gains, scale)
   - Reorder bullet points to put most relevant items first
3. **Skills Section**: 
   - Prioritize skills mentioned in job requirements
   - Group related skills together
   - Keep all existing skills but reorder by relevance
4. **Education & Certifications**: Keep as-is unless directly relevant to job

CRITICAL RULES:
- Do NOT add skills or experience not in the original CV (no fabrication!)
- Do NOT remove any experience or education entries
- Keep all factual information accurate (dates, companies, titles)
- Improve presentation and emphasis, not content invention
- Return complete CV data in the same structure as input

Return JSON with this structure:
{{
  "name": "Full Name",
  "email": "email@example.com", 
  "phone": "+1234567890",
  "linkedin": "linkedin.com/in/username",
  "summary": "Tailored professional summary emphasizing relevant experience",
  "skills": {{
    "languages": ["Most relevant first"],
    "frameworks": ["Prioritized by job relevance"],
    "tools": ["Reordered by importance"],
    "soft_skills": ["Relevant soft skills"]
  }},
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "period": "2021-2025",
      "years": 4,
      "description": ["Rewritten to highlight relevant achievements", "With metrics and impact"],
      "technologies": ["Technologies used"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree",
      "field": "Field",
      "institution": "University",
      "year": "2015"
    }}
  ],
  "certifications": ["Keep all certifications"],
  "total_years_experience": 10
}}
"""