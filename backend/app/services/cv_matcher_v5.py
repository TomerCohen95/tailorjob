"""
CV Matcher v5.0 - Fully AI-driven matching with GPT-4.
No computation, no formulas - just pure AI reasoning.

Architecture:
1. Extract CV facts (GPT-4o-mini, temp=0.0)
2. Analyze match (GPT-4, temp=0.2) - does EVERYTHING
"""

from typing import Dict, Any
from openai import AsyncAzureOpenAI
import json
from datetime import datetime


class CVMatcherV5:
    """
    Fully AI-driven CV matcher using GPT-4.
    Single comprehensive prompt handles:
    - Requirement matching (semantic + transferable)
    - Scoring (skills, experience, qualifications, overall)
    - Explanation (strengths, gaps, recommendations)
    """
    
    def __init__(
        self,
        extractor,
        gpt4_client: AsyncAzureOpenAI,
        gpt4_deployment: str
    ):
        """
        Initialize v5.0 matcher.
        
        Args:
            extractor: CV extractor instance (v5)
            gpt4_client: Azure OpenAI client for GPT-4
            gpt4_deployment: GPT-4 deployment name
        """
        self.extractor = extractor
        self.gpt4_client = gpt4_client
        self.gpt4_deployment = gpt4_deployment
        
        print(f"🔧 Initializing CV Matcher v5.0 (Fully AI-Driven)")
        print(f"   GPT-4 Deployment: {gpt4_deployment}")
        print(f"✅ CV Matcher v5.0 initialized successfully")
    
    async def analyze_match(
        self,
        cv_text: str,
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze CV-to-job match using pure AI reasoning.
        
        Args:
            cv_text: Raw CV text content
            job_data: Job posting data with requirements
            
        Returns:
            Complete analysis with scores, matches, gaps, explanations
        """
        print("\n" + "="*60)
        print(f"🎯 [v5.0] Analyzing CV match for job: {job_data.get('title', 'Unknown')}")
        print("="*60)
        
        try:
            # Stage 1: Extract CV facts (GPT-4o-mini)
            cv_facts = await self.extractor.extract_facts(cv_text)
            
            # Stage 2: Analyze match (GPT-4) - THE MAGIC HAPPENS HERE
            print(f"🧠 Analyzing match with GPT-4 (advanced reasoning)")
            analysis = await self._analyze_with_gpt4(cv_facts, job_data)
            
            # Add metadata
            analysis["analyzed_at"] = datetime.utcnow().isoformat()
            analysis["matcher_version"] = "5.0"
            analysis["scoring_method"] = "GPT-4 holistic reasoning (no computation)"
            
            print("\n" + "="*60)
            print(f"✅ [v5.0] Match analysis complete: {analysis['overall_score']}% match")
            print("="*60 + "\n")
            
            return analysis
            
        except Exception as e:
            print(f"❌ [v5.0] Match analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _analyze_with_gpt4(
        self,
        cv_facts: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use GPT-4 to analyze match with advanced reasoning.
        Single prompt does: comparison + scoring + explanation.
        """
        prompt = self._build_analysis_prompt(cv_facts, job_data)
        
        response = await self.gpt4_client.chat.completions.create(
            model=self.gpt4_deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Low temp for consistency, slight creativity for explanations
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # Validate required fields
        required = [
            "overall_score", "skills_score", "experience_score", "qualifications_score",
            "matched_must_have", "missing_must_have",
            "matched_nice_to_have", "missing_nice_to_have",
            "strengths", "gaps", "recommendations"
        ]
        for field in required:
            if field not in analysis:
                raise ValueError(f"GPT-4 response missing required field: {field}")
        
        print(f"✅ GPT-4 analysis complete:")
        print(f"   Overall: {analysis['overall_score']}%")
        print(f"   Skills: {analysis['skills_score']}%")
        print(f"   Experience: {analysis['experience_score']}%")
        print(f"   Qualifications: {analysis['qualifications_score']}%")
        
        return analysis
    
    def _build_analysis_prompt(
        self,
        cv_facts: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive analysis prompt for GPT-4.
        This is THE prompt that does everything - no computation!
        """
        # Extract job requirements
        requirements = job_data.get("requirements_matrix", {})
        must_have = requirements.get("must_have", [])
        nice_to_have = requirements.get("nice_to_have", [])
        
        # Format CV facts
        cv_summary = cv_facts.get("summary", "Not provided")
        cv_skills = json.dumps(cv_facts.get("skills", {}), indent=2)
        cv_experience = json.dumps(cv_facts.get("experience", [])[:3], indent=2)  # Top 3 jobs
        cv_education = json.dumps(cv_facts.get("education", []), indent=2)
        cv_years = cv_facts.get("total_years_experience", 0)
        
        return f"""You are an expert technical recruiter analyzing CV-to-job fit.

JOB POSTING:
Title: {job_data.get('title', 'Unknown')}
Company: {job_data.get('company', 'Unknown')}

REQUIREMENTS:

Must-Have:
{json.dumps(must_have, indent=2)}

Nice-to-Have:
{json.dumps(nice_to_have, indent=2)}

---

CANDIDATE CV:

Summary:
{cv_summary}

Skills:
{cv_skills}

Experience ({cv_years} years total):
{cv_experience}

Education:
{cv_education}

---

ANALYSIS TASK:

Perform a holistic analysis of how well this CV matches the job requirements.

1. REQUIREMENT MATCHING
   For each requirement (must-have and nice-to-have):
   - Determine if CV satisfies it (MATCHED / PARTIAL / NOT_MATCHED)
   - Explain reasoning with specific CV evidence (company, years, technologies)
   - Consider semantic equivalents:
     * Flask ≈ FastAPI (both Python web frameworks)
     * React Native ≈ React (same ecosystem)
     * Python backend ≈ C# backend (transferable skills)
   - Consider years of experience mentioned in requirements (e.g., "3+ years Python")
   - Be generous with "PARTIAL" for transferable skills

2. EDUCATION EVALUATION (STRICT)
   - Check if CV meets degree requirements
   - "equivalent degree" = Associates degree, technical degree, bootcamp certificate
   - "equivalent degree" ≠ work experience (unless job explicitly says "degree OR experience")
   - Examples:
     * 10 years experience ≠ Bachelor's degree (unless job explicitly allows)
     * Bootcamp certificate = may qualify as "equivalent degree" (education-based)
     * Training course alone = NOT a degree equivalent
   - If CV has no formal degree or equivalent educational qualification, qualifications_score should reflect this gap

3. SCORING (0-100 for each category)
   
   **Skills Score:**
   - How well do CV skills match job requirements?
   - Consider:
     * Exact matches (Python → Python requirement) = full credit
     * Semantic matches (Flask → FastAPI requirement) = high credit (80%)
     * Transferable (Python backend → Java backend) = medium credit (60%)
     * Missing with no equivalent = no credit
   - Calculate based on coverage of required skills
   
   **Experience Score:**
   - Does candidate have required years and relevant background?
   - Consider:
     * Years: Does total_years >= required_years?
     * Relevance: Is experience in same/similar domain?
     * Leadership: If management required, does CV show team leadership?
   - 100% if all experience requirements met, scale down proportionally if not
   
   **Qualifications Score:**
   - Does CV meet education/certification requirements?
   - Scoring:
     * Formal degree (Bachelor's/Master's/PhD) = 100%
     * Equivalent degree (Associates, bootcamp, technical degree) = 70-80% (if job allows)
     * Training/courses only = 50-60%
     * No formal education = 30-40%
   - Be strict: work experience does NOT replace degree requirement
   
   **Overall Score:**
   - Holistic assessment of match quality
   - Suggested weighting: 60% skills + 30% experience + 10% qualifications
   - BUT use judgment: if candidate is missing critical must-have, reduce overall score more aggressively

4. GENERATE INSIGHTS
   
   **Strengths (3-5 specific achievements):**
   - Cite specific companies, years, technologies from CV
   - Focus on what matches job requirements
   - Be concrete: "Led team of 5-6 engineers at Microsoft" NOT "Has leadership experience"
   
   **Gaps (list all missing requirements):**
   - What's missing from CV? (both must-have AND nice-to-have)
   - Be factual and direct
   - Include technical skills AND qualifications (like degree)
   
   **Recommendations (3-5 actionable steps):**
   - ONLY recommend practical, achievable actions based on candidate's career stage
   - DO NOT recommend pursuing degrees if candidate has 5+ years experience (too late in career, not worth time/cost)
   - DO recommend:
     * Short-term technical skills that can be learned quickly (e.g., "Learn Apache Spark via Databricks free course (2-3 weeks)", "Build React portfolio project (1-2 months)")
     * Project-based learning to demonstrate missing skills (e.g., "Create GitHub project showcasing X")
   - DO NOT recommend:
     * Long-term education (Bachelor's/Master's) for experienced professionals
     * Certifications UNLESS the job posting EXPLICITLY says "X certification required" or "X certified preferred"
       - Example: If job says "AWS experience", DO NOT suggest "Get AWS certification"
       - Example: If job says "AWS Certified Solutions Architect required", THEN suggest certification
     * Anything that takes >6 months for someone already working full-time
     * "Formalizing" or "validating" existing skills via certifications (if they have experience, no cert needed)
   - Focus on filling must-have technical skill GAPS (missing skills, not existing skills)
   - Be realistic: if gap is unfillable quickly (e.g., "need 5 years Java experience but candidate has 0"), acknowledge it's a deal-breaker rather than giving false hope
   - For education gaps: If candidate has 5+ years experience but no degree, acknowledge the gap but note that "experience may substitute in practice—discuss with recruiter"

---

CRITICAL RULES:
- Use ONLY facts from CV data above (no hallucination!)
- Be specific: mention company names, technologies, years
- Consider semantic similarity (Flask ≈ FastAPI) and transferability (Python → C#)
- **NEVER recommend certifications unless job posting EXPLICITLY requires them**
  * If CV has Azure experience and job says "Azure knowledge" → DO NOT suggest Azure cert
  * If CV lacks Spark and job says "Spark experience preferred" → suggest learning Spark (NOT cert)
  * ONLY suggest cert if job says "AWS Certified" or "Azure certification required"
- Be strict on education: work experience ≠ degree unless job explicitly says "degree OR experience"
- Scores must logically match your reasoning (missing degree → lower qualifications_score)
- Include concrete evidence for every claim
- If CV lacks something, state it clearly in gaps

---

Return JSON with this EXACT structure:

{{
  "overall_score": 85,
  "skills_score": 80,
  "experience_score": 95,
  "qualifications_score": 70,
  
  "matched_must_have": [
    {{
      "requirement": "3+ years Python",
      "status": "MATCHED",
      "evidence": "10 years experience with Python at Deep Instinct (2019-2021) and Microsoft (2021-2025)",
      "cv_fact": "Created scalable systems in Python (Flask, PostgreSQL) at Deep Instinct"
    }}
  ],
  
  "missing_must_have": [
    {{
      "requirement": "Bachelor's degree in CS or equivalent",
      "status": "NOT_MATCHED",
      "evidence": "CV shows training but no Bachelor's degree or equivalent degree (bootcamp, Associates, etc.)",
      "impact": "May not meet minimum education requirement"
    }}
  ],
  
  "matched_nice_to_have": [
    {{
      "requirement": "Azure knowledge",
      "status": "MATCHED",
      "evidence": "Developed C# backend services on Azure Cloud Services at Microsoft (2021-2025)"
    }}
  ],
  
  "missing_nice_to_have": [
    {{
      "requirement": "Experience with Spark",
      "status": "NOT_MATCHED",
      "evidence": "No mention of Apache Spark or big data technologies in CV"
    }}
  ],
  
  "strengths": [
    "10+ years backend engineering experience with Python, C#, and Rust across Microsoft and Deep Instinct",
    "Led team of 5-6 engineers at Microsoft (2021-2025), satisfying 2+ years management requirement",
    "Strong Azure Cloud Services experience at Microsoft, directly matching nice-to-have Azure requirement"
  ],
  
  "gaps": [
    "No Bachelor's degree or equivalent educational qualification - CV shows training only",
    "No experience with big data technologies (Spark, Presto, Trino) listed in nice-to-have requirements",
    "No React experience mentioned in CV"
  ],
  
  "recommendations": [
    "Obtain Bachelor's degree in Computer Science or related field to meet education requirement",
    "Gain hands-on experience with Apache Spark or other big data tools (Presto, Trino)",
    "Consider learning React to add full-stack development capabilities",
    "Obtain Azure certifications (e.g., Azure Administrator) to formalize cloud expertise"
  ],
  
  "reasoning": {{
    "skills_score_explanation": "Strong Python (10 years) and backend expertise matches core requirements. Azure experience matches nice-to-have. Missing some nice-to-have skills (Spark, React) reduces score to 80%.",
    
    "experience_score_explanation": "10 years backend engineering far exceeds 7-year requirement. Led team of 5-6 engineers satisfies 2+ years management requirement. Experience highly relevant to job: 95%.",
    
    "qualifications_score_explanation": "CV shows training but no Bachelor's degree. Job requires 'Bachelor's degree or equivalent degree'. Training alone may not qualify as 'equivalent degree'. Reduced score: 70%.",
    
    "overall_assessment": "Strong candidate with extensive backend engineering and leadership experience. Main concern is lack of formal degree. If company interprets 'equivalent' to include significant experience, candidate is excellent fit. Otherwise, may not meet minimum qualifications. Overall match: 85%."
  }}
}}
"""