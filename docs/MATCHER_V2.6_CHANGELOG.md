# CV Matcher v2.6 - LLM Fit Assessment

## Release Date
2025-11-27

## Overview
Version 2.6 introduces **LLM-based holistic fit assessment** to complement deterministic matching. The AI evaluates soft skills, career trajectory, growth potential, and overall suitability that rules-based matching can't capture.

## New Scoring Formula

### Before (v2.5):
```
Overall = (Must-have × 0.85) + (Nice-to-have × 0.15)
```

### After (v2.6):
```
Deterministic = (Must-have × 0.85) + (Nice-to-have × 0.15)
Fit Score = LLM assessment (0-100)
Overall = (Deterministic × 0.70) + (Fit Score × 0.30)
```

## What LLM Fit Assessment Evaluates

The AI considers factors that deterministic rules miss:

1. **Career Progression**: Consistent growth, increasing responsibility
2. **Depth vs Breadth**: Deep expertise in relevant areas vs surface knowledge
3. **Problem-Solving**: Evidence of tackling complex technical challenges
4. **Leadership/Collaboration**: Team leading, mentoring, cross-functional work
5. **Passion/Initiative**: Side projects, research, publications, extra effort
6. **Adaptability**: Successfully learning new technologies, domain changes
7. **Cultural Fit**: Background suggests thriving in this role type

## Scoring Guidelines

The LLM uses these ranges:
- **85-100**: Exceptional fit - strong track record, clear growth, relevant depth
- **70-84**: Good fit - solid experience, shows potential, minor gaps acceptable
- **55-69**: Moderate fit - has basics but lacks depth or key experiences
- **40-54**: Weak fit - significant concerns about readiness
- **0-39**: Poor fit - major misalignment

## Example Impact

For a candidate with:
- Must-haves: 4/5 met = 80%
- Nice-to-haves: 1/5 met = 20%
- **Deterministic**: 71%

**v2.5 (Deterministic only)**: 71% overall

**v2.6 (With LLM fit)**:
- If LLM assesses 85% fit: `(71 × 0.7) + (85 × 0.3)` = **75%** ✅ (+4%)
- If LLM assesses 70% fit: `(71 × 0.7) + (70 × 0.3)` = **71%** (no change)
- If LLM assesses 55% fit: `(71 × 0.7) + (55 × 0.3)` = **66%** (-5%)

## Key Features

### 1. Conservative Temperature (0.3)
Lower temperature ensures more consistent scoring across runs.

### 2. Graceful Fallback
If LLM call fails, uses deterministic score as proxy to avoid errors.

### 3. Logging
Prints fit score and reasoning to console for transparency:
```
🎯 LLM Fit Score: 85% - Strong career progression with consistent growth in security roles
```

### 4. Response Schema
Now includes component scores:
```json
{
  "overall_score": 75,
  "deterministic_score": 71,
  "fit_score": 85,
  "skills_score": 50,
  "experience_score": 100,
  "qualifications_score": 100,
  ...
}
```

## Benefits

### For Strong Candidates
- **Recognizes depth**: Experienced professionals get credit for expertise depth
- **Values growth**: Career progression matters, not just checkbox requirements
- **Considers initiative**: Side projects and research count
- **Rewards leadership**: Team building and mentoring add value

### For System
- **Reduces false negatives**: Strong candidates with non-traditional backgrounds get fair assessment
- **Better ranking**: Differentiates between "meets requirements" candidates
- **More nuanced**: Captures real-world hiring considerations
- **Still explainable**: Shows both deterministic and fit components

## Performance Impact

### API Calls
- **Added**: +1 OpenAI API call per match
- **Tokens**: ~500-800 per fit assessment
- **Latency**: +400-600ms per analysis

### Total Per Match
- CV verification: 1 call
- Fit assessment: 1 call (NEW)
- Recommendations: 1 call
- **Total**: 3 OpenAI calls per match

### Cost Mitigation
- 7-day caching in database
- Lower temperature (0.3) uses fewer tokens
- Fallback prevents blocking on API errors

## Testing

### Manual Test
```bash
cd backend
source venv/bin/activate
python clear_match_cache.py  # Clear cache
# Then re-analyze match in UI
```

### Check Console Output
Look for:
```
🎯 LLM Fit Score: 85% - Strong career progression...
✅ Match analysis complete: 75% match
```

### Compare Scores
The response will show:
- `overall_score`: Final combined score
- `deterministic_score`: Rules-based score
- `fit_score`: LLM holistic assessment

## Tuning Parameters

If you want to adjust the balance:

**More conservative** (favor deterministic):
```python
overall_score = (deterministic_score * 0.80) + (fit_score * 0.20)
```

**More AI-driven** (favor fit assessment):
```python
overall_score = (deterministic_score * 0.60) + (fit_score * 0.40)
```

**Current (balanced)**:
```python
overall_score = (deterministic_score * 0.70) + (fit_score * 0.30)
```

## Known Limitations

1. **Consistency**: LLM may vary ±5% on repeated assessments (mitigated by low temperature)
2. **Bias**: AI may have unconscious biases (monitor and adjust prompt)
3. **Explainability**: "Fit" is harder to explain than deterministic rules
4. **Cost**: Adds ~$0.002-0.003 per match analysis

## Future Improvements (v2.7+)

1. **Fit Reasoning Display**: Show LLM's reasoning in UI
2. **Confidence Score**: Include confidence level with fit score
3. **Multiple Evaluations**: Average 2-3 runs for critical decisions
4. **Bias Monitoring**: Track fit scores by demographics to detect bias
5. **Custom Weighting**: Let users adjust deterministic vs fit balance per job

## Version History

- **v2.0**: Hybrid preprocessing + LLM verification
- **v2.1**: Enhanced evidence with CV references
- **v2.2**: Category-based scoring
- **v2.3**: Detailed evidence strings
- **v2.4**: AI-powered detailed recommendations
- **v2.5**: Fairer scoring (85/15 weighting)
- **v2.6**: LLM fit assessment (70/30 deterministic/fit) ← **Current**

## Rollback Procedure

If fit assessment causes issues:

```python
# In _calculate_score(), change line 480 to:
overall_score = deterministic_score  # Disable fit assessment
```

Or revert to v2.5:
```bash
git checkout HEAD~1 backend/app/services/cv_matcher.py
```

---

**Status**: ✅ Deployed and running
**Testing**: Ready for real-world validation
**Next**: Monitor fit scores and adjust prompt/weighting as needed