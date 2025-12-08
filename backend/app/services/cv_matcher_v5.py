"""
CV Matcher v5.3 - Fully AI-driven matching with GPT-4.
Enhanced with discipline matching, score formula fixes, and CV presentation focus.

Architecture:
1. Extract CV facts (GPT-4o-mini, temp=0.0)
2. Analyze match (GPT-4, temp=0.2) - does EVERYTHING

v5.3 Changes:
- Fixed overall score calculation (0 missing must-haves = base score, no phantom penalties)
- Reduced penalty severity (0: none, 1-2: -5 to -10, 3-4: -15 to -20, 5+: -25 to -35)
- Completely rewrote recommendations to focus on CV presentation improvements
- Recommendations now prioritize highlighting existing experience over learning new skills
- Added explicit instructions to never suggest adding non-existent skills to CV
- Enhanced quantifiable metrics examples (team size, performance improvements, scale metrics)
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
    
    Version: v5.3 - CV Presentation Focus + Score Formula Fix
    """
    
    VERSION = "v5.3"
    VERSION_NAME = "CV Presentation Focus + Score Formula Fix"
    
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
        
        print(f"🔧 Initializing CV Matcher v{self.VERSION} ({self.VERSION_NAME})")
        print(f"   GPT-4 Deployment: {gpt4_deployment}")
        print(f"✅ CV Matcher v{self.VERSION} initialized successfully")
    
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
        print(f"🎯 [v{self.VERSION}] Analyzing CV match for job: {job_data.get('title', 'Unknown')}")
        print("="*60)
        
        try:
            # Stage 1: Extract CV facts (GPT-4o-mini)
            cv_facts = await self.extractor.extract_facts(cv_text)
            
            # Stage 2: Analyze match (GPT-4) - THE MAGIC HAPPENS HERE
            print(f"🧠 Analyzing match with GPT-4 (advanced reasoning)")
            analysis = await self._analyze_with_gpt4(cv_facts, job_data)
            
            # Add metadata
            analysis["analyzed_at"] = datetime.utcnow().isoformat()
            analysis["matcher_version"] = self.VERSION
            analysis["scoring_method"] = "GPT-4 holistic reasoning (no computation)"
            
            print("\n" + "="*60)
            print(f"✅ [v{self.VERSION}] Match analysis complete: {analysis['overall_score']}% match")
            print("="*60 + "\n")
            
            return analysis
            
        except Exception as e:
            print(f"❌ [v{self.VERSION}] Match analysis failed: {str(e)}")
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
        
        # Validate required fields with fallbacks for optional arrays
        required = [
            "overall_score", "skills_score", "experience_score", "qualifications_score",
            "matched_must_have", "missing_must_have",
            "strengths", "gaps", "recommendations"
        ]
        for field in required:
            if field not in analysis:
                raise ValueError(f"GPT-4 response missing required field: {field}")
        
        # Add fallbacks for nice-to-have fields (may be empty if job has no nice-to-haves)
        if "matched_nice_to_have" not in analysis:
            analysis["matched_nice_to_have"] = []
        if "missing_nice_to_have" not in analysis:
            analysis["missing_nice_to_have"] = []
        
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
   - Check if CV meets degree requirements EXACTLY as stated
   - COMPLETED degrees only:
     * "Bachelor's degree" = B.A., B.Sc., B.S., B.Tech (COMPLETED, not in-progress)
     * "In-progress degree" (e.g., "Expected 2027") = NOT a completed degree, score ~60-70%
     * "Master's/PhD in progress" = counts as having Bachelor's (if that was completed)
   - "equivalent degree" evaluation:
     * Associates degree, technical college degree = may qualify as "equivalent"
     * Bootcamp certificate alone = NOT equivalent to Bachelor's degree
     * Training courses alone = NOT equivalent to degree
     * Work experience = NOT equivalent to degree (unless job EXPLICITLY says "degree OR X years experience")
   - Job says "Bachelor's OR equivalent experience":
     * 5+ years relevant experience CAN substitute for degree
     * But if job just says "Bachelor's degree", experience doesn't count
   - If CV lacks completed degree, qualifications_score should reflect the gap proportionally

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
   - CRITICAL: Match the candidate's ROLE/DISCIPLINE to the job's requirements, not just years
   
   Role Matching Principles:
   - Many jobs specify a DISCIPLINE/SPECIALTY (e.g., "DevOps Engineer", "Data Scientist", "Security Engineer", "ML Engineer")
   - Evaluate if CV demonstrates professional work IN THAT DISCIPLINE, not just adjacent or transferable skills
   - Generic "Software Engineer" experience does NOT automatically equal specialized disciplines
   
   Discipline Transferability Guidelines (use judgment, these are examples):
   
   HIGH TRANSFERABILITY (90-100% credit):
   - SRE ↔ DevOps Engineer (functionally equivalent roles)
   - ML Engineer ↔ Data Scientist (overlapping work)
   - Backend Engineer ↔ Backend Developer (same discipline, different title)
   - Cloud Engineer ↔ Infrastructure Engineer (same domain)
   
   MEDIUM TRANSFERABILITY (60-80% credit):
   - Platform Engineer → DevOps Engineer (adjacent, some overlap)
   - Full-Stack Engineer → Backend Engineer (partial specialization)
   - Data Engineer → Data Scientist (same domain, different focus)
   - Security Engineer → DevOps Engineer (if security + infrastructure work shown)
   
   LOW TRANSFERABILITY (30-50% credit):
   - Software Engineer → DevOps Engineer (different discipline, career pivot)
   - Backend Engineer → Data Engineer (different domains)
   - Frontend Engineer → Backend Engineer (different tech stack)
   - QA Engineer → DevOps Engineer (different focus areas)
   
   MINIMAL TRANSFERABILITY (10-30% credit):
   - Frontend Engineer → Infrastructure Engineer (minimal overlap)
   - Mobile Engineer → Backend Engineer (different platforms)
   - Any discipline → completely unrelated discipline
   
   Scoring Formula:
   1. Determine discipline match level (high/medium/low/minimal)
   2. Check if years requirement is met
   3. Final score = (discipline_match_%) × (years_adequacy_%)
   
   Examples:
   - 8 years SRE, job needs 5 years DevOps = 95% (high transfer + exceeds years)
   - 8 years SWE, job needs 5 years DevOps = 35% (low transfer despite years)
   - 3 years DevOps, job needs 5 years DevOps = 60% (exact match but insufficient years)
   - 10 years SWE with some DevOps projects, job needs 5 years DevOps = 45% (partial experience)
   
   Leadership: If job requires people management, verify CV shows explicit team lead/manager role
   
   **Qualifications Score:**
   - Does CV meet education/certification requirements?
   - Scoring guidelines:
     * COMPLETED Bachelor's/Master's/PhD in relevant field = 100%
     * In-progress Bachelor's (expected graduation) = 60-70% (not yet completed)
     * Completed Associates or technical college degree = 70-80% (only if job accepts "equivalent")
     * Bootcamp certificate + some experience = 50-60%
     * Training courses only = 40-50%
     * No formal education = 20-40%
   - CRITICAL: Job says "Bachelor's degree" = need completed Bachelor's, not in-progress
   - Work experience does NOT replace degree requirement unless job explicitly says "OR X years experience"
   - For jobs requiring specific degrees (CS, Engineering): in-progress degree in correct field scores higher than completed degree in unrelated field
   
   **Overall Score:**
   - Calculate using multi-step process with must-have penalty
   
   Step 1: Calculate Base Score
   - Base = (skills_score × 0.6) + (experience_score × 0.3) + (qualifications_score × 0.1)
   - ALWAYS show this calculation explicitly in reasoning section
   
   Step 2: Count Missing Must-Haves
   - Count how many must-have requirements have status "NOT_MATCHED"
   - missing_count = number of NOT_MATCHED must-haves
   
   Step 3: Apply Must-Have Penalty
   - 0 missing: No penalty (final = base) ← CRITICAL: overall score MUST equal base score
   - 1-2 missing: Moderate penalty (-5 to -10 points from base)
   - 3-4 missing: Significant penalty (-15 to -20 points from base)
   - 5+ missing: Severe penalty (-25 to -35 points from base, candidate rarely suitable)
   
   Step 4: Apply Discipline Mismatch Cap (if applicable)
   - Evaluate the degree of discipline mismatch between CV and job:
     * Minor mismatch (adjacent roles, high skill overlap) → cap at 55-65%
     * Moderate mismatch (different specialties, some transferable skills) → cap at 40-55%
     * Major mismatch (unrelated disciplines, minimal skill overlap) → cap at 25-40%
   - Consider: role type, tech stack overlap, domain similarity, transferability
   - This cap applies AFTER penalty from Step 3
   - Be stricter when CV shows zero experience in the target discipline's core areas
   
   Final Score Interpretation:
   - 90-100%: Excellent fit, meets all/nearly all requirements
   - 75-89%: Good fit, minor gaps only
   - 60-74%: Acceptable fit, some gaps or discipline mismatch
   - 45-59%: Weak fit, major gaps or significant discipline mismatch
   - 0-44%: Poor fit, should not proceed to interview
   
   CRITICAL: Be consistent - if you identify 5+ missing must-haves, overall score should reflect this severity (typically 45-55% range)

