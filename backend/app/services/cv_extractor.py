"""
CV Extractor - Wrapper for CV Extractor v5.
Extracts structured facts from CV text using GPT-4o-mini.
"""

from typing import Dict, Any
from openai import AsyncAzureOpenAI
from app.config import settings


class CVExtractor:
    """
    Extract CV facts using GPT-4o-mini.
    Fast, cheap, accurate extraction with zero hallucination.
    """
    
    def __init__(self):
        """Initialize CV extractor with Azure OpenAI client."""
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT_MINI
    
    async def extract_facts(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract structured facts from CV text.
        
        Args:
            cv_text: Raw CV text content
            
        Returns:
            Structured CV facts (skills, experience, education, etc.)
        """
        import json
        
        prompt = self._build_extraction_prompt(cv_text)
        
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        facts = json.loads(response.choices[0].message.content)
        return facts
    
    def _build_extraction_prompt(self, cv_text: str) -> str:
        """Build extraction prompt for CV facts."""
        return f"""Extract factual information from this CV. Return ONLY facts present in the text.

CV TEXT:
{cv_text}

Return JSON with this exact structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "linkedin": "linkedin.com/in/username",
  "summary": "brief professional summary",
  "skills": {{
    "languages": ["Python", "C#", "Rust"],
    "frameworks": ["Flask", "FastAPI"],
    "tools": ["Azure", "Jenkins", "PostgreSQL"],
    "soft_skills": ["Leadership", "Mentorship"]
  }},
  "experience": [
    {{
      "title": "Senior Software Engineer",
      "company": "Microsoft",
      "period": "2021-2025",
      "years": 4,
      "description": ["Led team of 5-6 engineers", "Designed security agent in Rust"],
      "technologies": ["Rust", "C#", "Azure Cloud Services"]
    }}
  ],
  "education": [
    {{
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "institution": "MIT",
      "year": "2015"
    }}
  ],
  "certifications": ["AWS Certified Solutions Architect", "Azure Administrator"],
  "total_years_experience": 10
}}

CRITICAL RULES:
- Extract ONLY information explicitly stated in CV
- Do NOT infer or assume qualifications
- Be precise with years, titles, companies, technologies
- Include contact information (name, email, phone, linkedin) if present
- Calculate total_years_experience by summing all experience periods
"""