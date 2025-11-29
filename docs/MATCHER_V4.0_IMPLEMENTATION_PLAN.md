# CV Matcher v4.0 - Implementation Plan

## Overview

This document provides a step-by-step implementation plan for v4.0, combining:
- Architecture from [`MATCHER_V4.0_ARCHITECTURE.md`](MATCHER_V4.0_ARCHITECTURE.md)
- Improved prompts from [`MATCHER_V4.0_PROMPTS_REVIEW.md`](MATCHER_V4.0_PROMPTS_REVIEW.md)
- Lessons learned from v3.0 issues

**Target**: Production-ready v4.0 in 4 weeks

---

## Phase 1: Foundation (Week 1)

### Goal
Implement extraction layer with zero hallucination

### Tasks

#### 1.1 Create CV Extraction Service
**File**: `backend/app/services/cv_extractor_v4.py`

```python
from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any

class CVExtractorV4:
    """
    Extract structured facts from CV with zero hallucination.
    Uses improved prompt from MATCHER_V4.0_PROMPTS_REVIEW.md
    """
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
    
    async def extract_cv_facts(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract CV facts using improved prompt.
        Returns structured JSON with zero inference.
        """
        prompt = self._build_extraction_prompt(cv_text)
        
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a fact extraction engine. Return only valid JSON with no commentary."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Deterministic
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content.strip()
        return json.loads(result)
    
    def _build_extraction_prompt(self, cv_text: str) -> str:
        """Build extraction prompt from PROMPTS_REVIEW.md"""
        return f"""
You are a CV extraction engine. Extract ONLY factual information with ZERO inference or guessing.

CRITICAL RULES:
1. Extract ONLY text that appears in the CV
2. If something is not explicitly written, return null or []
3. Do NOT infer technologies from job descriptions
4. Do NOT assume experience duration if not stated
5. Do NOT interpret or summarize - extract verbatim

Return valid JSON ONLY:
{{
  "skills": [],
  "languages": [],
  "frameworks": [],
  "cloud_platforms": [],
  "databases": [],
  "tools": [],
  
  "education": [
    {{
      "degree": null,
      "field": null,
      "institution": null,
      "year": null
    }}
  ],
  
  "experience": [
    {{
      "title": "",
      "company": "",
      "start_year": null,
      "end_year": null,
      "duration_years": null,
      "responsibilities": [],
      "technologies": []
    }}
  ],
  
  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": [],
      "url": null
    }}
  ],
  
  "certifications": [
    {{
      "name": "",
      "issuer": null,
      "year": null
    }}
  ],
  
  "years_experience_total": null,
  "seniority_signals": [],
  "domain_expertise": [],
  "soft_skills": []
}}

CV TEXT:
{cv_text}

Return ONLY valid JSON. No markdown, no explanations.
"""
```

**Testing**:
```python
# Test with real CV from test_data/cvs/Tomer Cohen - CV.pdf
cv_text = extract_pdf_text("test_data/cvs/Tomer Cohen - CV.pdf")
extracted = await extractor.extract_cv_facts(cv_text)

# Assertions
assert "Python" in extracted["languages"]
assert "React" not in extracted["frameworks"]  # Not in CV
assert extracted["years_experience_total"] == 10
assert any("Senior" in sig for sig in extracted["seniority_signals"])
```

#### 1.2 Create Skill Normalizer
**File**: `backend/app/services/skill_normalizer.py`

```python
from typing import List, Dict, Any

class SkillNormalizer:
    """
    Normalize skills to canonical names.
    Eliminates semantic drift (React.js vs React vs ReactJS)
    """
    
    SKILL_MAPPINGS = {
        # Languages
        "golang": "go",
        "go lang": "go",
        "javascript": "js",
        "typescript": "ts",
        "node.js": "nodejs",
        "node": "nodejs",
        
        # Frameworks
        "react.js": "react",
        "reactjs": "react",
        "angular.js": "angular",
        "angularjs": "angular",
        "vue.js": "vue",
        "vuejs": "vue",
        
        # Cloud
        "aws": "amazon web services",
        "gcp": "google cloud",
        "azure cloud services": "azure",
        
        # Databases
        "postgres": "postgresql",
        "mongo": "mongodb",
        "mysql": "mysql",
        
        # Tools
        "git": "git",
        "docker": "docker",
        "k8s": "kubernetes",
    }
    
    def normalize_skill(self, skill: str) -> str:
        """Normalize single skill to canonical name"""
        skill_lower = skill.lower().strip()
        return self.SKILL_MAPPINGS.get(skill_lower, skill_lower)
    
    def normalize_cv_data(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all tech fields in CV"""
        normalized = cv_data.copy()
        
        for field in ["skills", "languages", "frameworks", "cloud_platforms", "databases", "tools"]:
            if field in normalized:
                normalized[field] = [self.normalize_skill(s) for s in normalized[field]]
        
        return normalized
    
    def normalize_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all tech fields in job requirements"""
        normalized = job_data.copy()
        
        if "must_have" in normalized:
            if "skills" in normalized["must_have"]:
                normalized["must_have"]["skills"] = [
                    self.normalize_skill(s) for s in normalized["must_have"]["skills"]
                ]
        
        if "nice_to_have" in normalized:
            if "skills" in normalized["nice_to_have"]:
                normalized["nice_to_have"]["skills"] = [
                    self.normalize_skill(s) for s in normalized["nice_to_have"]["skills"]
                ]
        
        return normalized
```

