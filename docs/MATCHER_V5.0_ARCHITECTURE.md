# CV Matcher v5.0 Architecture - Fully AI-Driven

## Overview

v5.0 removes ALL computation and math, delegating everything to AI reasoning. GPT-4 handles complex analysis (comparison, scoring), while GPT-4o-mini handles simple tasks (extraction).

**Design Philosophy:**
- **No code logic** - AI handles all matching, scoring, and reasoning
- **Prompt-driven** - Each stage is a carefully crafted prompt
- **GPT-4 for reasoning** - Complex semantic understanding
- **GPT-4o-mini for extraction** - Fast, cost-effective fact extraction

---

## Architecture: Pure AI Pipeline

```
CV Text + Job Requirements
          ↓
    [1] Extract Facts (GPT-4o-mini, temp=0.0)
          ↓
    CV Facts (JSON) + Job Requirements (JSON)
          ↓
    [2] Analyze Match (GPT-4, temp=0.2)
          ↓
    Match Analysis (JSON with scores, matches, gaps, explanations)
```

**Total Stages:** 2  
**Total API Calls:** 2  
**Computation:** 0 (none!)

---

## Stage 1: Fact Extraction (GPT-4o-mini)

**Purpose:** Extract structured facts from unstructured CV text  
**Model:** GPT-4o-mini (fast, cheap, accurate for extraction)  
**Temperature:** 0.0 (zero hallucination)

### Input
- CV text (string)

### Prompt
```
Extract factual information from this CV. Return ONLY facts present in the text.

CV TEXT:
{cv_text}

Return JSON:
{
  "summary": "brief professional summary",
  "skills": {
    "languages": ["Python", "C#"],
    "frameworks": ["Flask", "FastAPI"],
    "tools": ["Azure", "Jenkins"],
    "soft_skills": ["Leadership", "Mentorship"]
  },
  "experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Microsoft",
      "period": "2021-2025",
      "years": 4,
      "description": ["Led team...", "Designed..."],
      "technologies": ["Rust", "C#", "Azure"]
    }
  ],
  "education": [
    {
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "institution": "MIT",
      "year": "2015"
    }
  ],
  "certifications": ["AWS Certified", "..."],
  "total_years_experience": 10
}

RULES:
- Extract ONLY information explicitly stated in CV
- Do NOT infer or assume qualifications
- Be precise with years, titles, companies
- If education is training/bootcamp, mark as such
```

### Output
Structured CV facts (JSON)

---

## Stage 2: Match Analysis (GPT-4)

**Purpose:** Holistic CV-to-job matching with reasoning  
**Model:** GPT-4 (advanced reasoning, semantic understanding)  
**Temperature:** 0.2 (mostly deterministic, slight creativity for explanations)

### Input
- CV facts (from Stage 1)
- Job requirements (structured JSON)

