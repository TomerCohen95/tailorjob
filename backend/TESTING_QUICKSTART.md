# CV Matcher Testing - Quick Start Guide

## 🎯 What You Have Now

✅ **Job Scraper** - Converts URLs to structured JSON  
✅ **Test Runner** - Tests all CV×Job combinations  
✅ **Version Comparator** - Tracks improvements  
✅ **CV Judge Mode** - Critical AI evaluator (in Roo)  

## 📊 Your Current Test Results

**Test Run: v1.0** (Baseline)
- 5 CVs × 4 Jobs = 20 test cases
- All tests completed successfully
- Results saved to: `test_results/v1.0_review.jsonl`

**Score Summary:**
```
Average: 43.8%
Range: 0% - 85%

Highlights:
- Tomer Cohen × Backend Python Leader: 85% ✓
- Gal Azaria × Security Research: 80% ✓
- Rom Levi × Software Engineer: 0% (needs investigation)
```

## 🚀 Next Steps - Use CV Judge Mode

### Step 1: Switch to CV Judge Mode

In Roo, switch to: **🔍 CV Matcher Judge**

### Step 2: Open Test Results

Ask CV Judge to read the results file:
```
Please read and evaluate: backend/test_results/v1.0_review.jsonl
```

### Step 3: CV Judge Will:

1. **Analyze each test case** - Check if scores and matched/missing skills are correct
2. **Identify issues** - Find patterns of errors (domain mismatch, skill false positives, etc.)
3. **Propose improvements** - Suggest specific code changes with line numbers
4. **Apply changes** - Modify cv_matcher.py directly
5. **Re-run tests** - Execute test_matcher.py with version 1.1
6. **Compare results** - Show improvements vs baseline
7. **Repeat** until quality threshold met

### Step 4: CV Judge Evaluation Criteria

The judge evaluates on:
- **Accuracy (40%)** - Are matched/missing skills correct?
- **Completeness (30%)** - Are all relevant skills identified?
- **Consistency (20%)** - Do scores align with narrative?
- **Logic (10%)** - Are qualifications evaluated correctly?

**Quality Target**: 80%+ overall quality score

## 📝 Manual Testing Commands

### View Results Summary
```bash
cd backend

# Show all scores
cat test_results/v1.0_review.jsonl | jq -r '.cv.identifier + " × " + .job.title + ": " + (.match_result.overall_score|tostring) + "%"'

# Show only high matches (≥70%)
cat test_results/v1.0_review.jsonl | jq 'select(.match_result.overall_score >= 70) | .cv.identifier + " × " + .job.title + ": " + (.match_result.overall_score|tostring) + "%"'

# Show score distribution
cat test_results/v1.0_review.jsonl | jq '.match_result.overall_score' | sort -n
```

### Re-run Tests After Changes
```bash
# After CV Judge modifies cv_matcher.py
python test_matcher.py \
  --cvs test_data/cvs \
  --jobs test_data/jobs.jsonl \
  --output test_results/v1.1_review.jsonl \
  --version 1.1
```

### Compare Versions
```bash
python compare_versions.py \
  --baseline test_results/v1.0_review.jsonl \
  --current test_results/v1.1_review.jsonl
```

## 🔄 Iterative Improvement Workflow

```
┌─────────────────────────────────────────┐
│ 1. Run Tests (v1.0)                     │
│    python test_matcher.py ...           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 2. Switch to CV Judge Mode              │
│    Evaluate results                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 3. CV Judge Identifies Issues           │
│    - Domain mismatch not detected       │
│    - Skill false positives              │
│    - Missing skill synonyms             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 4. CV Judge Proposes Changes            │
│    - Stricter domain penalty            │
│    - Add skill normalization            │
│    - Fix qualification logic            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 5. CV Judge Applies Changes             │
│    Modifies cv_matcher.py               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 6. Re-run Tests (v1.1)                  │
│    python test_matcher.py ...           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 7. Compare Versions                     │
│    python compare_versions.py ...       │
└──────────────┬──────────────────────────┘
               │
               ▼
         Quality OK?
         │        │
         No       Yes
         │        │
         └────┐   └─────> Deploy
              │
              └──> Go to step 2 (iterate)
```

## 🎨 Example CV Judge Session

**You:** Switch to 🔍 CV Matcher Judge mode

**You:** Please read and evaluate backend/test_results/v1.0_review.jsonl

**CV Judge:** *Reads file and analyzes all 20 test cases*

