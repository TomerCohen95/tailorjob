# CV Matcher v5.0 Implementation Plan

## Overview

Transform the matcher from hybrid (v4.0) to fully AI-driven (v5.0) - zero computation, pure GPT-4 reasoning.

**Goal:** Replace 7 stages (3 AI + 4 computation) with 2 AI stages (extraction + analysis)

---

## Phase 1: Core Implementation

### Step 1.1: Update Configuration

**File:** `backend/.env`

Add GPT-4 deployment config:
```env
# Azure OpenAI deployments
AZURE_OPENAI_DEPLOYMENT_MINI=gpt-4o-mini
AZURE_OPENAI_DEPLOYMENT_GPT4=gpt-4

# Feature flags
USE_MATCHER_V5=false  # Start disabled
USE_MATCHER_V4=true   # Keep v4.0 as default
```

**File:** `backend/app/config.py`

Add settings:
```python
class Settings(BaseSettings):
    # Existing...
    AZURE_OPENAI_DEPLOYMENT_MINI: str = "gpt-4o-mini"
    AZURE_OPENAI_DEPLOYMENT_GPT4: str = "gpt-4"
    USE_MATCHER_V5: bool = False
    USE_MATCHER_V4: bool = True
```

---

### Step 1.2: Create CV Extractor v5

**File:** `backend/app/services/cv_extractor_v5.py`

**Strategy:** Reuse v4.0 extraction logic (already works well)

```python
"""
CV Extractor v5.0 - Extract structured facts from CV text.
Reuses v4.0 extraction with minor prompt improvements.
"""

from typing import Dict, Any
from openai import AsyncAzureOpenAI
import json

class CVExtractorV5:
    """Extract CV facts using GPT-4o-mini (fast, cheap, accurate)"""
    
    def __init__(self, client: AsyncAzureOpenAI, deployment: str):
        self.client = client
        self.deployment = deployment
        print(f"🔧 Initializing CV Extractor v5.0")
        print(f"   Deployment: {deployment}")
    
    async def extract_facts(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract structured facts from CV text.
        Uses GPT-4o-mini with temperature 0.0 for zero hallucination.
        """
        prompt = self._build_extraction_prompt(cv_text)
        
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # Zero hallucination
            response_format={"type": "json_object"}
        )
        
        facts = json.loads(response.choices[0].message.content)
        print(f"✅ Extracted: {len(facts.get('skills', {}).get('languages', []))} skills, "
              f"{len(facts.get('experience', []))} jobs, "
              f"{facts.get('total_years_experience', 0)} total years")
        
        return facts
    
    def _build_extraction_prompt(self, cv_text: str) -> str:
        """Build extraction prompt (reuse v4.0 prompt)"""
        return f"""Extract factual information from this CV. Return ONLY facts present in the text.

CV TEXT:
{cv_text}

Return JSON with this exact structure:
{{
  "summary": "brief professional summary",
  "skills": {{
    "languages": ["Python", "C#"],
    "frameworks": ["Flask", "FastAPI"],
    "tools": ["Azure", "Jenkins"],
    "soft_skills": ["Leadership", "Mentorship"]
  }},
  "experience": [
    {{
      "title": "Senior Software Engineer",
      "company": "Microsoft",
      "period": "2021-2025",
      "years": 4,
      "description": ["Led team of 5-6 engineers", "Designed security agent"],
      "technologies": ["Rust", "C#", "Azure"]
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
  "certifications": ["AWS Certified Solutions Architect"],
  "total_years_experience": 10
}}

CRITICAL RULES:
- Extract ONLY information explicitly stated in CV
- Do NOT infer or assume qualifications
- Be precise with years, titles, companies
- If education is training/bootcamp (not degree), mark degree as "Training" or "Bootcamp"
- Calculate total_years_experience from experience dates
- List ALL technologies mentioned in experience descriptions
"""
```

---

### Step 1.3: Create CV Matcher v5 (The Core)

**File:** `backend/app/services/cv_matcher_v5.py`

**This is where the magic happens** - single GPT-4 call does everything!