### Prompt
```
You are an expert technical recruiter analyzing CV-to-job fit.

JOB POSTING:
Title: {job_title}
Company: {company}

REQUIREMENTS:
Must-Have:
{must_have_requirements}

Nice-to-Have:
{nice_to_have_requirements}

CANDIDATE CV:
Summary: {cv_summary}

Skills:
{cv_skills}

Experience ({cv_total_years} years):
{cv_experience}

Education:
{cv_education}

---

ANALYSIS TASK:

1. REQUIREMENT MATCHING
   For each requirement (must-have and nice-to-have):
   - Determine if CV satisfies it (YES/NO/PARTIAL)
   - Explain reasoning with specific CV evidence
   - Consider semantic equivalents (e.g., Flask ≈ FastAPI)
   - Consider transferable skills (e.g., backend Python → backend Java)

2. EDUCATION EVALUATION
   - Check if CV meets degree requirements
   - "equivalent degree" = Associates, bootcamp, technical certification (NOT experience)
   - "equivalent experience" ONLY if job explicitly says "degree OR experience"
   - Be strict: 10 years experience ≠ Bachelor's degree (unless job allows)

3. SCORING (0-100 for each)
   - Skills Score: How well do CV skills match job requirements?
   - Experience Score: Does candidate have required years and relevant background?
   - Qualifications Score: Does CV meet education/certification requirements?
   - Overall Score: Holistic assessment of fit

4. GENERATE INSIGHTS
   - Strengths: 3-5 specific CV achievements matching job needs
   - Gaps: What's missing (both must-have and nice-to-have)
   - Recommendations: 3-5 actionable steps to improve match

---

CRITICAL RULES:
- Use ONLY facts from CV data above (no hallucination)
- Be specific: mention company names, technologies, years
- Consider semantic similarity (React Native ≈ React, Flask ≈ FastAPI)
- Consider transferability (Python backend → C# backend = high)
- Strict education: experience ≠ degree unless job explicitly allows
- Scores must reflect reasoning (if missing degree, qualifications score < 100)
- Include evidence for every claim

Return JSON:
{
  "overall_score": 85,
  "skills_score": 80,
  "experience_score": 95,
  "qualifications_score": 70,
  
  "matched_must_have": [
    {
      "requirement": "3+ years Python",
      "status": "MATCHED",
      "evidence": "10 years experience including Python at Deep Instinct (2019-2021) and Microsoft (2021-2025)",
      "cv_fact": "Created scalable systems in Python (Flask, PostgreSQL) at Deep Instinct"
    }
  ],
  
  "missing_must_have": [
    {
      "requirement": "Bachelor's degree in CS or equivalent",
      "status": "NOT_MATCHED",
      "evidence": "CV shows training but no Bachelor's degree",
      "impact": "May be disqualified unless job accepts experience as equivalent"
    }
  ],
  
  "matched_nice_to_have": [
    {
      "requirement": "Azure knowledge",
      "status": "MATCHED",
      "evidence": "Developed C# backend services on Azure Cloud Services at Microsoft (2021-2025)"
    }
  ],
  
  "missing_nice_to_have": [
    {
      "requirement": "Experience with Spark",
      "status": "NOT_MATCHED",
      "evidence": "No mention of Apache Spark or big data technologies in CV"
    }
  ],
  
  "strengths": [
    "10+ years backend engineering experience with Python, C#, and Rust",
    "Led team of 5-6 engineers at Microsoft, matching '2+ years management' requirement",
    "Strong Azure Cloud Services experience, directly matching nice-to-have requirement"
  ],
  
  "gaps": [
    "No Bachelor's degree (CV shows training only) - may not meet education requirement",
    "No experience with big data technologies (Spark, Presto, Trino)",
    "No React or front-end development experience"
  ],
  
  "recommendations": [
    "Obtain Bachelor's degree in Computer Science or related field, or highlight if job accepts equivalent experience",
    "Gain hands-on experience with Apache Spark or similar big data technologies",
    "Consider learning React to add full-stack capabilities",
    "Obtain Azure certifications to formalize cloud expertise"
  ],
  
  "reasoning": {
    "skills_score_explanation": "Strong Python (10 years) and backend expertise. Azure experience matches nice-to-have. Missing some nice-to-have skills (Spark, React) reduces score to 80%.",
    
    "experience_score_explanation": "10 years backend engineering exceeds 7-year requirement. Led team of 5-6 engineers satisfies management requirement. Score: 95%.",
    
    "qualifications_score_explanation": "CV shows training but no Bachelor's degree. Job requires 'Bachelor's degree or equivalent degree' - training may not qualify unless job interprets 'equivalent' broadly. Score: 70% (reduced due to education gap).",
    
    "overall_assessment": "Strong candidate with extensive backend experience and leadership. Main concern is lack of formal degree. If company accepts equivalent experience, candidate is excellent fit (85% match)."
  }
}
```

### Output
Complete match analysis with scores, matched/missing requirements, strengths, gaps, and recommendations

---

## Model Selection Strategy

| Stage | Model | Reason | Temp | Cost |
|-------|-------|--------|------|------|
| **Extract** | GPT-4o-mini | Fast extraction, low cost, accurate | 0.0 | $ |
| **Analyze** | GPT-4 | Complex reasoning, semantic understanding, holistic scoring | 0.2 | $$$ |

**Cost Optimization:**
- Use cheap GPT-4o-mini for simple extraction
- Use expensive GPT-4 only for complex reasoning
- Single GPT-4 call replaces 5+ v4.0 stages

---

## Benefits of v5.0

### ✅ Simplicity
- No computation code to maintain
- No scoring formulas to tune
- No normalization logic
- Just 2 prompts + API calls

