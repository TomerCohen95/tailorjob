from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any


class CVMatcherService:
    """
    AI-powered CV-to-Job matching service using Azure OpenAI.
    Generates deterministic match scores, strengths, gaps, and recommendations.
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
            print(f"⚠️ Azure OpenAI not configured - CV matching unavailable")

    async def analyze_match(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not self.client:
            raise Exception("Azure OpenAI not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY.")

        print(f"🎯 Analyzing CV match for job: {job_data.get('title')}")

        prompt = self._build_analysis_prompt(cv_data, job_data)

        # NEW SYSTEM MESSAGE (rewritten)
        system_message = """
You are an expert technical recruiter and hiring specialist.

Your task is to evaluate how well a candidate's CV matches a job description.  
Follow these strict rules:

1. Evaluate ONLY based on explicit content provided. No assumptions or invented requirements.
2. Normalize skill names (lowercase, trim, map synonyms such as "k8s"→"kubernetes", "js"→"javascript").
3. Apply deterministic scoring:

- Skills Score = (matched_skills_count / total_job_skills) * 100
- Qualifications Score = (matched_qualifications_count / total_job_qualifications) * 100
- Experience Score:
    • Strong alignment → 80–100  
    • Partial alignment → 50–79  
    • Weak alignment → 20–49  
    • Very weak or missing → 0–19

- Overall Score = (Skills 40%) + (Experience 40%) + (Qualifications 20%)

4. Output MUST be a single valid JSON object matching this schema:

{
  "overall_score": integer,
  "skills_score": integer,
  "experience_score": integer,
  "qualifications_score": integer,
  "strengths": string[],
  "gaps": string[],
  "recommendations": string[],
  "matched_skills": string[],
  "missing_skills": string[],
  "matched_qualifications": string[],
  "missing_qualifications": string[]
}

5. Use empty arrays [] when needed (never null).
6. All scores must be integers 0–100.
7. DO NOT output markdown, code blocks, explanations, or surrounding text. Only JSON.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,   # deterministic
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()

            # Should already be plain JSON now
            analysis = json.loads(result)

            # Ensure ALL fields exist (safety)
            required_fields = [
                "overall_score",
                "skills_score",
                "experience_score",
                "qualifications_score",
                "strengths",
                "gaps",
                "recommendations",
                "matched_skills",
                "missing_skills",
                "matched_qualifications",
                "missing_qualifications"
            ]

            for field in required_fields:
                if field not in analysis:
                    print(f"⚠️ Missing field from model: {field}, setting default.")
                    if "score" in field:
                        analysis[field] = 0
                    else:
                        analysis[field] = []

            # Normalize scores
            for score_field in [
                "overall_score",
                "skills_score",
                "experience_score",
                "qualifications_score"
            ]:
                try:
                    analysis[score_field] = int(analysis.get(score_field, 0))
                    if analysis[score_field] < 0 or analysis[score_field] > 100:
                        analysis[score_field] = max(0, min(100, analysis[score_field]))
                except:
                    analysis[score_field] = 0

            print(f"✅ Match analysis complete: {analysis['overall_score']}% match")
            return analysis

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Raw output was: {result[:500]}")
            raise ValueError(f"Failed to parse AI JSON: {str(e)}")

        except Exception as e:
            print(f"❌ Error analyzing CV match: {e}")
            raise ValueError(f"Failed to analyze CV match: {str(e)}")

    def _build_analysis_prompt(self, cv_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """
        Build user prompt: includes job info + CV details.
        """

        # Experience formatting
        experience_text = ""
        if cv_data.get("experience"):
            for exp in cv_data["experience"]:
                experience_text += f"\n- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('period', 'N/A')})"
                desc = exp.get("description")
                if desc:
                    if isinstance(desc, list):
                        for item in desc:
                            experience_text += f"\n  • {item}"
                    else:
                        experience_text += f"\n  • {desc}"

        # Education formatting
        education_text = ""
        if cv_data.get("education"):
            for edu in cv_data["education"]:
                education_text += f"\n- {edu.get('degree', 'N/A')} in {edu.get('field', 'N/A')} from {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})"

        # Job description formatting
        job_desc = job_data.get("description", "")
        if isinstance(job_desc, dict):
            parts = []
            if job_desc.get("responsibilities"):
                parts.append("Responsibilities: " + ", ".join(job_desc["responsibilities"]))
            if job_desc.get("requirements"):
                parts.append("Requirements: " + ", ".join(job_desc["requirements"]))
            if job_desc.get("qualifications"):
                parts.append("Qualifications: " + ", ".join(job_desc["qualifications"]))
            job_desc_text = " | ".join(parts)
        else:
            job_desc_text = str(job_desc)

        job_desc_text = job_desc_text[:6000]  # safety truncate (gpt-4o-mini supports larger context)

        return f"""
Evaluate how well this CV matches the job description. Follow all rules in the system message.

### JOB DETAILS
Title: {job_data.get('title')}
Company: {job_data.get('company')}
Description:
{job_desc_text}

### CV DETAILS
Summary:
{cv_data.get('summary', 'Not provided')}

Skills:
{', '.join(cv_data.get('skills', [])) if cv_data.get('skills') else 'None listed'}

Experience:
{experience_text if experience_text else 'None listed'}

Education:
{education_text if education_text else 'None listed'}

Certifications:
{', '.join(cv_data.get('certifications', [])) if cv_data.get('certifications') else 'None listed'}

Your output MUST be a single valid JSON object matching the schema in the system message.
"""


# Singleton instance
cv_matcher_service = CVMatcherService()