**Testing**:
```python
normalizer = SkillNormalizer()

# Test skill normalization
assert normalizer.normalize_skill("React.js") == "react"
assert normalizer.normalize_skill("ReactJS") == "react"
assert normalizer.normalize_skill("react") == "react"

# Test CV normalization
cv_data = {"skills": ["React.js", "Node.js", "PostgreSQL"]}
normalized = normalizer.normalize_cv_data(cv_data)
assert normalized["skills"] == ["react", "nodejs", "postgresql"]
```

#### 1.3 Success Criteria
- [ ] CV extraction returns valid JSON 100% of time
- [ ] Zero hallucination: extracted data only contains CV text
- [ ] Normalization reduces variants: React.js/ReactJS → react
- [ ] All tests pass

---

## Phase 2: Comparison Engine (Week 2)

### Goal
Implement deterministic comparison with 100% reproducibility

### Tasks

#### 2.1 Create Comparison Service
**File**: `backend/app/services/cv_comparator.py`

```python
from typing import Dict, Any, List, Set

class CVComparator:
    """
    Compare normalized CV vs job requirements using pure set operations.
    Zero AI involvement = 100% reproducible.
    """
    
    def compare_requirements(
        self,
        cv_normalized: Dict[str, Any],
        job_normalized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare CV vs job deterministically.
        Returns match status for each requirement.
        """
        
        # Combine all CV tech into single set
        cv_all_tech = self._get_all_cv_tech(cv_normalized)
        
        # Get job requirements
        job_must_skills = set(job_normalized.get("must_have", {}).get("skills", []))
        job_nice_skills = set(job_normalized.get("nice_to_have", {}).get("skills", []))
        
        # Compare must-have skills
        matched_must = self._compare_skill_set(job_must_skills, cv_all_tech, "must_have")
        missing_must = [
            {"requirement": skill, "status": "NOT_FOUND", "evidence": "Not in CV"}
            for skill in job_must_skills if skill not in cv_all_tech
        ]
        
        # Compare nice-to-have skills
        matched_nice = self._compare_skill_set(job_nice_skills, cv_all_tech, "nice_to_have")
        missing_nice = [
            {"requirement": skill, "status": "NOT_FOUND", "evidence": "Not in CV"}
            for skill in job_nice_skills if skill not in cv_all_tech
        ]
        
        # Compare experience years
        experience_match = self._compare_experience(cv_normalized, job_normalized)
        
        # Compare education
        education_match = self._compare_education(cv_normalized, job_normalized)
        
        # Compare management requirements
        management_match = self._compare_management(cv_normalized, job_normalized)
        
        return {
            "matched_must_have": matched_must,
            "missing_must_have": missing_must,
            "matched_nice_have": matched_nice,
            "missing_nice_have": missing_nice,
            "experience_match": experience_match,
            "education_match": education_match,
            "management_match": management_match
        }
    
    def _get_all_cv_tech(self, cv_data: Dict[str, Any]) -> Set[str]:
        """Combine all tech fields into single set"""
        all_tech = set()
        
        for field in ["skills", "languages", "frameworks", "cloud_platforms", "databases", "tools"]:
            if field in cv_data:
                all_tech.update(cv_data[field])
        
        return all_tech
    
    def _compare_skill_set(
        self,
        required_skills: Set[str],
        cv_skills: Set[str],
        req_type: str
    ) -> List[Dict[str, Any]]:
        """Compare skill sets"""
        matched = []
        
        for skill in required_skills:
            if skill in cv_skills:
                matched.append({
                    "requirement": skill,
                    "status": "EXACT_MATCH",
                    "evidence": f"CV lists: {skill}",
                    "requirement_type": req_type
                })
        
        return matched
    
    def _compare_experience(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare years of experience"""
        cv_years = cv_data.get("years_experience_total", 0) or 0
        job_years = job_data.get("must_have", {}).get("experience_years", 0) or 0
        
        return {
            "requirement": f"{job_years}+ years experience",
            "status": "MET" if cv_years >= job_years else "NOT_MET",
            "evidence": f"CV: {cv_years} years, Required: {job_years} years",
            "cv_years": cv_years,
            "required_years": job_years
        }
    
    def _compare_education(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare education requirements"""
        education_req = job_data.get("must_have", {}).get("education", {})
        required_degree = education_req.get("required")
        or_equivalent = education_req.get("or_equivalent", False)
        
        if not required_degree:
            return {"requirement": "No degree required", "status": "MET", "evidence": "N/A"}
        
        # Check for formal degree
        has_degree = self._has_formal_degree(cv_data.get("education", []))
        cv_years = cv_data.get("years_experience_total", 0) or 0
        
        # Meets via degree OR via experience (if or_equivalent is true)
        meets_requirement = has_degree or (or_equivalent and cv_years >= 5)
        
        if meets_requirement:
            if has_degree:
                evidence = "Has formal degree"
            else:
                evidence = f"Meets 'or equivalent' clause via {cv_years} years experience"
        else:
            evidence = "No formal degree and insufficient experience for equivalent"
        
        return {
            "requirement": required_degree,
            "status": "MET" if meets_requirement else "NOT_MET",
            "evidence": evidence,
            "has_formal_degree": has_degree,
            "or_equivalent_allowed": or_equivalent
        }
    
    def _has_formal_degree(self, education: List[Dict[str, Any]]) -> bool:
        """Check if candidate has bachelor's or higher"""
        degree_keywords = ["bachelor", "b.sc", "b.s.", "bsc", "ba ", "b.a.", "b.tech", "master", "phd", "m.sc", "m.s."]
        
        for edu in education:
            degree = (edu.get("degree") or "").lower()
            if any(kw in degree for kw in degree_keywords):
                return True
        
        return False
    
    def _compare_management(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare management requirements"""
        mgmt_req = job_data.get("management", {})
        mgmt_required = mgmt_req.get("required", False)
        
        if not mgmt_required:
            return {"requirement": "No management required", "status": "MET", "evidence": "N/A"}
        
        # Check for management signals
        seniority_signals = cv_data.get("seniority_signals", [])
        has_mgmt = any(
            "lead" in sig.lower() or "manage" in sig.lower() or "mentor" in sig.lower()
            for sig in seniority_signals
        )
        
        required_team_size = mgmt_req.get("team_size")
        evidence = "Has management/leadership experience" if has_mgmt else "No management signals found"
        
        return {
            "requirement": f"Management experience (team of {required_team_size})" if required_team_size else "Management experience",
            "status": "MET" if has_mgmt else "NOT_MET",
            "evidence": evidence
        }
```