4. GENERATE INSIGHTS
   
   **Strengths (3-5 specific achievements):**
   - Cite specific companies, years, technologies from CV
   - Focus on what matches job requirements
   - Be concrete: "Led team of 5-6 engineers at Microsoft" NOT "Has leadership experience"
   
   **Gaps (list all missing requirements):**
   - What's missing from CV? (both must-have AND nice-to-have)
   - Be factual and direct
   - Include technical skills AND qualifications (like degree)
   - If significant discipline/role mismatch exists, state it explicitly as a gap
   - Group missing items by category when helpful (languages, tools, domains, experience areas)
   
   **Recommendations (3-5 actionable steps):**
   - Focus on CV PRESENTATION improvements that can be done immediately (same day)
   - Recommendations should help highlight existing experience that matches job requirements
   - Be specific and reference actual CV content when applicable
   
   PRIORITIZE CV PRESENTATION IMPROVEMENTS:
   1. "Highlight [existing but understated skill/experience] more prominently in CV summary"
   2. "Add quantifiable metrics to [existing role] - e.g.:"
      - "Led team of X engineers"
      - "Improved [metric] by X%"
      - "Reduced latency from X to Y"
      - "Scaled system from X to Y users/customers"
      - "Processed X events per second"
      - "Managed budget of $X"
   3. "Expand [brief experience mention] with specific technologies/projects used"
   4. "Emphasize [transferable experience] as it relates to [job requirement]"
   5. "Add [existing but unlisted skill] to skills section if you have experience with it"
   
   APPLICATION STRATEGY IMPROVEMENTS:
   1. "In cover letter, emphasize [matching strength] which directly addresses [requirement]"
   2. "Highlight [similar technology/experience] as equivalent to [required technology]"
   3. "Reach out to hiring manager mentioning [specific matching experience]"
   
   ONLY IF MAJOR GAPS EXIST:
   - For discipline mismatch: "This role requires X discipline. Consider targeting [more aligned role type] positions"
   - For degree gap with experience: "Note: some companies accept experience in lieu of degree—discuss with recruiter"
   - For in-progress education: "Complete degree to strengthen qualifications for future applications"
   
   NEVER RECOMMEND:
   - "Learn [technology]" - not actionable for immediate CV submission
   - Building projects or GitHub repos - takes too long for bulk applications
   - Getting certifications (unless job explicitly requires them)
   - Pursuing degrees for candidates with 3+ years experience
   - Adding skills to CV that candidate doesn't actually have
   
   EXAMPLES OF GOOD RECOMMENDATIONS:
   ✅ "Highlight Python projects in your experience section if you have them - job requires 2+ years Python"
   ✅ "Add team size metrics to your Team Lead role (e.g., 'Led team of 6-8 engineers') to strengthen leadership evidence"
   ✅ "Add quantifiable impact to Windows Internals work (e.g., 'Improved event processing by 40%' or 'Reduced crash rate by 25%')"
   ✅ "Expand C++ experience section with specific frameworks/libraries used (job mentions modern C++)"
   ✅ "Emphasize C# backend work as it demonstrates backend expertise similar to required Java experience"
   ✅ "Add scale metrics to infrastructure work (e.g., 'Scaled from 100K to 2M daily users')"
   
   EXAMPLES OF BAD RECOMMENDATIONS:
   ❌ "Learn AWS through online courses" - not CV-worthy quickly
   ❌ "Get AWS certification" - takes months, not applicable
   ❌ "Build a portfolio project in React" - too time-consuming
   ❌ "Add Python to your skills section" - don't lie if you don't have experience
   
   LEGACY EXAMPLES (DO NOT USE - kept for reference only):
   - Missing Spark → "Learn Apache Spark via Databricks Community Edition (2-3 weeks)" ❌ BAD
   - Missing React → "Build a React portfolio project showcasing frontend skills (1-2 months)" ❌ BAD
   - Has Azure experience, job wants Azure → DO NOT suggest Azure certification ✅ CORRECT
   - In-progress CS degree → "Complete Bachelor's degree to meet formal education requirement" ✅ CORRECT
   - 10 years exp, no degree → "Job requires degree. With your experience, discuss waiver with recruiter." ✅ CORRECT

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
    "Job requires Bachelor's degree, but with 10+ years experience, discuss experience-based waiver with recruiter",
    "Learn Apache Spark via Databricks Community Edition (2-3 weeks) to match nice-to-have big data requirement",
    "Build React portfolio project (1-2 months) to demonstrate frontend capabilities if interested in full-stack roles"
  ],
  
  "reasoning": {{
    "skills_score_explanation": "Strong Python (10 years) and backend expertise matches core requirements. Azure experience matches nice-to-have. Missing some nice-to-have skills (Spark, React) reduces score to 80%.",
    
    "experience_score_explanation": "10 years backend engineering far exceeds 7-year requirement. Led team of 5-6 engineers satisfies 2+ years management requirement. Experience highly relevant to job: 95%.",
    
    "qualifications_score_explanation": "CV shows training but no Bachelor's degree. Job requires 'Bachelor's degree or equivalent degree'. Training alone does not qualify as 'equivalent degree'. However, 10+ years of professional experience may be considered by some employers. Score: 70% (acknowledging education gap but significant experience).",
    
    "overall_assessment": "Strong candidate with extensive backend engineering and leadership experience. Main concern is lack of formal degree. If company interprets 'equivalent' to include significant experience, candidate is excellent fit. Otherwise, may not meet minimum qualifications. Overall match: 85%."
  }}
}}
"""