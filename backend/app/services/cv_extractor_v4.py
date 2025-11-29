from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any


class CVExtractorV4:
    """
    Extract structured facts from CV with zero hallucination.
    v4.0: AI only extracts what exists, never infers or invents.
    """
    
    def __init__(self):
        self.client = None
        print(f"🔧 Initializing CV Extractor v4.0")
        print(f"   Endpoint: {settings.AZURE_OPENAI_ENDPOINT or '(not set)'}")
        print(f"   API Key: {'✓ Set' if settings.AZURE_OPENAI_KEY else '✗ Not set'}")
        print(f"   Deployment: {settings.AZURE_OPENAI_DEPLOYMENT or '(not set)'}")

        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
            try:
                self.client = AsyncAzureOpenAI(
                    api_key=settings.AZURE_OPENAI_KEY,
                    api_version="2024-02-15-preview",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
                print(f"✅ CV Extractor v4.0 initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize CV Extractor: {e}")
        else:
            print(f"⚠️ Azure OpenAI not configured - CV extraction unavailable")
    
    async def extract_cv_facts(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract CV facts using improved prompt with zero hallucination.
        Returns structured JSON with only explicit CV content.
        """
        if not self.client:
            raise Exception("Azure OpenAI not configured")
        
        print(f"📄 Extracting facts from CV ({len(cv_text)} chars)")
        
        prompt = self._build_extraction_prompt(cv_text)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fact extraction engine. Return only valid JSON with no commentary."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic extraction
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content.strip()
            extracted = json.loads(result)
            
            print(f"✅ Extracted: {len(extracted.get('skills', []))} skills, "
                  f"{len(extracted.get('experience', []))} jobs, "
                  f"{extracted.get('years_experience_total', 0)} total years")
            
            return extracted
            
        except Exception as e:
            print(f"❌ CV extraction failed: {e}")
            raise
    
    def _build_extraction_prompt(self, cv_text: str) -> str:
        """Build extraction prompt from MATCHER_V4.0_PROMPTS_REVIEW.md"""
        return f"""
You are a CV extraction engine. Extract ONLY factual information with ZERO inference or guessing.

CRITICAL RULES:
1. Extract ONLY text that appears in the CV
2. If something is not explicitly written, return null or []
3. Do NOT infer technologies from job descriptions
4. Do NOT assume experience duration if not stated
5. Do NOT interpret or summarize - extract verbatim

Return valid JSON ONLY:
{{
  "skills": [],
  "languages": [],
  "frameworks": [],
  "cloud_platforms": [],
  "databases": [],
  "tools": [],
  
  "education": [
    {{
      "degree": null,
      "field": null,
      "institution": null,
      "year": null
    }}
  ],
  
  "experience": [
    {{
      "title": "",
      "company": "",
      "start_year": null,
      "end_year": null,
      "duration_years": null,
      "responsibilities": [],
      "technologies": []
    }}
  ],
  
  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": [],
      "url": null
    }}
  ],
  
  "certifications": [
    {{
      "name": "",
      "issuer": null,
      "year": null
    }}
  ],
  
  "years_experience_total": null,
  
  "seniority_signals": [],
  
  "domain_expertise": [],
  
  "soft_skills": []
}}

FIELD DEFINITIONS:

- skills: All technical skills explicitly listed (any tech mentioned)
- languages: Programming languages only (Python, Java, C#, etc.)
- frameworks: Web/mobile frameworks (React, Django, Spring, etc.)
- cloud_platforms: AWS, Azure, GCP, etc.
- databases: PostgreSQL, MongoDB, MySQL, etc.
- tools: Git, Docker, Jenkins, Kubernetes, etc.

- education: Extract degree, field, institution, year if present
  * degree: "Bachelor's", "Master's", "Ph.D.", "Training", "Bootcamp", etc.
  * field: "Computer Science", "Engineering", "Cybersecurity", etc.

- experience: Extract job title, company, dates, responsibilities, tech
  * start_year/end_year: Extract if dates provided (end_year = null if current)
  * duration_years: Calculate from dates if available
  * responsibilities: Key bullet points verbatim
  * technologies: Tech mentioned in THIS specific role

- projects: Side projects, open source contributions
  * Extract name, brief description, technologies used
  * url: GitHub, portfolio link if provided

- certifications: Professional certifications
  * name: Full certification name ("AWS Certified Solutions Architect")
  * issuer: Certifying body ("Amazon Web Services")
  * year: Year obtained if provided

- years_experience_total: Total professional years across all roles

- seniority_signals: Extract EXACT phrases only:
  * "Senior", "Lead", "Staff", "Principal"
  * "Led team of X", "Managed Y engineers"
  * "Tech lead", "Squad lead", "Team leader"

- domain_expertise: Only if EXPLICITLY stated:
  * "Backend", "Frontend", "Full-stack"
  * "Data", "Security", "DevOps", "Mobile"
  * "Cybersecurity", "Machine Learning", "Data Platform"

- soft_skills: Only if explicitly mentioned:
  * "Leadership", "Mentoring", "Public speaking"
  * "Technical writing", "Cross-team collaboration"

EXAMPLES:

GOOD Extraction (CV says "Led team of 5 engineers"):
- seniority_signals: ["Led team of 5 engineers"]

BAD Extraction (CV says "Software Engineer at Microsoft"):
- seniority_signals: ["Senior"]  ❌ NOT explicitly stated

GOOD Extraction (CV lists "Python, React, PostgreSQL"):
- languages: ["Python"]
- frameworks: ["React"]
- databases: ["PostgreSQL"]

BAD Extraction (CV says "Developed web applications"):
- frameworks: ["React", "Node.js"]  ❌ NOT explicitly listed

GOOD Extraction (CV says "Backend engineer with focus on data platforms"):
- domain_expertise: ["Backend", "Data platforms"]

BAD Extraction (CV says "Worked at Microsoft"):
- domain_expertise: ["Cloud", "Enterprise"]  ❌ Inferred, not stated

CV TEXT:
{cv_text}

Return ONLY valid JSON. No markdown, no explanations, no commentary.
"""