```python
"""
CV Matcher v5.0 - Fully AI-driven matching with GPT-4.
No computation, no formulas - just pure AI reasoning.
"""

from typing import Dict, Any
from openai import AsyncAzureOpenAI
import json
from datetime import datetime

class CVMatcherV5:
    """
    Fully AI-driven CV matcher using GPT-4.
    Single prompt handles comparison, scoring, and explanation.
    """
    
    def __init__(
        self,
        extractor,
        gpt4_client: AsyncAzureOpenAI,
        gpt4_deployment: str
    ):
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
        
        Returns:
            Complete analysis with scores, matches, gaps, explanations
        """
        print("\n" + "="*60)
        print(f"🎯 [v5.0] Analyzing CV match for job: {job_data.get('title', 'Unknown')}")
        print("="*60)
        
        try:
            # Stage 1: Extract CV facts (GPT-4o-mini)
            print(f"📄 Extracting facts from CV ({len(cv_text)} chars)")
            cv_facts = await self.extractor.extract_facts(cv_text)
            
            # Stage 2: Analyze match (GPT-4)
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
        required = ["overall_score", "skills_score", "experience_score", "qualifications_score"]
        for field in required:
            if field not in analysis:
                raise ValueError(f"GPT-4 response missing required field: {field}")
        
        return analysis
    
    def _build_analysis_prompt(
        self,
        cv_facts: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive analysis prompt for GPT-4.
        This is THE prompt that does everything!
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
     * Python backend ≈ C# backend (transferable)
   - Consider years of experience for skill requirements
   - Be generous with "PARTIAL" for transferable skills

2. EDUCATION EVALUATION (STRICT)
   - Check if CV meets degree requirements
   - "equivalent degree" = Associates, technical degree, bootcamp certificate
   - "equivalent degree" ≠ work experience (unless job explicitly says "degree OR experience")
   - Examples:
     * 10 years experience ≠ Bachelor's degree (unless job allows)
     * Bootcamp certificate = may qualify as "equivalent degree"
     * Training course = NOT a degree equivalent
   - If CV has no degree, qualifications_score should reflect this

3. SCORING (0-100 for each category)
   
   **Skills Score:**
   - How well do CV skills match job requirements?
   - Consider:
     * Exact matches (Python → Python) = 100% contribution
     * Semantic matches (Flask → FastAPI) = 80% contribution
     * Transferable (Python backend → Java backend) = 60% contribution
     * Missing with no equivalent = 0% contribution
   - Formula: (total_match_value / total_requirements) * 100
   
   **Experience Score:**
   - Does candidate have required years and relevant background?
   - Consider:
     * Years: Does cv_years >= required_years?
     * Relevance: Is experience in same domain?
     * Leadership: If management required, does CV show leadership?
   - 100% if all requirements met, scale down proportionally
   
   **Qualifications Score:**
   - Does CV meet education/certification requirements?
   - Consider:
     * Formal degree (Bachelor's+) = 100%
     * Equivalent degree (Associates, bootcamp) = 70-80% (if job allows)
     * Training only = 50-60%
     * No education = 30-40%
   - Be strict: work experience does NOT replace degree
   
   **Overall Score:**
   - Holistic assessment: How good is this match?
   - Weight: 60% skills + 30% experience + 10% qualifications
   - But use judgment: if candidate is missing critical must-have, lower overall score

4. GENERATE INSIGHTS
   
   **Strengths (3-5 specific achievements):**
   - Mention company names, years, technologies
   - Focus on matches to job requirements
   - Be concrete: "Led team of 5-6 engineers at Microsoft" not "Has leadership experience"
   
   **Gaps (both must-have and nice-to-have):**
   - What's missing from CV?
   - Be factual and direct
   - Include both technical skills and qualifications
   
   **Recommendations (3-5 actionable steps):**
   - Specific actions to improve match
   - Examples: "Obtain certification in X", "Gain experience with Y"
   - Prioritize must-have gaps first

---

CRITICAL RULES:
- Use ONLY facts from CV data above (no hallucination)
- Be specific: include company names, technologies, years
- Consider semantic similarity and transferability
- Be strict on education: experience ≠ degree unless job explicitly allows
- Scores must reflect reasoning (missing degree → lower qualifications score)
- Include evidence for every claim
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
      "evidence": "CV shows training but no Bachelor's degree or equivalent degree",
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
    "Led team of 5-6 engineers at Microsoft (2021-2025), satisfying management requirement",
    "Strong Azure Cloud Services experience, directly matching nice-to-have Azure requirement"
  ],
  
  "gaps": [
    "No Bachelor's degree (CV shows training only) - may not meet education requirement",
    "No experience with big data technologies (Spark, Presto, Trino) listed in nice-to-have",
    "No React experience mentioned"
  ],
  
  "recommendations": [
    "Obtain Bachelor's degree in Computer Science or verify if job accepts equivalent experience",
    "Gain hands-on experience with Apache Spark or similar big data tools",
    "Consider learning React to add full-stack capabilities",
    "Obtain Azure certifications to formalize cloud expertise"
  ],
  
  "reasoning": {{
    "skills_score_explanation": "Strong Python (10 years) and backend expertise matches core requirements. Azure experience matches nice-to-have. Missing Spark and React reduces score to 80%.",
    
    "experience_score_explanation": "10 years backend engineering exceeds 7-year requirement. Led team of 5-6 engineers satisfies 2+ years management. Highly relevant experience: 95%.",
    
    "qualifications_score_explanation": "CV shows training but no Bachelor's degree. Job requires 'Bachelor's degree or equivalent degree'. Training may not qualify as 'equivalent degree'. Score: 70% (reduced due to education gap).",
    
    "overall_assessment": "Strong candidate with extensive backend and leadership experience. Main concern is lack of formal degree. If company interprets 'equivalent' broadly (accepts experience), candidate is excellent fit. Otherwise, may not meet minimum qualifications. Match: 85%."
  }}
}}
"""
```

