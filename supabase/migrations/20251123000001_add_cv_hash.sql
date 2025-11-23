-- Add file_hash column to cvs table for duplicate detection
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS file_hash TEXT;

-- Create index on file_hash and user_id for fast duplicate lookups
CREATE INDEX IF NOT EXISTS idx_cvs_user_hash ON cvs(user_id, file_hash);

-- Add comment explaining the column
COMMENT ON COLUMN cvs.file_hash IS 'SHA-256 hash of file content for duplicate detection';