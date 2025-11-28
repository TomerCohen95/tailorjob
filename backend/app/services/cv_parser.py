import pdfplumber
import io
import json
from typing import Dict, Any, Optional, List
from openai import AzureOpenAI
from app.config import settings
import dateparser
from datetime import datetime

class CVParserService:
    """Service for parsing CV content using Azure OpenAI"""
    
    def __init__(self):
        self.client = None
        print(f"🔧 Initializing CV Parser Service")
        print(f"   Endpoint: {settings.AZURE_OPENAI_ENDPOINT or '(not set)'}")
        print(f"   API Key: {'✓ Set' if settings.AZURE_OPENAI_KEY else '✗ Not set'}")
        print(f"   Deployment: {settings.AZURE_OPENAI_DEPLOYMENT or '(not set)'}")
        
        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
            try:
                self.client = AzureOpenAI(
                    api_key=settings.AZURE_OPENAI_KEY,
                    api_version="2024-02-01",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                print(f"✅ Azure OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Azure OpenAI client: {e}")
        else:
            print(f"⚠️  Azure OpenAI not configured - will use fallback parsing")
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file using pdfplumber for better layout preservation"""
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    async def parse_cv_text(self, cv_text: str) -> Dict[str, Any]:
        """Parse CV text using Azure OpenAI to extract structured data"""
        
        print(f"📋 parse_cv_text called - Client available: {self.client is not None}")
        
        if not self.client:
            # Fallback: return basic structure without AI parsing
            print(f"⚠️  Returning fallback response - Azure OpenAI client not available")
            return {
                "summary": "AI parsing not configured",
                "skills": ["Please configure Azure OpenAI"],
                "experience": [],
                "education": [],
                "certifications": []
            }
        
        print(f"🤖 Using Azure OpenAI to parse CV text ({len(cv_text)} chars)")
        
        try:
            prompt = f"""
You are a CV/Resume parser. Extract ALL structured information from the CV text below.

IMPORTANT: DO NOT summarize or shorten any content. Extract COMPLETE and DETAILED information as it appears in the CV.
This data will be used later for job tailoring, so preserving all details is critical.

Ensure all strings are properly escaped for JSON (especially backslashes).
Return ONLY a valid JSON object with this exact structure:
{{
    "summary": "Complete professional summary or objective - include ALL details, achievements, and qualifications mentioned",
    "skills": {{
        "languages": ["Python", "JavaScript", ...],
        "frameworks": ["React", "FastAPI", ...],
        "tools": ["Docker", "Git", ...],
        "soft_skills": ["Leadership", "Communication", ...]
    }},
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "period": "Start - End Date",
            "description": ["Responsibility or achievement 1", "Responsibility or achievement 2", "..."]
        }}
    ],
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "University/School Name",
            "year": "Graduation Year",
            "field": "Field of Study"
        }}
    ],
    "certifications": ["Certification 1", "Certification 2"]
}}

Guidelines:
- Categorize skills into languages, frameworks, tools, and soft skills. If unsure, put in 'tools'.
- For experience: The "description" field MUST be an array of strings, where each string is a separate bullet point/responsibility/achievement
- Split bullet points into separate array items - do NOT combine them into one long string
- Preserve specific details like project names, team sizes, technologies used, results achieved
- Do NOT condense or summarize - extract verbatim when possible
- Remove bullet point symbols (●, •, -, *) from the beginning of each item - just include the text

CV Text:
{cv_text}

JSON Response:"""

            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a CV parser that returns only valid JSON. Ensure all strings are properly escaped."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(result_text)
            
            # Calculate years of experience per skill
            parsed_data["skills_experience"] = self._calculate_experience(parsed_data)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error. Raw text content:\n{result_text}")
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to parse CV with AI: {str(e)}")
    
    async def parse_cv_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse CV file (PDF or DOCX) and extract structured data"""
        
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            cv_text = self.extract_text_from_pdf(file_content)
        elif filename.lower().endswith('.docx'):
            # For now, return placeholder for DOCX
            # You can add python-docx library later for DOCX parsing
            return {
                "summary": "DOCX parsing not yet implemented",
                "skills": ["Please use PDF format"],
                "experience": [],
                "education": [],
                "certifications": []
            }
        else:
            raise Exception("Unsupported file format. Only PDF and DOCX are supported.")
        
        # Parse the extracted text
        parsed_data = await self.parse_cv_text(cv_text)
        
        return parsed_data

# Global instance
    def _calculate_experience(self, parsed_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate years of experience for each skill based on job history.
        Returns a dictionary mapping skill names to years of experience.
        """
        skill_years = {}
        
        # Flatten skills list for easy lookup
        all_skills = []
        skills_data = parsed_data.get("skills", {})
        if isinstance(skills_data, dict):
            for category in skills_data.values():
                if isinstance(category, list):
                    all_skills.extend([s.lower() for s in category])
        elif isinstance(skills_data, list):
            all_skills = [s.lower() for s in skills_data]
            
        experience_list = parsed_data.get("experience", [])
        
        for job in experience_list:
            # Parse dates
            period = job.get("period", "")
            if not period:
                continue
                
            # Split period into start and end
            parts = period.split("-")
            if len(parts) != 2:
                # Try "to" separator
                parts = period.split(" to ")
                
            if len(parts) != 2:
                continue
                
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            
            start_date = dateparser.parse(start_str)
            
            if end_str.lower() in ["present", "current", "now"]:
                end_date = datetime.now()
            else:
                end_date = dateparser.parse(end_str)
                
            if not start_date or not end_date:
                continue
                
            # Calculate duration in years
            duration_days = (end_date - start_date).days
            duration_years = max(0, duration_days / 365.25)
            
            # Check for skills in job description
            description = job.get("description", [])
            if isinstance(description, list):
                desc_text = " ".join(description).lower()
            else:
                desc_text = str(description).lower()
                
            # Also check title
            title = job.get("title", "").lower()
            full_text = f"{title} {desc_text}"
            
            for skill in all_skills:
                # Simple substring match for now - could be improved with regex or NLP
                # Add spaces to avoid partial matches (e.g. "java" in "javascript")
                if f" {skill} " in f" {full_text} " or \
                   f" {skill}," in f" {full_text} " or \
                   f" {skill}." in f" {full_text} ":
                    skill_years[skill] = skill_years.get(skill, 0) + duration_years
                    
        # Round to 1 decimal place
        return {k: round(v, 1) for k, v in skill_years.items()}

cv_parser_service = CVParserService()