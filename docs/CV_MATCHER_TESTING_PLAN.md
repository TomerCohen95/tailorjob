# CV Matcher Testing & Improvement Plan

## Executive Summary

This plan provides a complete testing and improvement framework for the CV matcher. The system enables:

1. **Batch testing** - Test multiple CVs against multiple jobs automatically
2. **Job scraping** - Convert job URLs to structured JSON format
3. **Result export** - Generate comprehensive review files for external AI evaluation
4. **Version comparison** - Track improvements across matcher versions
5. **Iterative improvement** - Systematic prompt/logic refinement workflow

## Architecture Components

### 1. Job URL Scraper (`backend/scrape_jobs.py`)

**Purpose**: Convert a list of job URLs into structured JSON format for testing

**Input**: `job_urls.txt`
```
https://www.linkedin.com/jobs/view/123456
https://jobs.lever.co/company/job-id
https://example.com/careers/position
```

**Output**: `jobs.jsonl` (one JSON per line)
```json
{"id":"job-001","title":"Senior Backend Engineer","company":"TechCorp","url":"https://...","description":"..."}
{"id":"job-002","title":"Frontend Developer","company":"StartupXYZ","url":"https://...","description":"..."}
```

**CLI Usage**:
```bash
cd backend

# Scrape all URLs and export to JSONL
python scrape_jobs.py \
  --urls ./test_data/job_urls.txt \
  --output ./test_data/jobs.jsonl

# With progress tracking
# Output:
# Scraping jobs...
# [1/10] ✓ Senior Backend Engineer @ TechCorp
# [2/10] ✓ Frontend Developer @ StartupXYZ
# [3/10] ✗ Failed: Login required (skipped)
# [4/10] ✓ Full Stack Engineer @ StartupABC
# ...
# 
# Successfully scraped: 8/10 jobs
# Failed: 2 jobs (see errors.log)
# Output saved to: ./test_data/jobs.jsonl
```

**Features**:
- Reuses existing [`job_scraper_service`](backend/app/services/job_scraper.py:8)
- Handles failures gracefully (logs errors, continues with next URL)
- Deduplication via job_id extraction
- Progress bar with ETA
- Resume capability (skip already scraped jobs)
- Error reporting (which URLs failed and why)

**Implementation Notes**:
- Uses existing scraper service - no new scraping logic needed
- Async execution for speed
- Validates scraped data before export
- Auto-generates job IDs if not found in URL

---

### 2. Batch Test Runner (`backend/test_matcher.py`)

**Purpose**: Run CV matcher against all CV+Job combinations and export results

**Input**:
- CV folder: `test_data/cvs/` (PDFs or pre-parsed JSONs)
- Jobs file: `test_data/jobs.jsonl`

**Output**: `test_results/review_YYYYMMDD_HHMMSS.jsonl`

Each line contains complete test case:
```json
{
  "test_id": "cv-001_job-003",
  "timestamp": "2025-11-25T16:30:00Z",
  "matcher_version": "1.2.0",
  "cv": {
    "identifier": "backend-senior.pdf",
    "parsed_data": { /* full CV data */ }
  },
  "job": {
    "id": "job-003",
    "title": "Senior Frontend Developer",
    "company": "StartupXYZ",
    "description": { /* structured description */ }
  },
  "match_result": {
    "overall_score": 42,
    "skills_score": 25,
    "experience_score": 50,
    "qualifications_score": 100,
    "strengths": [...],
    "gaps": [...],
    "recommendations": [...],
    "matched_skills": [...],
    "missing_skills": [...],
    "matched_qualifications": [...],
    "missing_qualifications": [...]
  },
  "metadata": {
    "execution_time_ms": 1234,
    "model": "gpt-4",
    "temperature": 0
  }
}
```

**CLI Usage**:
```bash
# Basic run
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --output ./test_results/review.jsonl

# With version tagging
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --version 1.2.0 \
  --output ./test_results/v1.2.0_review.jsonl

# Resume previous run
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --resume ./test_results/review.jsonl

# Output format options
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --output-format markdown  # or: jsonl, json, html
```

