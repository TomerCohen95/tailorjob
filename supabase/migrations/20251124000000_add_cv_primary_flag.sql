-- Add is_primary column to cvs table
ALTER TABLE cvs ADD COLUMN is_primary BOOLEAN DEFAULT false;

-- Create index for faster queries
CREATE INDEX idx_cvs_user_primary ON cvs(user_id, is_primary) WHERE is_primary = true;

-- Create function to ensure only one primary CV per user
CREATE OR REPLACE FUNCTION ensure_single_primary_cv()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.is_primary = true THEN
    -- Unset all other CVs for this user
    UPDATE cvs 
    SET is_primary = false 
    WHERE user_id = NEW.user_id 
    AND id != NEW.id 
    AND is_primary = true;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to maintain single primary CV
CREATE TRIGGER trigger_ensure_single_primary_cv
  BEFORE INSERT OR UPDATE ON cvs
  FOR EACH ROW
  WHEN (NEW.is_primary = true)
  EXECUTE FUNCTION ensure_single_primary_cv();

-- Set the most recent CV as primary for existing users
UPDATE cvs c1
SET is_primary = true
WHERE id IN (
  SELECT DISTINCT ON (user_id) id
  FROM cvs
  ORDER BY user_id, created_at DESC
);