**Testing**:
```python
comparator = CVComparator()

cv_normalized = {
    "skills": ["python", "flask"],
    "languages": ["python"],
    "years_experience_total": 10
}

job_normalized = {
    "must_have": {
        "skills": ["python", "react"],
        "experience_years": 5
    }
}

result = comparator.compare_requirements(cv_normalized, job_normalized)

# Assertions
assert len(result["matched_must_have"]) == 1  # Python matched
assert len(result["missing_must_have"]) == 1  # React missing
assert result["experience_match"]["status"] == "MET"  # 10 >= 5
```

#### 2.2 Success Criteria
- [ ] Comparison is 100% reproducible (same input → same output)
- [ ] All must-have AND nice-to-have requirements checked
- [ ] Education logic handles "or equivalent" correctly
- [ ] Management requirements properly detected
- [ ] All tests pass

---

## Phase 3: Hybrid Scoring (Week 3)

### Goal
Implement base scoring + AI-assisted transferability

### Tasks

#### 3.1 Create Base Scoring Service
**File**: `backend/app/services/base_scorer.py`

```python
from typing import Dict, Any

class BaseScorer:
    """
    Calculate base scores using deterministic rules.
    No AI involvement = 100% reproducible.
    """
    
    def calculate_base_scores(
        self,
        comparison: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate component scores from comparison results.
        Pure math, no AI.
        """
        
        # Skills score (must-have 80%, nice-to-have 20%)
        skills_score = self._calculate_skills_score(comparison)
        
        # Experience score
        experience_score = self._calculate_experience_score(comparison, cv_data, job_data)
        
        # Qualifications score
        qualifications_score = self._calculate_qualifications_score(comparison)
        
        return {
            "skills_score": skills_score,
            "experience_score": experience_score,
            "qualifications_score": qualifications_score,
            "breakdown": {
                "matched_must_count": len(comparison["matched_must_have"]),
                "total_must_count": len(comparison["matched_must_have"]) + len(comparison["missing_must_have"]),
                "matched_nice_count": len(comparison["matched_nice_have"]),
                "total_nice_count": len(comparison["matched_nice_have"]) + len(comparison["missing_nice_have"])
            }
        }
    
    def _calculate_skills_score(self, comparison: Dict[str, Any]) -> int:
        """Calculate skills score from exact matches only"""
        total_must = len(comparison["matched_must_have"]) + len(comparison["missing_must_have"])
        matched_must = len(comparison["matched_must_have"])
        
        total_nice = len(comparison["matched_nice_have"]) + len(comparison["missing_nice_have"])
        matched_nice = len(comparison["matched_nice_have"])
        
        # Must-haves are 80% weight, nice-to-haves are 20%
        must_score = (matched_must / total_must * 100) if total_must > 0 else 100
        nice_score = (matched_nice / total_nice * 100) if total_nice > 0 else 100
        
        return int(must_score * 0.8 + nice_score * 0.2)
    
    def _calculate_experience_score(
        self,
        comparison: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> int:
        """Calculate experience score"""
        cv_years = cv_data.get("years_experience_total", 0) or 0
        job_years = job_data.get("must_have", {}).get("experience_years", 0) or 0
        
        if cv_years >= job_years * 1.5:
            score = 100  # 150%+ of required
        elif cv_years >= job_years:
            score = 90   # Meets requirement
        elif cv_years >= job_years * 0.75:
            score = 70   # Close to requirement
        elif cv_years >= job_years * 0.5:
            score = 50   # Half of requirement
        else:
            score = 30   # Below half
        
        # Seniority bonus
        job_level = (job_data.get("role_level") or "").lower()
        seniority_signals = cv_data.get("seniority_signals", [])
        has_senior = any("senior" in sig.lower() or "lead" in sig.lower() for sig in seniority_signals)
        
        if ("senior" in job_level or "lead" in job_level) and has_senior:
            score = min(100, score + 10)
        
        return int(score)
    
    def _calculate_qualifications_score(self, comparison: Dict[str, Any]) -> int:
        """Calculate qualifications score"""
        education_match = comparison.get("education_match", {})
        
        if education_match.get("status") == "MET":
            return 100
        else:
            return 60  # Some credit for experience
```