**Features**:
- Parallel execution (configurable worker count)
- Progress tracking with ETA
- Resume capability (skip completed tests)
- Version tagging for comparison
- Multiple output formats (JSONL, JSON, Markdown, HTML)
- Automatic CV parsing (PDF → JSON)
- Error handling (continues on failure, logs errors)

**Implementation Notes**:
- Reuses [`cv_matcher_service`](backend/app/services/cv_matcher.py:9) - no changes needed
- Reuses [`cv_parser_service`](backend/app/services/cv_parser.py:8) for PDF parsing
- Stores results incrementally (safe to interrupt)
- Deterministic test ordering (same input → same order)

---

### 3. Version Comparison Tool (`backend/compare_versions.py`)

**Purpose**: Compare test results between two matcher versions

**CLI Usage**:
```bash
python compare_versions.py \
  --baseline ./test_results/v1.0_review.jsonl \
  --current ./test_results/v1.1_review.jsonl \
  --output ./comparison_v1.0_vs_v1.1.md
```

**Output**: Markdown comparison report

```markdown
# Version Comparison: v1.0 → v1.1

## Summary
- Total tests: 50
- Improved: 32 tests (64%)
- Degraded: 5 tests (10%)
- Unchanged: 13 tests (26%)
- Average score change: +8.2%

## Score Distribution Changes

### v1.0
- 0-20%: 5 tests
- 21-40%: 10 tests
- 41-60%: 20 tests
- 61-80%: 10 tests
- 81-100%: 5 tests

### v1.1
- 0-20%: 2 tests (↓3)
- 21-40%: 6 tests (↓4)
- 41-60%: 18 tests (↓2)
- 61-80%: 18 tests (↑8)
- 81-100%: 6 tests (↑1)

## Detailed Changes

### Significant Improvements (↑15% or more)

**Test: backend-senior.pdf × Frontend Job**
- v1.0: 55% overall (incorrect - should be lower for domain mismatch)
- v1.1: 42% overall (✓ correct - proper domain penalty)
- Analysis: Better domain mismatch detection

**Test: fullstack-mid.pdf × Full Stack Role**
- v1.0: 68% overall
- v1.1: 85% overall (↑17%)
- Analysis: Better skill synonym matching (recognized "JS" as "JavaScript")

### Regressions (↓10% or more)

**Test: security-expert.pdf × Security Engineer**
- v1.0: 88% overall
- v1.1: 75% overall (↓13%)
- Analysis: May be over-penalizing specialized roles - investigate

## Recommendations

Based on the comparison:
1. ✅ Domain mismatch detection significantly improved
2. ✅ Skill synonym matching working better
3. ⚠️ Review security/specialized role scoring logic
4. ✅ Overall quality improved - ready for further testing
```

**Features**:
- Side-by-side score comparison
- Identifies improvements and regressions
- Highlights significant changes
- Statistical summary
- Actionable recommendations

---

### 4. Result Analysis Tool (`backend/analyze_results.py`)

**Purpose**: Generate statistics and insights from test results

**CLI Usage**:
```bash
# Basic statistics
python analyze_results.py \
  --input ./test_results/v1.1_review.jsonl \
  --stats

# Find specific patterns
python analyze_results.py \
  --input ./test_results/v1.1_review.jsonl \
  --filter "overall_score < 50"

# Export filtered results
python analyze_results.py \
  --input ./test_results/v1.1_review.jsonl \
  --filter "domain_mismatch" \
  --export ./domain_mismatch_cases.jsonl
```

**Output Examples**:

