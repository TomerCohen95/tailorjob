-- CV Job Matches Table (AI Scoring with Caching)
CREATE TABLE cv_job_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  
  -- Overall Score
  overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
  
  -- Category Scores
  skills_score INTEGER CHECK (skills_score >= 0 AND skills_score <= 100),
  experience_score INTEGER CHECK (experience_score >= 0 AND experience_score <= 100),
  qualifications_score INTEGER CHECK (qualifications_score >= 0 AND qualifications_score <= 100),
  
  -- Detailed Analysis (JSON)
  analysis JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- Structure: {
  --   "strengths": ["Strong Python skills", "Relevant AWS experience"],
  --   "gaps": ["Missing Kubernetes experience", "No ML background"],
  --   "recommendations": ["Emphasize Python projects", "Add cloud certifications"],
  --   "matched_skills": ["Python", "AWS", "Docker"],
  --   "missing_skills": ["Kubernetes", "ML"],
  --   "matched_qualifications": ["5+ years experience", "Bachelor's degree"],
  --   "missing_qualifications": ["MBA preferred"]
  -- }
  
  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
  
  -- Ensure one match per CV-Job pair
  UNIQUE(cv_id, job_id)
);

-- Indexes for performance
CREATE INDEX idx_cv_job_matches_cv ON cv_job_matches(cv_id);
CREATE INDEX idx_cv_job_matches_job ON cv_job_matches(job_id);
CREATE INDEX idx_cv_job_matches_user ON cv_job_matches(user_id);
CREATE INDEX idx_cv_job_matches_expires ON cv_job_matches(expires_at);

-- Enable Row Level Security
ALTER TABLE cv_job_matches ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their own match scores
CREATE POLICY "Users can manage own match scores"
  ON cv_job_matches FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Function to cleanup expired matches (can be called by cron job)
CREATE OR REPLACE FUNCTION cleanup_expired_matches()
RETURNS void AS $$
BEGIN
  DELETE FROM cv_job_matches WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a trigger to auto-update expires_at on update
CREATE OR REPLACE FUNCTION refresh_match_expiry()
RETURNS TRIGGER AS $$
BEGIN
  NEW.expires_at = NOW() + INTERVAL '7 days';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_cv_job_match_expiry
  BEFORE UPDATE ON cv_job_matches
  FOR EACH ROW
  WHEN (OLD.overall_score IS DISTINCT FROM NEW.overall_score)
  EXECUTE FUNCTION refresh_match_expiry();