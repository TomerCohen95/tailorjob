-- CVs Table (File Metadata)
CREATE TABLE cvs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  original_filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size INTEGER,
  mime_type TEXT,
  status TEXT NOT NULL DEFAULT 'uploaded',
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  parsed_at TIMESTAMPTZ,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CV Sections (Parsed Data)
CREATE TABLE cv_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
  summary TEXT,
  skills JSONB DEFAULT '[]'::jsonb,
  experience JSONB DEFAULT '[]'::jsonb,
  education JSONB DEFAULT '[]'::jsonb,
  certifications JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(cv_id)
);

-- Jobs Table
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  description TEXT NOT NULL,
  url TEXT,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tailored CVs
CREATE TABLE tailored_cvs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  format TEXT DEFAULT 'markdown',
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CV Revisions
CREATE TABLE cv_revisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tailored_cv_id UUID NOT NULL REFERENCES tailored_cvs(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  revision_type TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tailored_cv_id UUID NOT NULL REFERENCES tailored_cvs(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cvs_user_id ON cvs(user_id);
CREATE INDEX idx_cvs_status ON cvs(status);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_tailored_cvs_user_id ON tailored_cvs(user_id);
CREATE INDEX idx_tailored_cvs_cv_job ON tailored_cvs(cv_id, job_id);
CREATE INDEX idx_chat_messages_tailored_cv ON chat_messages(tailored_cv_id);

-- Enable RLS
ALTER TABLE cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE tailored_cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage own CVs"
  ON cvs FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage own CV sections"
  ON cv_sections FOR ALL
  USING (EXISTS (
    SELECT 1 FROM cvs WHERE cvs.id = cv_sections.cv_id AND cvs.user_id = auth.uid()
  ));

CREATE POLICY "Users can manage own jobs"
  ON jobs FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage own tailored CVs"
  ON tailored_cvs FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own revisions"
  ON cv_revisions FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM tailored_cvs 
    WHERE tailored_cvs.id = cv_revisions.tailored_cv_id 
    AND tailored_cvs.user_id = auth.uid()
  ));

CREATE POLICY "Users can view own chat messages"
  ON chat_messages FOR ALL
  USING (EXISTS (
    SELECT 1 FROM tailored_cvs 
    WHERE tailored_cvs.id = chat_messages.tailored_cv_id 
    AND tailored_cvs.user_id = auth.uid()
  ));

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cvs_updated_at
  BEFORE UPDATE ON cvs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cv_sections_updated_at
  BEFORE UPDATE ON cv_sections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tailored_cvs_updated_at
  BEFORE UPDATE ON tailored_cvs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();