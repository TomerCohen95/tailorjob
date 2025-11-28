-- Add requirements_matrix column to jobs table for structured requirement matching
-- This enables the v2.3 matcher with category-based scoring and detailed evidence

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requirements_matrix JSONB;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_jobs_requirements_matrix ON jobs USING GIN (requirements_matrix);

-- Add comment explaining the structure
COMMENT ON COLUMN jobs.requirements_matrix IS 'Structured job requirements extracted by scraper. Format: {"must_have": [...], "nice_to_have": [...], "meta": {...}}';