#### 3.2 Create Transferability Assessor
**File**: `backend/app/services/transferability_assessor.py`

```python
from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any, List
import asyncio

class TransferabilityAssessor:
    """
    AI-assisted transferability assessment.
    Narrow scope: only rate skill similarity, not overall fit.
    """
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
    
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
        """
        
        # Assess each missing requirement in parallel
        tasks = [
            self._assess_single_requirement(
                cv_skills, req["requirement"], cv_years, cv_domain, job_domain
            )
            for req in missing_requirements
        ]
        
        assessments = await asyncio.gather(*tasks)
        
        return {"assessments": assessments}
    
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
        Uses improved prompt from PROMPTS_REVIEW.md
        """
        
        prompt = self._build_transferability_prompt(
            cv_skills, missing_req, cv_years, cv_domain, job_domain
        )
        
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
        return json.loads(result)
    
    def _build_transferability_prompt(
        self,
        cv_skills: List[str],
        missing_req: str,
        cv_years: int,
        cv_domain: List[str],
        job_domain: str
    ) -> str:
        """Build transferability prompt from PROMPTS_REVIEW.md"""
        return f"""
Rate transferability from 0.0 to 1.0.

CANDIDATE HAS:
{", ".join(cv_skills)}
Years of experience: {cv_years}
Domain: {", ".join(cv_domain)}

MISSING REQUIREMENT: {missing_req}

JOB DOMAIN: {job_domain}

RATING SCALE:
- 1.0 = Same skill different name (React.js vs React)
- 0.8 = Adjacent framework (Angular when needs React)
- 0.7 = Same category (Vue when needs React)
- 0.6 = Same domain different tech (Backend Python → Backend Node.js)
- 0.5 = Senior engineer, learnable skill (10+ years backend → React)
- 0.4 = Loosely related (5 years backend → React)
- 0.3 = Peripheral (Backend → Frontend)
- 0.2 = Minimal overlap
- 0.0 = Unrelated

SPECIAL RULES:
- Senior engineers (10+ years) get +0.1 bonus for learnable frameworks
- Adjacent frameworks (React/Angular/Vue) get minimum 0.7
- Orthogonal domain (backend → frontend) caps at 0.5

Return JSON:
{{
  "requirement": "{missing_req}",
  "transferability_score": 0.0-1.0,
  "reasoning": "Brief explanation",
  "ramp_up_time": "2-4 weeks|1-2 months|3-6 months|6-12 months|Not transferable"
}}

Be consistent. Same input should produce same score ±0.1.
"""
```