---

### Step 1.4: Update API Endpoint

**File:** `backend/app/api/routes/matching.py`

Add v5.0 routing:

```python
from app.services.cv_matcher_v5 import CVMatcherV5
from app.services.cv_extractor_v5 import CVExtractorV5

# Initialize v5.0 services (if enabled)
cv_matcher_v5 = None
if settings.USE_MATCHER_V5:
    gpt4_client = AsyncAzureOpenAI(
        api_key=settings.AZURE_OPENAI_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
    )
    
    extractor_v5 = CVExtractorV5(
        client=gpt4_client,
        deployment=settings.AZURE_OPENAI_DEPLOYMENT_MINI
    )
    
    cv_matcher_v5 = CVMatcherV5(
        extractor=extractor_v5,
        gpt4_client=gpt4_client,
        gpt4_deployment=settings.AZURE_OPENAI_DEPLOYMENT_GPT4
    )

@router.post("/analyze")
async def analyze_cv_job_match(...):
    """Analyze CV-to-job match using latest matcher version"""
    
    # Route to v5.0 if enabled
    if settings.USE_MATCHER_V5 and cv_matcher_v5:
        print("🚀 Using Matcher v5.0 (Fully AI-Driven with GPT-4)")
        analysis = await cv_matcher_v5.analyze_match(cv_text, job)
    # Fallback to v4.0
    elif settings.USE_MATCHER_V4 and cv_matcher_v4:
        print("🚀 Using Matcher v4.0 (Hybrid)")
        analysis = await cv_matcher_v4.analyze_match(cv_text, job)
    else:
        # v3.0 fallback
        ...
```

---

## Phase 2: Testing & Validation

### Step 2.1: Unit Tests

**File:** `backend/tests/test_cv_matcher_v5.py`

Test v5.0 with known CV/job pairs:

```python
import pytest
from app.services.cv_matcher_v5 import CVMatcherV5

@pytest.mark.asyncio
async def test_v5_degree_strict_interpretation():
    """Test that v5.0 correctly penalizes missing degree"""
    # CV with 10 years experience but no degree
    cv_text = "..."
    
    # Job requiring "Bachelor's degree or equivalent"
    job = {...}
    
    analysis = await matcher_v5.analyze_match(cv_text, job)
    
    # Should have low qualifications score (not 100%)
    assert analysis["qualifications_score"] < 100
    assert analysis["qualifications_score"] >= 50  # Has training
    
    # Should mention degree in missing requirements
    assert any("degree" in m["requirement"].lower() 
               for m in analysis["missing_must_have"])

@pytest.mark.asyncio
async def test_v5_semantic_matching():
    """Test that v5.0 recognizes Flask ≈ FastAPI"""
    cv_text = "... Flask experience ..."
    job = {"requirements_matrix": {"must_have": ["FastAPI experience"]}}
    
    analysis = await matcher_v5.analyze_match(cv_text, job)
    
    # Should recognize Flask as partial match for FastAPI
    assert analysis["skills_score"] > 50  # Partial credit
```

### Step 2.2: Comparison Testing

**File:** `backend/scripts/compare_v4_v5.py`

Compare v4.0 vs v5.0 on same data:

