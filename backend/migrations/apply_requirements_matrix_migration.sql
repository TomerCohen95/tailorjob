-- Add requirements_matrix column to jobs table
-- Run this in Supabase SQL Editor or via psql

-- Add the column if it doesn't exist
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS requirements_matrix JSONB;

-- Create GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_jobs_requirements_matrix 
ON jobs USING GIN (requirements_matrix);

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' 
AND column_name = 'requirements_matrix';