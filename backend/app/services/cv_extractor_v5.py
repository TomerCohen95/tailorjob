"""
CV Extractor v5.0 - Extract structured facts from CV text.
Reuses v4.0 extraction logic (proven to work well).
Part of fully AI-driven matcher v5.0.
"""

from typing import Dict, Any
from openai import AsyncAzureOpenAI
import json


class CVExtractorV5:
    """
    Extract CV facts using GPT-4o-mini.
    Fast, cheap, accurate extraction with zero hallucination.
    """
    
    def __init__(self, client: AsyncAzureOpenAI, deployment: str):
        """
        Initialize CV extractor.
        
        Args:
            client: Azure OpenAI client
            deployment: Deployment name (e.g., "gpt-4o-mini")
        """
        self.client = client
        self.deployment = deployment
        print(f"🔧 Initializing CV Extractor v5.0")
        print(f"   Deployment: {deployment}")
        print(f"✅ CV Extractor v5.0 initialized successfully")
    
    async def extract_facts(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract structured facts from CV text.
        
        Uses GPT-4o-mini with temperature 0.0 for zero hallucination.
        
        Args:
            cv_text: Raw CV text content
            
        Returns:
            Structured CV facts (skills, experience, education, etc.)
        """
        print(f"📄 Extracting facts from CV ({len(cv_text)} chars)")
        
        prompt = self._build_extraction_prompt(cv_text)
        
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # Zero hallucination
            response_format={"type": "json_object"}
        )
        
        facts = json.loads(response.choices[0].message.content)
        
        # Log extraction summary
        skills_count = len(facts.get("skills", {}).get("languages", []))
        jobs_count = len(facts.get("experience", []))
        years = facts.get("total_years_experience", 0)
        
        print(f"✅ Extracted: {skills_count} skills, {jobs_count} jobs, {years} total years")
        
        return facts
    
    def _build_extraction_prompt(self, cv_text: str) -> str:
        """
        Build extraction prompt.
        Reuses proven v4.0 prompt with minor improvements.
        """
        return f"""Extract factual information from this CV. Return ONLY facts present in the text.

CV TEXT:
{cv_text}

Return JSON with this exact structure:
{{
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
- If education is training/bootcamp (not Bachelor's/Master's/PhD), mark degree as "Training" or "Bootcamp Certificate"
- Calculate total_years_experience by summing all experience periods
- List ALL technologies mentioned in experience descriptions (languages, frameworks, tools)
- For soft skills, extract only if explicitly mentioned (e.g., "Leadership", "Mentorship")
"""