### ✅ Intelligence
- GPT-4 understands semantic equivalents (Flask ≈ FastAPI)
- Understands transferability (backend Python → backend C#)
- Holistic reasoning (not just keyword matching)
- Contextual scoring (considers overall fit, not just math)

### ✅ Flexibility
- Easy to adjust behavior (edit prompt, not code)
- No need to handle edge cases in code
- AI adapts to new requirements naturally

### ✅ Accuracy
- Advanced reasoning for complex cases
- Considers context and nuance
- Explains every decision with evidence

---

## Comparison: v4.0 vs v5.0

| Aspect | v4.0 (Hybrid) | v5.0 (Full AI) |
|--------|---------------|----------------|
| **Stages** | 7 (3 AI + 4 computation) | 2 (both AI) |
| **API Calls** | 3 (gpt-4o-mini only) | 2 (1 mini + 1 GPT-4) |
| **Computation** | Normalization, comparison, scoring | None |
| **Code Complexity** | ~1500 lines across 8 files | ~300 lines (2 services) |
| **Flexibility** | Edit code for changes | Edit prompt for changes |
| **Reasoning** | Limited (rule-based) | Advanced (GPT-4) |
| **Cost per match** | ~$0.005 | ~$0.03 (GPT-4 is 6x more) |
| **Speed** | Fast (minimal AI calls) | Slower (GPT-4 latency) |

---

## Implementation Files

### Core Services (2 files)

1. **`backend/app/services/cv_extractor_v5.py`**
   - Extract CV facts using GPT-4o-mini
   - Temperature: 0.0
   - Output: Structured JSON

2. **`backend/app/services/cv_matcher_v5.py`**
   - Analyze match using GPT-4
   - Temperature: 0.2
   - Output: Complete analysis with scores

### Configuration

**`backend/.env`**
```env
# Model selection
AZURE_OPENAI_DEPLOYMENT_MINI=gpt-4o-mini
AZURE_OPENAI_DEPLOYMENT_GPT4=gpt-4

# Feature flags
USE_MATCHER_V5=true
USE_MATCHER_V4=false
```

---

## Migration Path

### Phase 1: Implement v5.0 (parallel to v4.0)
- Create `cv_extractor_v5.py` (reuse v4.0 extraction logic)
- Create `cv_matcher_v5.py` (single GPT-4 call)
- Add GPT-4 deployment config
- Add `USE_MATCHER_V5` flag

### Phase 2: A/B Testing
- Run both v4.0 and v5.0 on same CV/job pairs
- Compare results, accuracy, cost, speed
- Collect user feedback

### Phase 3: Gradual Rollout
- Enable v5.0 for 10% of users
- Monitor performance, cost, accuracy
- Increase to 50%, then 100%

### Phase 4: Deprecate v4.0
- Remove computation-based services
- Keep v4.0 code as fallback (1 month)
- Full v5.0 rollout

---

## Cost Analysis

### v4.0 Hybrid (current)
- GPT-4o-mini extraction: $0.001
- GPT-4o-mini transferability: $0.002
- GPT-4o-mini explanation: $0.002
- **Total:** ~$0.005 per match

### v5.0 Full AI
- GPT-4o-mini extraction: $0.001
- GPT-4 analysis: $0.03
- **Total:** ~$0.031 per match

**Cost increase:** 6x ($0.005 → $0.031)

**Justification:**
- Simpler codebase (300 lines vs 1500 lines)
- Better accuracy (GPT-4 reasoning)
- Easier to maintain (edit prompts, not code)
- Worth the cost for better user experience

---

## Risks & Mitigation

### Risk 1: Higher Cost
**Mitigation:** 
- Use GPT-4o (cheaper than GPT-4) if available
- Cache results aggressively
- Consider batch processing for non-urgent matches

### Risk 2: Slower Response
**Mitigation:**
- GPT-4 has higher latency (~5s vs ~2s)
- Show loading indicators
- Consider streaming responses

### Risk 3: Less Predictable
**Mitigation:**
- Low temperature (0.2) for consistency
- Extensive prompt testing
- Keep v4.0 as fallback

### Risk 4: Hallucination
**Mitigation:**
- Strict prompt rules ("use ONLY CV facts")
- Temperature 0.0 for extraction
- Validation checks on output

---

## Success Metrics

### Accuracy
- % of matches where qualifications score is correct (strict degree interpretation)
- % of matches with all requirements detected

### User Satisfaction
- User ratings of match quality
- Feedback on explanations clarity

### Performance
- Average latency per match
- Cost per match
- API error rate

---

## Next Steps

1. Get approval for v5.0 architecture
2. Implement `cv_extractor_v5.py` (reuse v4.0)
3. Implement `cv_matcher_v5.py` (single GPT-4 prompt)
4. Test with same CV/job data as v4.0
5. Compare results, iterate on prompts
6. A/B test with real users
7. Gradual rollout