```
=== Test Results Analysis ===

Overall Statistics:
- Total tests: 50
- Average overall score: 62.4%
- Average skills score: 65.8%
- Average experience score: 68.2%
- Average qualifications score: 75.1%

Score Distribution:
  0-20%:  ████ 4 tests (8%)
 21-40%:  ████████ 8 tests (16%)
 41-60%:  ████████████████████ 20 tests (40%)
 61-80%:  ███████████████ 15 tests (30%)
81-100%:  ██████ 6 tests (12%)

Most Common Missing Skills:
1. React - 30 tests (60%)
2. TypeScript - 25 tests (50%)
3. Python - 18 tests (36%)
4. AWS - 15 tests (30%)
5. Docker - 12 tests (24%)

Gap Analysis:
- Domain mismatch identified: 12 tests
- Education requirements not met: 8 tests
- Experience level mismatch: 6 tests
- Certification gaps: 4 tests

Recommendations Frequency:
- "Build portfolio projects" - 18 tests
- "Gain experience with [skill]" - 25 tests
- "Consider certification in [area]" - 8 tests
```

---

## Complete Workflow

### Step 1: Prepare Test Data

```bash
cd backend

# Create directories
mkdir -p test_data/cvs test_results

# Copy your CVs
cp ~/Documents/my-cv.pdf test_data/cvs/
cp ~/Documents/other-cvs/*.pdf test_data/cvs/

# Create job URLs file
cat > test_data/job_urls.txt << 'EOF'
https://www.linkedin.com/jobs/view/123456
https://jobs.lever.co/company/senior-backend
https://www.glassdoor.com/job-listing/frontend-dev
EOF

# Scrape jobs
python scrape_jobs.py \
  --urls test_data/job_urls.txt \
  --output test_data/jobs.jsonl

# Verify output
cat test_data/jobs.jsonl | jq .title
# Output:
# "Senior Backend Engineer"
# "Senior Frontend Developer"
# "Full Stack Engineer"
```

### Step 2: Run Baseline Tests (v1.0)

```bash
# Run tests with current matcher version
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --version 1.0 \
  --output ./test_results/v1.0_review.jsonl

# Output:
# Loading 5 CVs...
# Parsing PDFs... [████████████] 5/5
# Loading 10 jobs from jobs.jsonl...
# 
# Running 50 test combinations...
# Progress: [████████████] 50/50 (100%) - ETA: 0s
# 
# Results saved to: ./test_results/v1.0_review.jsonl
# 
# Summary:
# - Average overall score: 58.2%
# - Score range: 18% - 92%
# - Total execution time: 2m 15s
```

### Step 3: Review with External AI

```bash
# Option A: Send file to Roo (this system)
# Roo can read the file and evaluate each test case

# Option B: Copy to ChatGPT/Claude
cat test_results/v1.0_review.jsonl | jq -c . > review_for_ai.jsonl
# Copy contents and send to your AI system with prompt:
# "Review these CV matcher results. For each test case, evaluate:
#  1. Are matched/missing skills correct?
#  2. Is the score reasonable?
#  3. Are recommendations helpful?
#  Identify patterns of errors."

# Option C: Generate human-readable markdown
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --version 1.0 \
  --output-format markdown

# Open test_results/v1.0_review.md in browser or editor
```

### Step 4: Analyze Feedback & Modify Matcher

Based on AI feedback (example):
```
Issues found:
1. Domain mismatch not detected (15 cases) - Backend CV scored 70% for Frontend job
2. Skill synonyms not recognized (12 cases) - "JS" not matched to "JavaScript"
3. Over-weighting irrelevant experience (8 cases)
```

**Action**: Modify matcher prompt in [`cv_matcher.py`](backend/app/services/cv_matcher.py:50)

```python
# Example modifications:

# 1. Strengthen domain mismatch rules
system_message = """
...
4. EXPERIENCE SCORING - DOMAIN AWARENESS (STRICTER)
   Consider domain relevance:
   - Frontend job + Frontend experience = 85-100%
   - Backend job + Backend experience = 85-100%
   - Frontend job + Backend experience = 25-40% (WRONG DOMAIN)  # ← Changed from 35-50%
   - Backend job + Frontend experience = 25-40% (WRONG DOMAIN)  # ← Changed from 35-50%
   ...

# 2. Add skill synonym normalization
2. SKILL MATCHING RULES - CRITICAL
   ...
   - Normalize skill names and map synonyms:
     * "k8s" → "kubernetes"
     * "js", "javascript", "ecmascript" → "javascript"
     * "ts", "typescript" → "typescript"
     * "react.js", "reactjs" → "react"
     * "docker", "containerization" → "docker"  # ← Added more synonyms
   ...
```