```python
"""Compare v4.0 (hybrid) vs v5.0 (full AI) results"""

async def compare_matchers():
    cv_text = load_test_cv()
    job = load_test_job()
    
    # Run both matchers
    v4_result = await matcher_v4.analyze_match(cv_text, job)
    v5_result = await matcher_v5.analyze_match(cv_text, job)
    
    print("\n" + "="*60)
    print("V4.0 (Hybrid) vs V5.0 (Full AI) Comparison")
    print("="*60)
    
    print(f"\nOverall Score:")
    print(f"  v4.0: {v4_result['overall_score']}%")
    print(f"  v5.0: {v5_result['overall_score']}%")
    print(f"  Diff: {v5_result['overall_score'] - v4_result['overall_score']:+}%")
    
    print(f"\nQualifications Score (key metric):")
    print(f"  v4.0: {v4_result['qualifications_score']}%")
    print(f"  v5.0: {v5_result['qualifications_score']}%")
    
    print(f"\nMissing Must-Have:")
    print(f"  v4.0: {len(v4_result['missing_must_have'])} items")
    print(f"  v5.0: {len(v5_result['missing_must_have'])} items")
```

---

## Phase 3: Gradual Rollout

### Step 3.1: Feature Flag Rollout

Week 1: Internal testing
```env
USE_MATCHER_V5=true  # Enable for dev/staging
USE_MATCHER_V4=true  # Keep as fallback
```

Week 2: 10% of users
```python
# Route based on user ID hash
if hash(user_id) % 100 < 10:
    use_v5 = True
```

Week 3-4: 50% of users
Week 5+: 100% rollout

### Step 3.2: Monitoring

Track metrics:
- Average response time (v5.0 will be slower due to GPT-4)
- Cost per match (v5.0 will be ~6x more expensive)
- User satisfaction scores
- Error rates

### Step 3.3: Cost Monitoring

```python
# Log cost per match
v5_cost_per_match = (
    gpt4_mini_tokens * gpt4_mini_price +
    gpt4_tokens * gpt4_price
)

print(f"💰 v5.0 match cost: ${v5_cost_per_match:.4f}")
```

---

## Phase 4: Optimization (Post-Launch)

### Step 4.1: Prompt Tuning

- A/B test prompt variations
- Optimize for accuracy vs cost
- Fine-tune temperature settings

### Step 4.2: Model Selection

Consider alternatives:
- GPT-4o instead of GPT-4 (cheaper, faster)
- GPT-4-turbo (faster)
- Claude 3.5 Sonnet (competitive pricing)

### Step 4.3: Caching

Aggressive caching to reduce costs:
```python
# Cache key: hash(cv_text + job_requirements)
cache_key = hashlib.sha256(
    f"{cv_text}{job_requirements}".encode()
).hexdigest()

# Check cache before GPT-4 call
if cached := redis.get(f"v5:match:{cache_key}"):
    return json.loads(cached)
```

---

## Success Criteria

### Accuracy
- ✅ Qualifications score < 100% for CVs without degree
- ✅ All must-have/nice-to-have requirements detected
- ✅ Degree gap mentioned in gaps/recommendations

### Performance
- ⏱️ P95 latency < 10s (acceptable for GPT-4)
- 💰 Cost per match < $0.05 (6x increase acceptable)
- 📈 Error rate < 1%

### User Satisfaction
- ⭐ Average rating ≥ 4.5/5
- 📝 Positive feedback on explanation clarity
- 🎯 Users report more accurate matches

---

## Rollback Plan

If v5.0 issues arise:

1. **Immediate:** Set `USE_MATCHER_V5=false` (instant rollback to v4.0)
2. **Monitor:** Check logs for error patterns
3. **Fix:** Update prompts or code
4. **Re-test:** Validate fixes in staging
5. **Re-deploy:** Gradual rollout again

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: Implementation** | 3 days | Core services, API routing, config |
| **Phase 2: Testing** | 2 days | Unit tests, comparison testing |
| **Phase 3: Rollout** | 4 weeks | 10% → 50% → 100% gradual rollout |
| **Phase 4: Optimization** | Ongoing | Prompt tuning, caching, cost optimization |

**Total:** ~5 weeks to full rollout

---

## Cost Projection

Assuming 1000 matches/day:

**v4.0 current cost:**
- $0.005 per match
- 1000 matches/day = $5/day
- Monthly: ~$150

**v5.0 projected cost:**
- $0.031 per match
- 1000 matches/day = $31/day
- Monthly: ~$930

**Cost increase:** $780/month (+520%)

**Justification:**
- Simpler codebase (80% less code)
- Better accuracy (GPT-4 reasoning)
- Faster iteration (edit prompts, not code)
- Better user experience

---

## Next Steps

1. ✅ Get approval for v5.0 plan
2. Implement `cv_extractor_v5.py` (reuse v4.0)
3. Implement `cv_matcher_v5.py` (single GPT-4 call)
4. Add GPT-4 config to `.env`
5. Test with v4.0 test cases
6. Compare results side-by-side
7. Start gradual rollout (10% → 100%)