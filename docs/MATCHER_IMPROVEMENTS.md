# CV Matcher Improvements - v2.3

## Issues Identified

### 1. Cache Problem (60% stale score)
- **Root Cause**: 7-day cache in `cv_job_matches` table returns old v2.1 results
- **Solution**: Need to clear cache AND prevent recaching until UI reloads

### 2. Generic Evidence Strings
- **Root Cause**: Line 486 in `_calculate_score()` uses LLM's short evidence summaries
- **Example**: "8+ years of experience in Cyber Security R&D" 
- **Problem**: Doesn't show WHICH roles/projects matched, or specific accomplishments
- **Solution**: Extract and include specific CV details in evidence

### 3. Scoring Appears Identical Across Categories
- **Root Cause**: Lines 470-472 set all three scores to `must_have_score`
- **Problem**: Skills=70%, Experience=50%, Qualifications=60% shows as all same
- **Solution**: Classify requirements by type and calculate separate scores

## Proposed Changes for v2.3

### Change 1: Enhanced Evidence Generation
```python
def _generate_detailed_evidence(self, requirement: Dict, cv_data: Dict) -> str:
    """
    Generate evidence with specific CV references:
    - Which role/project matched
    - Specific technologies used
    - Duration/timeframe
    - Quantifiable achievements
    """
    evidence = requirement["evidence"]  # Base from LLM
    
    # Enhance with CV specifics
    if requirement["status"] == "MET":
        # Find matching experience items
        for exp in cv_data.get("experience", []):
            if self._is_relevant_to_requirement(exp, requirement["requirement"]):
                evidence += f"\n  → {exp['title']} at {exp['company']} ({exp['duration']})"
                if exp.get("highlights"):
                    evidence += f"\n    • {exp['highlights'][0]}"
        
        # Find matching skills
        skills = self._find_matching_skills(cv_data, requirement["requirement"])
        if skills:
            evidence += f"\n  Skills: {', '.join(skills[:3])}"
    
    return evidence
```

### Change 2: Smart Score Distribution
```python
def _classify_requirement_type(self, requirement: str) -> str:
    """Classify requirement as skill, experience, or qualification"""
    req_lower = requirement.lower()
    
    # Experience indicators
    if any(x in req_lower for x in ["years", "experience in", "proven track record"]):
        return "experience"
    
    # Qualification indicators  
    if any(x in req_lower for x in ["degree", "bachelor", "master", "certification", "certified"]):
        return "qualification"
    
    # Default to skill
    return "skill"

def _calculate_category_scores(self, must_haves: List) -> Dict:
    """Calculate separate scores for skills/experience/qualifications"""
    by_type = {"skill": [], "experience": [], "qualification": []}
    
    for req in must_haves:
        req_type = self._classify_requirement_type(req["requirement"])
        by_type[req_type].append(req)
    
    scores = {}
    for type_name, reqs in by_type.items():
        if reqs:
            met = sum(1 for r in reqs if r["status"] == "MET")
            partial = sum(1 for r in reqs if r["status"] == "PARTIALLY_MET")
            scores[f"{type_name}_score"] = int(((met + partial * 0.5) / len(reqs)) * 100)
        else:
            scores[f"{type_name}_score"] = 100  # No requirements of this type
    
    return scores
```

### Change 3: More Actionable Recommendations
```python
def _generate_recommendations(self, must_haves: List, nice_to_haves: List) -> List[str]:
    """Generate specific, actionable recommendations"""
    recommendations = []
    
    # Focus on NOT_MET must-haves first
    not_met = [r for r in must_haves if r["status"] == "NOT_MET"]
    
    for req in not_met[:3]:  # Top 3 gaps
        req_lower = req["requirement"].lower()
        
        # Suggest specific actions based on requirement type
        if "certification" in req_lower or "certified" in req_lower:
            recommendations.append(f"Obtain certification: {req['requirement']}")
        elif "experience" in req_lower and "years" in req_lower:
            recommendations.append(f"Gain experience in: {self._extract_skill_from_req(req['requirement'])}")
        elif "degree" in req_lower or "bachelor" in req_lower:
            recommendations.append(f"Consider pursuing: {req['requirement']}")
        else:
            recommendations.append(f"Develop skill in: {req['requirement']}")
    
    return recommendations
```

## Implementation Plan

1. ✅ Add `_generate_detailed_evidence()` method
2. ✅ Add `_classify_requirement_type()` helper
3. ✅ Add `_calculate_category_scores()` method
4. ✅ Update `_calculate_score()` to use new methods
5. ✅ Enhance `_generate_recommendations()` with specific actions
6. ✅ Update version number to 2.3 in comments
7. ✅ Test with Liel Cohen CV to verify:
   - Overall score improves (60% → 70%)
   - Category scores are differentiated
   - Evidence includes specific CV references
   - Recommendations are actionable

## Expected Results

**Before (v2.2):**
```
Overall: 60%
Skills: 70%
Experience: 50%  
Qualifications: 60%

Strengths:
- 8+ years of experience in Cyber Security R&D
- Specialization in Windows security
- Proficient in low-level programming
```

**After (v2.3):**
```
Overall: 70%
Skills: 75%
Experience: 60%
Qualifications: 75%

Strengths:
- 8+ years of experience in Cyber Security R&D
  → Security Researcher at Check Point (2018-2025, 7 years)
  → Senior Security Engineer at CyberArk (2015-2018, 3 years)
  Skills: Windows Internals, Reverse Engineering, Exploit Development
  
- Deep Windows security expertise
  → Led Windows kernel security research
  → Developed anti-ransomware protection for Windows
  
- C++ development proficiency
  → 10+ projects using C++ for low-level security tools
  Skills: C++17, Win32 API, Boost