### Step 5: Retest & Compare (v1.1)

```bash
# Run tests again with modified matcher
python test_matcher.py \
  --cvs ./test_data/cvs \
  --jobs ./test_data/jobs.jsonl \
  --version 1.1 \
  --output ./test_results/v1.1_review.jsonl

# Compare versions
python compare_versions.py \
  --baseline ./test_results/v1.0_review.jsonl \
  --current ./test_results/v1.1_review.jsonl \
  --output ./comparison_v1.0_vs_v1.1.md

# Review comparison
cat comparison_v1.0_vs_v1.1.md

# Send comparison to AI for evaluation:
# "Did the changes fix the issues? Any new problems?"
```

### Step 6: Iterate Until Satisfied

```bash
# Continue cycle:
# Test → Review → Modify → Retest → Compare
# Until quality is acceptable

# Track all versions
ls -la test_results/
# v1.0_review.jsonl
# v1.1_review.jsonl
# v1.2_review.jsonl
# v1.3_review.jsonl (final)
```

### Step 7: Deploy to Production

Once satisfied with test results:

1. The matcher service already uses the modified prompt (no deployment needed)
2. Clear cache to force re-analysis with new version:
   ```bash
   # Via API
   curl -X DELETE http://localhost:8000/api/matching/score/{cv_id}/{job_id}
   
   # Or directly in database
   supabase db reset  # if needed
   ```

---

## Implementation Files Summary

### New Files to Create

1. **`backend/scrape_jobs.py`** (~150 lines)
   - Reads URLs from file
   - Calls existing job_scraper_service for each URL
   - Exports to JSONL format
   - Error handling and progress tracking

2. **`backend/test_matcher.py`** (~300 lines)
   - Loads CVs and jobs
   - Runs matcher for each combination
   - Exports results in multiple formats
   - Progress tracking, resume capability

3. **`backend/compare_versions.py`** (~200 lines)
   - Loads two result files
   - Compares scores and outputs
   - Generates markdown diff report
   - Statistical analysis

4. **`backend/analyze_results.py`** (~150 lines)
   - Loads result file
   - Generates statistics
   - Filters and searches
   - Exports subsets

### Total Lines of Code: ~800 lines

### No Changes to Existing Code
- All existing services reused as-is
- No modifications to production code
- Zero risk to current functionality

---

## Directory Structure After Implementation

```
backend/
├── test_data/                    # Your test data
│   ├── cvs/                      # CV files (PDFs)
│   │   ├── backend-senior.pdf
│   │   ├── frontend-mid.pdf
│   │   └── fullstack-junior.pdf
│   ├── job_urls.txt              # URLs to scrape
│   └── jobs.jsonl                # Scraped job data
│
├── test_results/                 # Test outputs
│   ├── v1.0_review.jsonl         # Baseline results
│   ├── v1.1_review.jsonl         # After improvements
│   ├── v1.2_review.jsonl         # Further improvements
│   ├── comparison_v1.0_vs_v1.1.md
│   └── comparison_v1.1_vs_v1.2.md
│
├── scrape_jobs.py                # NEW: URL → JSON converter
├── test_matcher.py               # NEW: Batch test runner
├── compare_versions.py           # NEW: Version comparator
├── analyze_results.py            # NEW: Statistics tool
│
└── app/                          # Existing code (no changes)
    └── services/
        ├── cv_matcher.py         # Modify only prompt text
        ├── cv_parser.py          # Reused as-is
        └── job_scraper.py        # Reused as-is
```

---

## Timeline Estimate

### Phase 1: Job Scraper (2-3 hours)
- [ ] Create `scrape_jobs.py`
- [ ] Add URL file parser
- [ ] Integrate job_scraper_service
- [ ] Add progress tracking
- [ ] Test with sample URLs

