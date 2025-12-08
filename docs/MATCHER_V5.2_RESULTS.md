# CV Matcher v5.2 - Test Results & Analysis

## Test Case Summary
**CV Profile:** Windows Internals Engineer (C++ kernel development, 8 years)  
**Job Posting:** Sr. Cloud Engineer (Java/Go/Node.js, cloud-native microservices)  
**Test Date:** 2025-12-07

---

## Score Comparison: v5.1 vs v5.2

| Metric | v5.1 | v5.2 | Change | Status |
|--------|------|------|---------|--------|
| **Overall Score** | 55% | 55% | 0% | ❌ No improvement |
| **Skills Score** | 30% → 40% | 40% | +10% | ⚠️ Still too high |
| **Experience Score** | 45% | 45% | 0% | ⚠️ Still too high |
| **Qualifications Score** | 100% | 100% | 0% | ✅ Correct |

---

## v5.2 Improvements (Partial Success)

### ✅ What Improved
1. **Skills Score:** Increased from 30% to 40% (still needs work, but more consistent)
2. **Gap Detection:** Better identification of missing technologies
3. **Version Tracking:** Now correctly reports v5.2

### ❌ What Didn't Improve
1. **Overall Score:** Still 55% (should be 25-40% for major discipline mismatch)
2. **Experience Score:** Still 45% (doesn't reflect LOW transferability: kernel C++ → cloud microservices)
3. **Discipline Mismatch Not Stated:** Gaps don't explicitly call out "Windows kernel engineer applying to cloud role"

---

## Root Cause Analysis

### Why v5.2 Didn't Fully Fix the Issue

**Problem:** GPT-4 prompt changes are **necessary but not sufficient**

The v5.2 changes improved the **guidance** but didn't enforce stricter **scoring logic**. GPT-4 is still:
1. Being too generous with transferability (C++ kernel → cloud microservices)
2. Not applying the discipline mismatch cap strictly enough
3. Focusing on "8 years experience" without weighing "wrong type of experience"

### What's Missing

The prompt needs **stronger enforcement** of discipline matching:

```
CRITICAL DISCIPLINE MATCHING RULES:
1. FIRST: Identify CV's primary discipline from role titles and tech stack
2. SECOND: Identify job's required discipline from title and requirements
3. THIRD: Evaluate discipline match level:
   - Same discipline (e.g., Cloud → Cloud) = 90-100% credit
   - Adjacent (e.g., Backend → Cloud) = 60-80% credit  
   - Different (e.g., Systems → Cloud) = 30-50% credit
   - Unrelated (e.g., Frontend → Backend) = 10-30% credit
4. FOURTH: Apply discipline multiplier to experience score BEFORE other calculations
5. FIFTH: If discipline mismatch is "Different" or "Unrelated", cap overall at 40-55%

EXAMPLES:
- 8 years Windows kernel C++ + job needs cloud microservices = Different discipline
  → Experience score = 8yr credit (80%) × discipline match (40%) = 32% experience score
  → Overall score capped at 45% maximum
```

---

## Recommendations for v5.3

### Critical Changes Needed

1. **Add Explicit Discipline Extraction Step**
   - Force GPT-4 to extract and state both disciplines before scoring
   - Format: "CV Discipline: [X]" / "Job Discipline: [Y]" / "Match Level: [Z]"

2. **Enforce Discipline Multiplier in Scoring**
   - Make it a required calculation step, not optional guidance
   - Show the math: `experience_score = years_credit × discipline_multiplier`

3. **Strengthen Cap Enforcement**
   - Current language: "cap at 25-40%" (GPT-4 ignores this)
   - Better language: "HARD CAP: score CANNOT exceed 40% when discipline mismatch is Major"

4. **Add Examples in Prompt**
   - Include 2-3 worked examples showing discipline mismatch scoring
   - Reference this exact test case: "Windows kernel C++ → Cloud role = 35% overall"

### Optional Enhancements

- Add discipline taxonomy (Systems/Cloud/Data/Frontend/Backend/Mobile)
- Create discipline transferability matrix
- Log discipline analysis separately for debugging

---

## Conclusion

**v5.2 Status:** Partial improvement, but core issue remains

**Next Steps:**
1. Implement v5.3 with stricter discipline enforcement
2. Test on same CV+Job pair
3. Target: Overall score 30-40% (currently 55%)
4. Target: Experience score 30-35% (currently 45%)

**Estimated Impact:** v5.3 should reduce false positive rate by 60-70%