#### 3.3 Create Final Scorer
**File**: `backend/app/services/final_scorer.py`

```python
from typing import Dict, Any

class FinalScorer:
    """
    Combine base scores + transferability into final score.
    Formula is deterministic, only transferability ratings vary slightly.
    """
    
    def calculate_final_scores(
        self,
        base_scores: Dict[str, Any],
        transferability: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate final scores using hybrid approach.
        Base scores (deterministic) + Transferability credits (AI-assisted)
        """
        
        # Add transferability credits to skills score
        skills_score = self._calculate_skills_with_transferability(
            base_scores, transferability, comparison
        )
        
        # Experience and qualifications remain from base scores
        experience_score = base_scores["experience_score"]
        qualifications_score = base_scores["qualifications_score"]
        
        # Overall score (weighted average)
        overall_score = int(
            skills_score * 0.5 +
            experience_score * 0.35 +
            qualifications_score * 0.15
        )
        
        return {
            "overall_score": overall_score,
            "skills_score": skills_score,
            "experience_score": experience_score,
            "qualifications_score": qualifications_score,
            "base_skills_score": base_scores["skills_score"],
            "transferability_details": transferability["assessments"],
            "scoring_method": "v4.0 (base + transferability)"
        }
    
    def _calculate_skills_with_transferability(
        self,
        base_scores: Dict[str, Any],
        transferability: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> int:
        """
        Add transferability credits to base skills score.
        Formula: (exact_matches + transferable_credits) / total_requirements * 100
        """
        
        total_must = base_scores["breakdown"]["total_must_count"]
        exact_must = base_scores["breakdown"]["matched_must_count"]
        
        # Calculate transferable credits
        transferable_credit = sum(
            assessment["transferability_score"]
            for assessment in transferability["assessments"]
            if assessment["requirement"] in [r["requirement"] for r in comparison["missing_must_have"]]
        )
        
        # Must-have score with transferability
        must_score = ((exact_must + transferable_credit) / total_must * 100) if total_must > 0 else 100
        
        # Nice-to-have score (no transferability for now, optional feature)
        total_nice = base_scores["breakdown"]["total_nice_count"]
        exact_nice = base_scores["breakdown"]["matched_nice_count"]
        nice_score = (exact_nice / total_nice * 100) if total_nice > 0 else 100
        
        # Weighted combination (80% must, 20% nice)
        return int(must_score * 0.8 + nice_score * 0.2)
```

#### 3.4 Success Criteria
- [ ] Base scores are 100% reproducible
- [ ] Transferability assessments are realistic (Angular → React = 0.7-0.9)
- [ ] Final score formula is transparent and tunable
- [ ] Transferability assessments are consistent (±0.1 variance)
- [ ] All tests pass

---

## Phase 4: Explanation Generator (Week 4)

### Goal
Generate human-readable explanations grounded in extracted facts

### Tasks

#### 4.1 Create Explanation Service
**File**: `backend/app/services/explanation_generator.py`