### Phase 2: Test Runner (4-5 hours)
- [ ] Create `test_matcher.py`
- [ ] Add CV loader (PDF + JSON support)
- [ ] Add job loader
- [ ] Integrate cv_parser and cv_matcher services
- [ ] Add parallel execution
- [ ] Add progress tracking
- [ ] Implement multiple output formats
- [ ] Test with sample data

### Phase 3: Analysis Tools (3-4 hours)
- [ ] Create `compare_versions.py`
- [ ] Implement diff logic
- [ ] Generate markdown report
- [ ] Create `analyze_results.py`
- [ ] Add statistics generation
- [ ] Add filtering capabilities
- [ ] Test comparison and analysis

### Phase 4: Testing & Documentation (2-3 hours)
- [ ] End-to-end testing
- [ ] Create usage examples
- [ ] Write troubleshooting guide
- [ ] Document common issues

**Total: 11-15 hours** (spread over 2-3 days)

---

## Success Criteria

### Must Have (MVP)
- ✅ Scrape job URLs to JSONL
- ✅ Run batch tests (all CVs × all jobs)
- ✅ Export complete test results
- ✅ Support resume capability
- ✅ Version tagging and comparison

### Should Have
- ✅ Progress tracking with ETA
- ✅ Multiple output formats (JSONL, Markdown)
- ✅ Error handling and logging
- ✅ Statistical analysis
- ✅ Parallel execution

### Nice to Have (Future)
- ⏳ Web UI for result browsing
- ⏳ Automated regression testing
- ⏳ Ground truth dataset with human annotations
- ⏳ CI/CD integration (test on every commit)
- ⏳ API for external evaluation tools

---

## Next Steps

1. **Approve this plan** ✅ (awaiting your feedback)
2. **Prepare test data**
   - Provide CV files (or use dummy examples)
   - Provide job URLs (or use public job boards)
3. **Implement Phase 1** (job scraper)
4. **Validate scraper output** (check JSONL format)
5. **Implement Phase 2** (test runner)
6. **Run initial tests** (establish baseline)
7. **Review with external AI** (you + your AI system)
8. **Iterate improvements** (modify matcher prompt)
9. **Retest and compare** (measure progress)
10. **Deploy when satisfied**

---

## Questions & Decisions Needed

### 1. Output Format Preference
- **JSONL** (recommended) - Easy to stream, line-by-line processing
- **JSON** - Single array, easier for some tools
- **Markdown** - Human-readable, good for browser viewing
- **All three** - Maximum flexibility

**Recommendation**: Start with JSONL, add others if needed

### 2. Parallel Execution
- **Sequential** (simple, slower) - 1 test at a time
- **Parallel** (faster, complex) - 5-10 tests simultaneously

**Recommendation**: Start sequential, add parallel in Phase 2

### 3. Test Data Source
- **Your real CVs/jobs** - Best for actual use case
- **Synthetic examples** - Faster to get started, less realistic
- **Public examples** - GitHub CV templates + public job boards

**Recommendation**: Mix of real + synthetic for comprehensive testing

### 4. External AI Integration
- **Manual** (copy/paste) - Simple, works with any AI
- **Script-assisted** (generate formatted prompt) - Semi-automated
- **Full API integration** - Fully automated (future)

**Recommendation**: Start manual, automate later if needed

---

## Summary

This plan provides a complete, implementable solution for testing and improving the CV matcher:

1. **Job scraper** converts URLs → structured JSON
2. **Test runner** executes all CV×Job combinations
3. **Export format** provides complete data for external AI review
4. **Comparison tool** tracks improvements across versions
5. **Analysis tool** generates insights and statistics

**Key Benefits**:
- ✅ Systematic testing (not ad-hoc)
- ✅ Quantifiable improvements (score changes, issue reduction)
- ✅ Reproducible (same input → same output)
- ✅ No risk to production (separate testing environment)
- ✅ Flexible evaluation (works with any AI system)
- ✅ Fast iteration (test → review → modify cycle < 10 minutes)

**Ready to implement once you provide**:
- Test CVs (or confirmation to use synthetic examples)
- Job URLs (or confirmation to use public examples)
- Output format preference (JSONL recommended)
- Any other specific requirements
