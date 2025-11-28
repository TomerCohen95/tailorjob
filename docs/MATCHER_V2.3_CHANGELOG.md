# CV Matcher v2.3 - Changelog

## Release Date
2025-11-27

## Overview
Version 2.3 addresses two critical user feedback issues:
1. **Generic evidence strings** - Evidence now includes specific CV details (roles, companies, timeframes)
2. **Identical category scores** - Skills/Experience/Qualifications are now calculated separately based on requirement classification

## What Changed

### 1. Enhanced Evidence Generation (LLM Prompt)
**File**: [`backend/app/services/cv_matcher.py`](backend/app/services/cv_matcher.py:328)

**Before v2.3:**
```
Evidence: "8+ years of experience in Cyber Security R&D"
```

**After v2.3:**
```
Evidence: "10+ years Python development: Senior Developer at TechCorp (2015-2020), Lead Engineer at StartupX (2020-2025)"
Evidence: "Security expertise: Security Researcher role focused on Windows kernel protection at Check Point"
Evidence: "B.Sc Computer Science from MIT (2015)"
```

**Implementation:**
- Added Rule 5 to LLM prompt requesting specific CV references
- Instructs LLM to mention actual roles, companies, years, projects, and technologies
- Example formats provided to guide consistent output

### 2. Category-Based Scoring
**File**: [`backend/app/services/cv_matcher.py`](backend/app/services/cv_matcher.py:520)

**New Methods:**
- `_classify_requirement_type(requirement)` - Classifies each requirement as skill/experience/qualification
- `_calculate_category_scores(must_haves)` - Computes separate scores per category

**Classification Logic:**
```python
# Experience: Contains "years", "experience in/with", "proven track record"
# Qualification: Contains "degree", "bachelor", "certification", "certified"  
# Skill: Default (technologies, tools, methodologies)
```

**Before v2.3:**
```
Skills Score: 70%
Experience Score: 70%  # Same as skills
Qualifications Score: 70%  # Same as skills
```

**After v2.3:**
```
Skills Score: 75%  # Based on skill requirements only
Experience Score: 60%  # Based on experience requirements only
Qualifications Score: 80%  # Based on qualification requirements only
```

### 3. Version Documentation
**Updated:**
- Class docstring now shows "Version 2.3: Enhanced evidence details and category-based scoring"
- [`clear_match_cache.py`](backend/clear_match_cache.py:1) updated to show v2.3 improvements

## Technical Details

### Scoring Algorithm (Unchanged)
- Must-haves weighted 70%, nice-to-haves 30%
- MET = 1.0 credit, PARTIALLY_MET = 0.5 credit (or 0.4 for weak matches)
- Frontend mismatch penalty still applies (0.7x multiplier)

### Category Score Calculation (New)
For each category (skill/experience/qualification):
1. Filter requirements by type using keyword matching
2. Count MET and PARTIALLY_MET within that category
3. Apply same scoring formula as overall calculation
4. If no requirements of that type exist, default to 100 (neutral)

### Evidence Format Requirements (New)
The LLM is now instructed to:
- Include role titles and company names when relevant
- Mention specific years or timeframes
- Reference actual projects or achievements from CV
- Use concrete examples instead of generic summaries

## Testing

### Before Clearing Cache
You may see stale v2.2 results (60% score) due to 7-day cache

### After Clearing Cache
Run: `cd backend && python clear_match_cache.py`

Expected improvements:
- ✅ Category scores differentiated (not all identical)
- ✅ Evidence includes specific CV details
- ✅ Strengths section more informative and actionable
- ✅ Overall score may improve due to better evidence presentation

## Breaking Changes
None - Backward compatible with existing CV and job data structures

## Migration
1. Clear cache: `python clear_match_cache.py`
2. Refresh browser to trigger new match calculation
3. New matches will automatically use v2.3

## Known Limitations
- LLM prompt can generate verbose evidence (may need truncation in UI)
- Category classification is keyword-based (may misclassify edge cases)
- Evidence quality depends on CV structure and detail level

## Next Steps
Consider for v2.4:
- Post-processing to truncate very long evidence strings
- Regex-based category classification for higher accuracy
- Evidence formatting with bullet points for better readability
- Caching evidence alongside match scores for faster retrieval