```python
from openai import AsyncAzureOpenAI
from app.config import settings
import json
from typing import Dict, Any, List

class ExplanationGenerator:
    """
    Generate explanations based ONLY on extracted data.
    No hallucination - AI is constrained to provided facts.
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
        Uses improved prompt from PROMPTS_REVIEW.md
        """
        
        prompt = self._build_explanation_prompt(
            cv_data, job_data, comparison, transferability, scores
        )
        
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a CV consultant. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # More creative for recommendations
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content.strip()
        return json.loads(result)
    
    def _build_explanation_prompt(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        comparison: Dict[str, Any],
        transferability: Dict[str, Any],
        scores: Dict[str, Any]
    ) -> str:
        """Build explanation prompt from PROMPTS_REVIEW.md"""
        
        # Format CV data
        cv_summary = f"""
Skills: {", ".join(cv_data.get("skills", []))}
Experience: {cv_data.get("years_experience_total", 0)} years
Seniority: {", ".join(cv_data.get("seniority_signals", []))}
Domain: {", ".join(cv_data.get("domain_expertise", []))}
"""
        
        # Format comparison
        matched_must = [r["requirement"] for r in comparison["matched_must_have"]]
        missing_must = [r["requirement"] for r in comparison["missing_must_have"]]
        
        return f"""
Generate match explanation using ONLY the data below.

CV DATA:
{cv_summary}

MATCHED REQUIREMENTS:
{", ".join(matched_must) if matched_must else "None"}

MISSING REQUIREMENTS:
{", ".join(missing_must) if missing_must else "None"}

TRANSFERABILITY:
{json.dumps(transferability["assessments"], indent=2)}

SCORES:
Overall: {scores["overall_score"]}%
Skills: {scores["skills_score"]}%
Experience: {scores["experience_score"]}%

CRITICAL RULES:
1. Use ONLY data provided above
2. Do NOT invent facts
3. Quote specific CV evidence

Generate:
1. strengths: 3-5 items prioritized by importance
2. gaps: Missing must-haves with transferability context
3. recommendations: 2-4 specific, actionable items

Return JSON:
{{
  "strengths": [],
  "gaps": [],
  "recommendations": []
}}

GOOD strength: "10 years Python at Microsoft and Deep Instinct (exceeds 3+ requirement)"
BAD strength: "Strong technical skills"

GOOD gap: "React.js - However, has Angular (transferability: 0.8, ramp-up: 2-4 weeks)"
BAD gap: "Missing frontend skills"

GOOD recommendation: "Complete React course on Udemy (20 hours) to fill React.js gap"
BAD recommendation: "Improve skills"

SPECIAL: If candidate has 10+ years, NEVER recommend getting a degree.
"""
```

#### 4.2 Success Criteria
- [ ] Strengths are specific and quote CV evidence
- [ ] Gaps include transferability context when score >= 0.5
- [ ] Recommendations are actionable (course/project/cert, not generic advice)
- [ ] No recommendations for degrees if candidate has 10+ years
- [ ] All tests pass

---

## Phase 5: Integration & Testing (Week 4)

### Goal
Integrate all components and test end-to-end

### Tasks

#### 5.1 Create Main v4 Service
**File**: `backend/app/services/cv_matcher_v4.py`

