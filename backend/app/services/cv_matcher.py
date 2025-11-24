from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any

class CVMatcherService:
    """
    AI-powered CV-to-Job matching service using Azure OpenAI.
    Analyzes compatibility and provides detailed recommendations.
    """
    
    def __init__(self):
        self.client = None
        print(f"🔧 Initializing CV Matcher Service")
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
                print(f"✅ CV Matcher client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize CV Matcher client: {e}")
        else:
            print(f"⚠️  Azure OpenAI not configured - CV matching unavailable")
    
    async def analyze_match(
        self, 
        cv_data: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze how well a CV matches a job description.
        
        Args:
            cv_data: Parsed CV sections (summary, skills, experience, etc.)
            job_data: Job details (title, company, description)
            
        Returns:
            Match analysis with scores and recommendations
        """
        if not self.client:
            raise Exception("Azure OpenAI not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY.")
        
        print(f"🎯 Analyzing CV match for job: {job_data.get('title')}")
        
        prompt = self._build_analysis_prompt(cv_data, job_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert recruiter analyzing CV-job fit. Provide honest, actionable feedback in valid JSON format only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result.startswith('```json'):
                result = result[7:]
                if result.endswith('```'):
                    result = result[:-3]
            elif result.startswith('```'):
                result = result[3:]
                if result.endswith('```'):
                    result = result[:-3]
            
            result = result.strip()
            
            # Parse JSON response
            analysis = json.loads(result)
            
            # Validate required fields
            required_fields = ['overall_score', 'strengths', 'gaps', 'recommendations']
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field in AI response: {field}")
            
            # Ensure scores are integers and within range
            analysis['overall_score'] = int(analysis['overall_score'])
            if analysis['overall_score'] < 0 or analysis['overall_score'] > 100:
                analysis['overall_score'] = max(0, min(100, analysis['overall_score']))
            
            # Ensure optional scores are also valid if present
            for score_field in ['skills_score', 'experience_score', 'qualifications_score']:
                if score_field in analysis and analysis[score_field] is not None:
                    analysis[score_field] = int(analysis[score_field])
                    analysis[score_field] = max(0, min(100, analysis[score_field]))
            
            print(f"✅ Match analysis complete: {analysis['overall_score']}% match")
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            print(f"Raw response: {result[:200]}...")
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            print(f"❌ Error analyzing CV match: {e}")
            raise ValueError(f"Failed to analyze CV match: {str(e)}")
    
    def _build_analysis_prompt(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """Build the analysis prompt with CV and job data"""
        
        # Format experience for better readability
        experience_text = ""
        if cv_data.get('experience'):
            for exp in cv_data['experience']:
                experience_text += f"\n- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('period', 'N/A')})"
                if exp.get('description'):
                    if isinstance(exp['description'], list):
                        for desc in exp['description']:
                            experience_text += f"\n  • {desc}"
                    else:
                        experience_text += f"\n  • {exp['description']}"
        
        # Format education
        education_text = ""
        if cv_data.get('education'):
            for edu in cv_data['education']:
                education_text += f"\n- {edu.get('degree', 'N/A')} in {edu.get('field', 'N/A')} from {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})"
        
        # Handle job description - can be string or structured JSON
        job_description = job_data.get('description', '')
        if isinstance(job_description, dict):
            # Structured job description - format nicely
            desc_parts = []
            if job_description.get('responsibilities'):
                desc_parts.append(f"Responsibilities: {', '.join(job_description['responsibilities'][:5])}")
            if job_description.get('requirements'):
                desc_parts.append(f"Requirements: {', '.join(job_description['requirements'][:5])}")
            if job_description.get('qualifications'):
                desc_parts.append(f"Qualifications: {', '.join(job_description['qualifications'][:5])}")
            job_desc_text = ' | '.join(desc_parts)[:2000]
        else:
            # Plain text description
            job_desc_text = str(job_description)[:2000]
        
        return f"""Analyze how well this CV matches the job description. Provide scores and actionable recommendations.

**Job Details:**
Title: {job_data.get('title')}
Company: {job_data.get('company')}
Description: {job_desc_text}

**Candidate CV:**
Summary: {cv_data.get('summary', 'Not provided')}

Skills: {', '.join(cv_data.get('skills', [])) if cv_data.get('skills') else 'None listed'}

Experience:{experience_text if experience_text else ' None listed'}

Education:{education_text if education_text else ' None listed'}

Certifications: {', '.join(cv_data.get('certifications', [])) if cv_data.get('certifications') else 'None listed'}

Return ONLY a JSON object with this EXACT structure (no additional text):
{{
  "overall_score": 85,
  "skills_score": 90,
  "experience_score": 80,
  "qualifications_score": 85,
  "strengths": [
    "Strong Python and AWS experience aligns with requirements",
    "Leadership experience matches senior role expectations"
  ],
  "gaps": [
    "Missing Kubernetes experience mentioned in requirements",
    "No machine learning background for ML-related tasks"
  ],
  "recommendations": [
    "Emphasize Python projects in summary",
    "Highlight AWS certifications prominently",
    "Consider adding relevant ML coursework or projects"
  ],
  "matched_skills": ["Python", "AWS", "Docker", "CI/CD"],
  "missing_skills": ["Kubernetes", "Machine Learning", "TensorFlow"],
  "matched_qualifications": ["5+ years experience", "Bachelor's degree", "Team leadership"],
  "missing_qualifications": ["MBA (preferred)", "Public speaking experience"]
}}

Guidelines:
- Be honest but constructive in your assessment
- Scores should reflect realistic match percentage (0-100)
- Focus on actionable recommendations the candidate can implement
- Consider both required and preferred qualifications
- Match skills even if terminology differs (e.g., "JS" vs "JavaScript")
- If arrays are empty, use empty arrays [], not null
- All scores must be integers between 0-100
"""


# Singleton instance
cv_matcher_service = CVMatcherService()