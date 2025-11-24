-- Add job_id column to store extracted job identifier from URL
-- This helps detect duplicates even when URLs have different query parameters
ALTER TABLE jobs ADD COLUMN job_id TEXT;

-- Add unique constraint on job URL to prevent duplicate job postings
-- URLs are the most reliable way to identify the same job posting

-- First, add a unique index on (user_id, url) - same user can't add same job twice
-- This handles NULL urls gracefully (NULLs are not considered equal in unique constraints)
CREATE UNIQUE INDEX jobs_user_url_unique
ON jobs(user_id, url)
WHERE url IS NOT NULL;

-- Add unique index on (user_id, company, job_id) for detecting duplicates via job ID
-- This catches cases where same job has slightly different URLs (tracking params, etc.)
CREATE UNIQUE INDEX jobs_user_company_job_id_unique
ON jobs(user_id, LOWER(company), job_id)
WHERE job_id IS NOT NULL;

-- Also add a compound unique index on (user_id, company, title) for jobs without URLs or job_id
-- This prevents obvious duplicates like same company/title combination
CREATE UNIQUE INDEX jobs_user_company_title_unique
ON jobs(user_id, LOWER(company), LOWER(title))
WHERE url IS NULL AND job_id IS NULL;

-- Add helpful comments
COMMENT ON COLUMN jobs.job_id IS
  'Extracted job identifier from URL (e.g., LinkedIn job ID, Indeed job key) for deduplication';

COMMENT ON INDEX jobs_user_url_unique IS
  'Prevents users from adding the same job URL twice';

COMMENT ON INDEX jobs_user_company_job_id_unique IS
  'Prevents duplicate jobs with same company/job_id (handles URL variations)';
  
COMMENT ON INDEX jobs_user_company_title_unique IS
  'Fallback: prevents duplicate jobs with same company/title when URL and job_id are not available';