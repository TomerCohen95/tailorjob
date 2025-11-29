from openai import AsyncAzureOpenAI
from app.config import settings
from typing import Dict, Any, List
import json


class ExplanationGenerator:
    """
    Phase 4: Explanation Generation (AI - Constrained)
    
    Generates human-readable explanations using ONLY extracted data.
    - Strengths: Evidence-based highlights from CV
    - Gaps: What's missing (must-have + nice-to-have)
    - Recommendations: Actionable improvements
    
    Key constraints:
    - Temperature 0.3 (focused but natural)
    - Must reference actual CV content
    - Cannot hallucinate qualifications
    """
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
    
    async def generate_explanation(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        comparison: Dict[str, Any],
        transferability: Dict[str, Any],
        scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate strengths, gaps, and recommendations.
        
        Returns:
            {
                "strengths": ["...", "..."],
                "gaps": ["...", "..."],
                "recommendations": ["...", "..."]
            }
        """
        
        prompt = self._build_explanation_prompt(
            cv_data, job_data, comparison, transferability, scores
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a career advisor generating CV match explanations. "
                            "You MUST only reference facts from the provided CV data. "
                            "Do NOT invent or assume qualifications. "
                            "Be specific and cite evidence (company names, years, technologies). "
                            "Return valid JSON only."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "strengths": result.get("strengths", [])[:5],  # Max 5
                "gaps": result.get("gaps", [])[:5],  # Max 5
                "recommendations": result.get("recommendations", [])[:5]  # Max 5
            }
            
        except Exception as e:
            print(f"❌ Explanation generation failed: {e}")
            return self._generate_fallback_explanation(comparison)
    
    def _build_explanation_prompt(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        comparison: Dict[str, Any],
        transferability: Dict[str, Any],
        scores: Dict[str, Any]
    ) -> str:
        """Build prompt for explanation generation"""
        
        # Extract key data
        cv_summary = cv_data.get("summary", "Not provided")
        cv_experience = cv_data.get("experience_detailed", [])
        cv_skills = cv_data.get("skills", {})
        cv_years = cv_data.get("years_experience_total", 0)
        
        job_title = job_data.get("title", "Unknown")
        matched_must = [r["requirement"] for r in comparison["matched_must_have"]]
        missing_must = [r["requirement"] for r in comparison["missing_must_have"]]
        matched_nice = [r["requirement"] for r in comparison["matched_nice_have"]]
        missing_nice = [r["requirement"] for r in comparison["missing_nice_have"]]
        
        # Add education/experience/management to missing if not met
        education_match = comparison.get("education_match", {})
        if education_match.get("status") == "NOT_MET":
            missing_must.append(education_match.get("requirement", "Degree requirement"))
        
        experience_match = comparison.get("experience_match", {})
        if experience_match.get("status") == "NOT_MET":
            missing_must.append(experience_match.get("requirement", "Experience requirement"))
        
        management_match = comparison.get("management_match", {})
        if management_match and management_match.get("status") == "NOT_MET":
            missing_must.append(management_match.get("requirement", "Management experience"))
        
        # Transferability info
        transferable_skills = [
            a for a in transferability.get("assessments", [])
            if a.get("transferability_score", 0) >= 0.5
        ]
        
        prompt = f"""Analyze this CV-to-job match and generate explanations.

JOB TITLE: {job_title}

CV SUMMARY:
{cv_summary}

CV EXPERIENCE ({cv_years} years total):
{json.dumps(cv_experience[:3], indent=2)}

CV SKILLS:
{json.dumps(cv_skills, indent=2)}

MATCH RESULTS:
- Matched Must-Have Requirements: {matched_must}
- Missing Must-Have Requirements: {missing_must}
- Matched Nice-to-Have: {matched_nice}
- Missing Nice-to-Have: {missing_nice}

TRANSFERABILITY ANALYSIS:
{json.dumps(transferable_skills, indent=2)}

SCORES:
- Overall: {scores['overall_score']}%
- Skills: {scores['skills_score']}%
- Experience: {scores['experience_score']}%
- Qualifications: {scores['qualifications_score']}%

Generate a JSON response with:
1. "strengths": List 3-5 specific achievements/skills from the CV that match job requirements. 
   Include company names, years, and technologies. Be concrete.

2. "gaps": List what's missing (both must-have and nice-to-have).
   Be factual - if candidate lacks something, state it clearly.

3. "recommendations": List 3-5 actionable steps to improve match score.
   Be specific (e.g., "Gain experience with X", "Obtain Y certification").

CRITICAL RULES:
- Only reference facts from the CV data above
- Include company names and years for credibility
- Do NOT invent qualifications
- Be specific, not generic
- If something is missing, say so directly

Return JSON format:
{{
    "strengths": ["...", "..."],
    "gaps": ["...", "..."],
    "recommendations": ["...", "..."]
}}"""
        
        return prompt
    
    def _generate_fallback_explanation(
        self,
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate basic explanation if AI fails"""
        
        matched = [r["requirement"] for r in comparison["matched_must_have"]]
        missing = [r["requirement"] for r in comparison["missing_must_have"]]
        
        return {
            "strengths": [
                f"Meets requirement: {req}" for req in matched[:3]
            ] if matched else ["Unable to determine strengths"],
            
            "gaps": [
                f"Missing requirement: {req}" for req in missing[:3]
            ] if missing else ["No critical gaps identified"],
            
            "recommendations": [
                "Review job requirements carefully",
                "Ensure CV highlights relevant experience",
                "Consider adding certifications if applicable"
            ]
        }