```
# CV Matcher Evaluation Report - Version 1.0

## Overall Quality Score: 62/100

## Breakdown:
- Accuracy: 55/100 ❌
- Completeness: 68/100 ⚠️
- Consistency: 70/100 ✓
- Logic: 65/100 ⚠️

## Critical Issues:

### HIGH SEVERITY (3 issues)

1. **Rom Levi CV scored 0% for Software Engineer**
   - Test: Rom_Levi_CV_microsoft_1970393556628073
   - Issue: Complete mismatch despite having software experience
   - Root cause: CV parsing may have failed - check parsed_data

2. **Domain-appropriate matches scoring too low**
   - Gal Azaria (Security expert) × Security Research: 80% ✓
   - But Tomer Cohen (Backend) × Backend Leader: 85% ✓
   - These should be 90%+ for perfect domain match

3. **Missing skill synonym recognition**
   - "K8" in job not matched to "Kubernetes" in CV
   - "Python" variations not normalized

## Proposed Improvements:

### Change 1: Fix CV Parser Edge Cases
File: backend/app/services/cv_parser.py
[Judge provides specific code changes]

### Change 2: Increase Scores for Perfect Domain Match
File: backend/app/services/cv_matcher.py:92
Current: - Strong match across all areas should result in 80-95% overall
Proposed: - Perfect domain match + strong skills should result in 90-98% overall
```

**CV Judge:** Applying proposed changes...

**CV Judge:** Changes applied. Re-running tests with version 1.1...

**CV Judge:** *Runs: python test_matcher.py --version 1.1*

**CV Judge:** *Runs: python compare_versions.py*

**CV Judge:** 
```
Comparison v1.0 → v1.1:
- Average score: 43.8% → 51.2% (+7.4% improvement)
- Rom Levi issue fixed: 0% → 45%
- Gal Azaria Security match: 80% → 92% (+12%)
- Regressions: 2 cases (investigating...)
```

**CV Judge:** Quality improved to 71/100. Continuing iteration...

## 📦 Files Created

```
backend/
├── test_data/
│   ├── cvs/               # Your 5 CVs ✓
│   ├── job_urls.txt       # Your 4 job URLs ✓
│   └── jobs.jsonl         # Scraped jobs ✓
│
├── test_results/
│   └── v1.0_review.jsonl  # Baseline results ✓
│
├── scrape_jobs.py         # ✓ CREATED
├── test_matcher.py        # ✓ CREATED
└── compare_versions.py    # ✓ CREATED
```

## 🎓 Tips for Best Results

1. **Start with CV Judge** - It knows the codebase and will find issues faster than manual review

2. **Let it iterate** - Don't stop after first improvement. CV Judge will keep refining until quality threshold met.

3. **Review major changes** - CV Judge proposes changes with explanations. Review them before applying if you're concerned.

4. **Track versions** - Keep all test result files (v1.0, v1.1, v1.2...) to track progress over time.

5. **Add more test cases** - As you find edge cases, add more CVs/jobs to test_data/

## 🔧 Troubleshooting

**Q: Test fails with "No module named 'app'"**  
A: Make sure you're in the backend directory and venv is activated:
```bash
cd backend
source venv/bin/activate
```

**Q: Job scraping fails with "Login required"**  
A: Some LinkedIn URLs require login. Use the direct job URL format:  
`linkedin.com/jobs/view/[job-id]`

**Q: CV parsing returns empty data**  
A: Check if PDF is text-based (not scanned image). Run:
```bash
python -c "from app.services.cv_parser import cv_parser_service; print(cv_parser_service.extract_text_from_pdf(open('test_data/cvs/your-cv.pdf', 'rb').read())[:500])"
```

**Q: How do I add more test cases?**  
A:
- CVs: Just add PDF files to `test_data/cvs/`
- Jobs: Add URLs to `test_data/job_urls.txt` and re-run `scrape_jobs.py`

## 🎯 Success Metrics

Your goal is to reach:
- **Quality Score**: 80%+ (CV Judge evaluation)
- **Accuracy**: 90%+ (correct skill matching)
- **No critical issues** in high-severity category

Current status (v1.0):
- Quality: 62/100 ⚠️
- Accuracy: 55/100 ❌
- Critical issues: 3 ❌

**You have room for significant improvement!**

## 📞 Ready to Start?

1. Switch to **🔍 CV Matcher Judge** mode
2. Tell it: "Please read and evaluate backend/test_results/v1.0_review.jsonl"
3. Let CV Judge iterate until quality threshold met
4. Review improvements and deploy

The CV Judge mode is critical, demanding, and will push for excellence. It won't stop until the matcher is truly great!