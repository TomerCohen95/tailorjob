import PyPDF2
import io
import json
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from app.config import settings

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
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
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

Return ONLY a valid JSON object with this exact structure:
{{
    "summary": "Complete professional summary or objective - include ALL details, achievements, and qualifications mentioned",
    "skills": ["skill1", "skill2", "skill3", "..."],
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
- Extract ALL skills mentioned (technical, soft skills, tools, technologies, languages)
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
                    {"role": "system", "content": "You are a CV parser that returns only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
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
            
            return parsed_data
            
        except json.JSONDecodeError as e:
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
cv_parser_service = CVParserService()