# CV Matcher Testing - Implementation Clarification

## YES - We Use Your Exact Existing Functions!

The testing scripts will **directly import and call** your existing services. No duplication, no reimplementation.

## Code Example: How Test Scripts Will Work

### 1. Job Scraping Script (`scrape_jobs.py`)

```python
# Import your existing service
from app.services.job_scraper import job_scraper_service

async def scrape_jobs_from_urls(url_file: str, output_file: str):
    """
    Read URLs from file and scrape using YOUR existing scraper
    """
    with open(url_file) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    results = []
    for i, url in enumerate(urls, 1):
        try:
            print(f"[{i}/{len(urls)}] Scraping {url}...")
            
            # ✅ CALLS YOUR EXISTING FUNCTION
            job_data = await job_scraper_service.scrape_job(url)
            
            results.append(job_data)
            print(f"✓ {job_data['title']} @ {job_data['company']}")
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    # Export to JSONL
    with open(output_file, 'w') as f:
        for job in results:
            f.write(json.dumps(job) + '\n')
```

**Result**: Uses [`job_scraper_service.scrape_job()`](backend/app/services/job_scraper.py:25) exactly as-is.

---

### 2. Test Matcher Script (`test_matcher.py`)

```python
# Import your existing services
from app.services.cv_parser import cv_parser_service
from app.services.cv_matcher import cv_matcher_service

async def run_tests(cv_folder: str, jobs_file: str, output_file: str):
    """
    Run matcher tests using YOUR existing parser and matcher
    """
    # Load CVs
    cv_files = list(Path(cv_folder).glob('*.pdf'))
    cvs = []
    
    for cv_file in cv_files:
        print(f"Parsing {cv_file.name}...")
        
        # ✅ CALLS YOUR EXISTING CV PARSER
        with open(cv_file, 'rb') as f:
            file_content = f.read()
        
        text = cv_parser_service.extract_text_from_pdf(file_content)
        cv_data = await cv_parser_service.parse_cv_text(text)
        
        cvs.append({
            'identifier': cv_file.name,
            'parsed_data': cv_data
        })
    
    # Load jobs
    with open(jobs_file) as f:
        jobs = [json.loads(line) for line in f]
    
    # Run tests
    results = []
    for cv in cvs:
        for job in jobs:
            print(f"Testing {cv['identifier']} × {job['title']}...")
            
            # ✅ CALLS YOUR EXISTING MATCHER
            match_result = await cv_matcher_service.analyze_match(
                cv_data=cv['parsed_data'],
                job_data=job
            )
            
            # Store complete test case
            results.append({
                'test_id': f"{cv['identifier']}_{job['id']}",
                'cv': cv,
                'job': job,
                'match_result': match_result,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    # Export results
    with open(output_file, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
```

**Result**: 
- Uses [`cv_parser_service.extract_text_from_pdf()`](backend/app/services/cv_parser.py:31)
- Uses [`cv_parser_service.parse_cv_text()`](backend/app/services/cv_parser.py:42)
- Uses [`cv_matcher_service.analyze_match()`](backend/app/services/cv_matcher.py:36)

All exactly as they are in your codebase!

---

## What the Test Scripts Do

### They are **thin wrappers** that:

1. **Load input data** (CVs from folder, jobs from file)
2. **Call your existing functions** (no changes to logic)
3. **Collect results** (store in structured format)
4. **Export for review** (JSONL file for CV Judge mode)

### They do NOT:
- ❌ Reimplement scraping logic
- ❌ Reimplement parsing logic
- ❌ Reimplement matching logic
- ❌ Change any behavior

### They ARE:
- ✅ Orchestration layer (loop over files, call functions)
- ✅ Data aggregation (combine CV + Job + Result)
- ✅ Export formatting (JSONL output)

---

## Import Paths

All test scripts will import from your existing services:

```python
from app.services.job_scraper import job_scraper_service    # Singleton instance
from app.services.cv_parser import cv_parser_service        # Singleton instance
from app.services.cv_matcher import cv_matcher_service      # Singleton instance
```

These are the **exact same instances** used by your FastAPI app!

---

## Why This Approach?

### Benefits:
1. **Zero duplication** - Test scripts use production code
2. **Same behavior** - Tests reflect actual production matching
3. **Easy maintenance** - Change one place, tests automatically use new logic
4. **Guaranteed accuracy** - Testing exactly what users experience

### What Gets Tested:
- The actual Azure OpenAI prompts in [`cv_matcher.py:50-117`](backend/app/services/cv_matcher.py:50)
- The actual parsing logic in [`cv_parser.py`](backend/app/services/cv_parser.py:1)
- The actual scraping logic in [`job_scraper.py`](backend/app/services/job_scraper.py:1)

---

## When CV Judge Mode Improves Code

When the CV Judge mode identifies issues and proposes changes:

```python
# CV Judge will modify cv_matcher.py directly
# Example: Stricter domain mismatch penalty

# BEFORE (in cv_matcher.py:86):
- Frontend job + Backend experience = 35-50%

# AFTER (CV Judge applies change):
- Frontend job + Backend experience = 25-40% (WRONG DOMAIN)
```

**Then immediately:**
1. Re-run tests using the SAME test scripts
2. The scripts automatically use the modified `cv_matcher_service`
3. Compare new results with previous version
4. Measure improvement

---

## Summary

✅ **YES** - Test scripts call your exact existing functions  
✅ **NO** - No reimplementation or duplication  
✅ **YES** - CV Judge mode modifies your actual service files  
✅ **YES** - Tests automatically use modified logic  

The test framework is a **thin orchestration layer** around your existing services, not a replacement for them.