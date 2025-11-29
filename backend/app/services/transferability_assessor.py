from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any, List
import asyncio


class TransferabilityAssessor:
    """
    AI-assisted transferability assessment.
    v4.0: Narrow scope - only rate skill similarity, not overall fit.
    """
    
    def __init__(self):
        self.client = None
        print(f"🔧 Initializing Transferability Assessor v4.0")
        print(f"   Endpoint: {settings.AZURE_OPENAI_ENDPOINT or '(not set)'}")
        print(f"   API Key: {'✓ Set' if settings.AZURE_OPENAI_KEY else '✗ Not set'}")

        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
            try:
                self.client = AsyncAzureOpenAI(
                    api_key=settings.AZURE_OPENAI_KEY,
                    api_version="2024-02-15-preview",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
                print(f"✅ Transferability Assessor v4.0 initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Transferability Assessor: {e}")
        else:
            print(f"⚠️ Azure OpenAI not configured")
    
    async def assess_missing_skills(
        self,
        cv_skills: List[str],
        missing_requirements: List[Dict[str, Any]],
        cv_years: int,
        cv_domain: List[str],
        job_domain: str
    ) -> Dict[str, Any]:
        """
        Assess transferability for all missing requirements.
        Uses parallel API calls for speed.
        
        Returns:
            {
                "assessments": [
                    {
                        "requirement": str,
                        "transferability_score": float,
                        "reasoning": str,
                        "ramp_up_time": str
                    },
                    ...
                ]
            }
        """
        if not self.client:
            print("⚠️ No AI client, returning 0.0 transferability for all")
            return {
                "assessments": [
                    {
                        "requirement": req["requirement"],
                        "transferability_score": 0.0,
                        "reasoning": "AI not configured",
                        "ramp_up_time": "Unknown"
                    }
                    for req in missing_requirements
                ]
            }
        
        if not missing_requirements:
            print("✅ No missing requirements to assess")
            return {"assessments": []}
        
        print(f"🔄 Assessing transferability for {len(missing_requirements)} missing requirements")
        
        # Assess each missing requirement in parallel
        tasks = [
            self._assess_single_requirement(
                cv_skills,
                req["requirement"],
                cv_years,
                cv_domain,
                job_domain
            )
            for req in missing_requirements
        ]
        
        assessments = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_assessments = []
        for i, assessment in enumerate(assessments):
            if isinstance(assessment, Exception):
                print(f"❌ Assessment failed for {missing_requirements[i]['requirement']}: {assessment}")
                # Add fallback assessment
                valid_assessments.append({
                    "requirement": missing_requirements[i]["requirement"],
                    "transferability_score": 0.0,
                    "reasoning": f"Assessment failed: {str(assessment)}",
                    "ramp_up_time": "Unknown"
                })
            else:
                valid_assessments.append(assessment)
        
        print(f"✅ Assessed {len(valid_assessments)} requirements")
        
        return {"assessments": valid_assessments}
    
    async def _assess_single_requirement(
        self,
        cv_skills: List[str],
        missing_req: str,
        cv_years: int,
        cv_domain: List[str],
        job_domain: str
    ) -> Dict[str, Any]:
        """
        Assess transferability for one missing requirement.
        Uses improved prompt from MATCHER_V4.0_PROMPTS_REVIEW.md
        """
        
        prompt = self._build_transferability_prompt(
            cv_skills, missing_req, cv_years, cv_domain, job_domain
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill transferability rater. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low for consistency
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content.strip()
            assessment = json.loads(result)
            
            # Ensure required fields
            if "transferability_score" not in assessment:
                assessment["transferability_score"] = 0.0
            if "reasoning" not in assessment:
                assessment["reasoning"] = "No reasoning provided"
            if "ramp_up_time" not in assessment:
                assessment["ramp_up_time"] = "Unknown"
            if "requirement" not in assessment:
                assessment["requirement"] = missing_req
            
            return assessment
            
        except Exception as e:
            print(f"❌ Error assessing {missing_req}: {e}")
            return {
                "requirement": missing_req,
                "transferability_score": 0.0,
                "reasoning": f"Error: {str(e)}",
                "ramp_up_time": "Unknown"
            }
    
    def _build_transferability_prompt(
        self,
        cv_skills: List[str],
        missing_req: str,
        cv_years: int,
        cv_domain: List[str],
        job_domain: str
    ) -> str:
        """Build transferability prompt from MATCHER_V4.0_PROMPTS_REVIEW.md"""
        
        cv_skills_str = ", ".join(cv_skills[:20])  # Limit to first 20 skills
        if len(cv_skills) > 20:
            cv_skills_str += f" (and {len(cv_skills) - 20} more)"
        
        cv_domain_str = ", ".join(cv_domain) if cv_domain else "Not specified"
        
        return f"""
Rate transferability from 0.0 to 1.0 for this missing requirement.

CANDIDATE HAS:
Skills: {cv_skills_str}
Years of experience: {cv_years}
Domain: {cv_domain_str}

MISSING REQUIREMENT: {missing_req}

JOB DOMAIN: {job_domain}

RATING SCALE (0.0 to 1.0):

**1.0** - Exact Match (same skill, different name)
  Examples: "React.js" vs "React", "PostgreSQL" vs "Postgres"

**0.9** - Near-Identical (minor variant)
  Examples: "Python 3" vs "Python", "AWS Cloud" vs "Amazon Web Services"

**0.8** - Adjacent Framework (same purpose, different tool)
  Examples: "Angular" → "React", "MySQL" → "PostgreSQL", "Jenkins" → "GitLab CI"
  Ramp-up: 2-4 weeks

**0.7** - Same Category (different frameworks, same domain)
  Examples: "Vue.js" → "React", "MongoDB" → "PostgreSQL", "Flask" → "FastAPI"
  Ramp-up: 1-2 months

**0.6** - Same Domain (different tech stack, same problem space)
  Examples: "Backend (Python)" → "Backend (Node.js)", "iOS (Swift)" → "Android (Kotlin)"
  Ramp-up: 2-3 months

**0.5** - Transferable with Training (senior engineer, learnable skill)
  Applies when: 10+ years in ANY domain + missing requirement is framework/tool
  Examples: "10 years Backend (Python)" → "React", "Senior Engineer" → "TypeScript"
  Ramp-up: 3-6 months

**0.4** - Loosely Related (some overlap, significant learning)
  Examples: "5 years Backend" → "React", "Data analysis" → "Machine Learning"
  Ramp-up: 6-9 months

**0.3** - Peripheral (tangentially related, different focus)
  Examples: "Backend" → "Frontend", "DevOps" → "Data Science"
  Ramp-up: 9-12 months

**0.2** - Minimal Overlap (same industry, different role)
  Examples: "QA Engineer" → "Software Engineer"

**0.0** - Unrelated (completely different field)
  Examples: "Marketing" → "React", "Sales" → "Python"

SPECIAL RULES:
1. Senior Bonus: If {cv_years}+ years + "Senior"/"Lead" → add +0.1 (max 1.0)
2. Domain Penalty: If candidate domain ORTHOGONAL to job domain → cap at 0.5
3. Adjacent frameworks (React/Angular/Vue) → minimum 0.7

Return JSON:
{{
  "requirement": "{missing_req}",
  "transferability_score": 0.0-1.0,
  "reasoning": "Brief explanation (1-2 sentences)",
  "ramp_up_time": "2-4 weeks|1-2 months|3-6 months|6-12 months|12+ months|Not transferable"
}}

CRITICAL: Be consistent. Same input should produce same score ±0.1.
"""