```python
from app.services.cv_extractor_v4 import CVExtractorV4
from app.services.skill_normalizer import SkillNormalizer
from app.services.cv_comparator import CVComparator
from app.services.base_scorer import BaseScorer
from app.services.transferability_assessor import TransferabilityAssessor
from app.services.final_scorer import FinalScorer
from app.services.explanation_generator import ExplanationGenerator
from typing import Dict, Any
from datetime import datetime
import json

class CVMatcherServiceV4:
    """
    CV Matcher v4.0 - Extract → Normalize → Compare → Score → Explain
    """
    
    def __init__(self):
        self.extractor = CVExtractorV4()
        self.normalizer = SkillNormalizer()
        self.comparator = CVComparator()
        self.base_scorer = BaseScorer()
        self.transferability = TransferabilityAssessor()
        self.final_scorer = FinalScorer()
        self.explanation = ExplanationGenerator()
        
        print("🔧 Initializing CV Matcher v4.0")
    
    async def analyze_match(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for v4.0 matching.
        """
        
        print(f"🎯 [v4.0] Analyzing CV match for job: {job_data.get('title')}")
        
        # Step 1: Extract CV facts (AI - zero hallucination)
        # Note: cv_data already contains parsed sections, but we re-extract for v4.0
        cv_text = self._format_cv_text(cv_data)
        cv_extracted = await self.extractor.extract_cv_facts(cv_text)
        
        # Step 2: Job requirements (already extracted by scraper)
        job_requirements = job_data.get("requirements_matrix", {})
        
        # Step 3: Normalize (Rules)
        cv_normalized = self.normalizer.normalize_cv_data(cv_extracted)
        job_normalized = self.normalizer.normalize_job_data(job_requirements)
        
        # Step 4: Deterministic comparison (Rules)
        comparison = self.comparator.compare_requirements(cv_normalized, job_normalized)
        
        # Step 5A: Base scoring (Rules)
        base_scores = self.base_scorer.calculate_base_scores(
            comparison, cv_normalized, job_normalized
        )
        
        # Step 5B: Transferability assessment (AI - narrow scope)
        transferability = await self.transferability.assess_missing_skills(
            cv_skills=list(self._get_all_cv_tech(cv_normalized)),
            missing_requirements=comparison["missing_must_have"],
            cv_years=cv_normalized.get("years_experience_total", 0) or 0,
            cv_domain=cv_normalized.get("domain_expertise", []),
            job_domain=job_normalized.get("domain", "")
        )
        
        # Step 5C: Final scoring (Rules + transferability)
        scores = self.final_scorer.calculate_final_scores(
            base_scores, transferability, comparison
        )
        
        # Step 6: AI explanation (Constrained)
        explanation = await self.explanation.generate_explanation(
            cv_normalized, job_normalized, comparison, transferability, scores
        )
        
        # Combine results
        result = self._build_final_result(
            scores, comparison, transferability, explanation, cv_normalized
        )
        
        print(f"✅ [v4.0] Match analysis complete: {result['overall_score']}% match")
        
        # Log for review
        self._log_match_analysis(cv_data, job_data, result)
        
        return result
    
    def _format_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """Format CV sections into text for extraction"""
        sections = cv_data.get("sections", {})
        
        text_parts = []
        
        if "summary" in sections:
            text_parts.append(f"SUMMARY:\n{sections['summary']}\n")
        
        if "experience" in sections:
            exp_text = sections["experience"]
            if isinstance(exp_text, str):
                text_parts.append(f"EXPERIENCE:\n{exp_text}\n")
            elif isinstance(exp_text, list):
                text_parts.append(f"EXPERIENCE:\n{json.dumps(exp_text, indent=2)}\n")
        
        if "skills" in sections:
            skills_text = sections["skills"]
            if isinstance(skills_text, str):
                text_parts.append(f"SKILLS:\n{skills_text}\n")
            elif isinstance(skills_text, dict):
                text_parts.append(f"SKILLS:\n{json.dumps(skills_text, indent=2)}\n")
        
        if "education" in sections:
            edu_text = sections["education"]
            if isinstance(edu_text, str):
                text_parts.append(f"EDUCATION:\n{edu_text}\n")
            elif isinstance(edu_text, list):
                text_parts.append(f"EDUCATION:\n{json.dumps(edu_text, indent=2)}\n")
        
        return "\n".join(text_parts)
    
    def _get_all_cv_tech(self, cv_data: Dict[str, Any]) -> set:
        """Get all tech from CV"""
        all_tech = set()
        for field in ["skills", "languages", "frameworks", "cloud_platforms", "databases", "tools"]:
            if field in cv_data:
                all_tech.update(cv_data[field])
        return all_tech
    
    def _build_final_result(
        self,
        scores: Dict[str, Any],
        comparison: Dict[str, Any],
        transferability: Dict[str, Any],
        explanation: Dict[str, Any],
        cv_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build final match result"""
        
        # Extract matched/missing lists
        matched_skills = [r["requirement"] for r in comparison["matched_must_have"]]
        missing_skills = [r["requirement"] for r in comparison["missing_must_have"]]
        
        # Education details
        education_match = comparison.get("education_match", {})
        matched_qualifications = []
        missing_qualifications = []
        
        if education_match.get("status") == "MET":
            matched_qualifications.append(education_match["evidence"])
        else:
            missing_qualifications.append(education_match["requirement"])
        
        return {
            **scores,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_qualifications": matched_qualifications,
            "missing_qualifications": missing_qualifications,
            "gaps": explanation["gaps"],
            "strengths": explanation["strengths"],
            "recommendations": explanation["recommendations"],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _log_match_analysis(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ):
        """Log match analysis for review"""
        # Implement logging as needed
        pass
```

#### 5.2 Add v4 Endpoint
**File**: `backend/app/api/routes/matching.py`

Add new endpoint:
```python
@router.post("/analyze-v4")
async def analyze_match_v4(request: AnalyzeMatchRequest):
    """Analyze CV-to-job match using v4.0 matcher"""
    matcher = CVMatcherServiceV4()
    result = await matcher.analyze_match(request.cv_data, request.job_data)
    return result
```

#### 5.3 Testing Suite
Create comprehensive tests in `backend/tests/test_matcher_v4.py`:

```python
import pytest
from app.services.cv_matcher_v4 import CVMatcherServiceV4

@pytest.mark.asyncio
async def test_v4_no_empty_arrays():
    """Test that v4.0 never returns empty gaps/matched_qualifications"""
    matcher = CVMatcherServiceV4()
    
    # Load test data
    cv_data = load_test_cv("Tomer Cohen - CV.pdf")
    job_data = load_test_job("Backend Python Team Leader")
    
    result = await matcher.analyze_match(cv_data, job_data)
    
    # Critical assertions
    assert "matched_qualifications" in result
    assert "missing_qualifications" in result
    assert isinstance(result["gaps"], list)
    
    # If there are missing must-haves, gaps should not be empty
    if result["missing_skills"]:
        assert len(result["gaps"]) > 0

@pytest.mark.asyncio
async def test_v4_no_hallucination():
    """Test that v4.0 doesn't hallucinate technologies"""
    matcher = CVMatcherServiceV4()
    
    cv_data = load_test_cv("Backend only CV")  # CV with only Python/Backend
    job_data = load_test_job("React Frontend")
    
    result = await matcher.analyze_match(cv_data, job_data)
    
    # Should NOT show React in matched_skills
    assert "React" not in result["matched_skills"]
    assert "React" in result["missing_skills"]

@pytest.mark.asyncio
async def test_v4_transferability_realistic():
    """Test that transferability assessments are realistic"""
    matcher = CVMatcherServiceV4()
    
    cv_data = load_test_cv("Angular developer")
    job_data = load_test_job("React developer")
    
    result = await matcher.analyze_match(cv_data, job_data)
    
    # Check transferability for Angular → React
    transferability_details = result["transferability_details"]
    react_assessment = next(
        (a for a in transferability_details if a["requirement"] == "React"),
        None
    )
    
    assert react_assessment is not None
    assert 0.7 <= react_assessment["transferability_score"] <= 0.9  # Adjacent framework

@pytest.mark.asyncio
async def test_v4_reproducibility():
    """Test that v4.0 base scores are reproducible"""
    matcher = CVMatcherServiceV4()
    
    cv_data = load_test_cv("Tomer Cohen - CV.pdf")
    job_data = load_test_job("Backend Python Team Leader")
    
    # Run twice
    result1 = await matcher.analyze_match(cv_data, job_data)
    result2 = await matcher.analyze_match(cv_data, job_data)
    
    # Base scores should be identical
    assert result1["base_skills_score"] == result2["base_skills_score"]
    assert result1["experience_score"] == result2["experience_score"]
    assert result1["qualifications_score"] == result2["qualifications_score"]
    
    # Overall score may vary slightly due to transferability (±2 points acceptable)
    assert abs(result1["overall_score"] - result2["overall_score"]) <= 2
```

#### 5.4 Success Criteria
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] v4.0 vs v3.0 comparison shows improvements:
  - [ ] Zero empty gaps/matched_qualifications arrays
  - [ ] Hallucination rate < 5%
  - [ ] Transferability assessments 90%+ realistic
  - [ ] Recommendations 85%+ specific
- [ ] Performance acceptable: latency < 6 seconds (95th percentile)

---

## Deployment Strategy

### Option A: Parallel Rollout (Recommended)
1. Deploy v4.0 as `/api/matching/analyze-v4`
2. Keep v3.0 as `/api/matching/analyze`
3. Update frontend to call v4.0 for new matches
4. A/B test with 50/50 split for 1 week
5. Gather user feedback
6. Switch primary endpoint if v4.0 successful

### Option B: Feature Flag
1. Add `MATCHER_VERSION=4` config
2. Toggle between v3.0 and v4.0 per request
3. Monitor error rates and accuracy
4. Gradual rollout: 10% → 50% → 100%

### Success Metrics
- **Accuracy**: Hallucination rate < 5%
- **Completeness**: Zero empty arrays (gaps, matched_qualifications)
- **Quality**: Recommendation specificity > 85%
- **Performance**: P95 latency < 6 seconds
- **User Satisfaction**: Net Promoter Score increase

---

## Timeline Summary

| Week | Phase | Deliverable | Success Criteria |
|------|-------|-------------|------------------|
| 1 | Foundation | CV extraction + normalization | Zero hallucination, 100% accurate extraction |
| 2 | Comparison | Deterministic comparison engine | 100% reproducible, all requirements checked |
| 3 | Scoring | Hybrid base + transferability | Realistic transferability (90%+), reproducible base |
| 4 | Explanation | Constrained AI explanations | Specific recommendations (85%+), no degree for veterans |
| 4 | Integration | End-to-end v4.0 service | All tests pass, ready for deployment |

---

## Next Steps

1. **Review & Approve**: Get stakeholder sign-off on plan
2. **Set up environment**: Create feature branch `feature/matcher-v4`
3. **Start Week 1**: Implement CV extraction service
4. **Daily standups**: Track progress against timeline
5. **Weekly demos**: Show progress to stakeholders

**Ready to start implementation?**
