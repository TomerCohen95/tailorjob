-- Migration: Add profile tables for structured CV and Job matching
-- Created: 2025-11-25
-- Description: Adds job_profiles and cv_profiles tables for normalized, structured matching

-- ============================================================================
-- JOB PROFILES TABLE
-- ============================================================================
-- Stores normalized, structured job requirements extracted from job descriptions
-- One profile per job, created after job scraping

CREATE TABLE job_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Normalized Skills (lowercase, deduplicated)
    required_skills TEXT[] NOT NULL DEFAULT '{}',
    preferred_skills TEXT[] NOT NULL DEFAULT '{}',
    
    -- Technologies by Category
    programming_languages TEXT[] NOT NULL DEFAULT '{}',
    frameworks TEXT[] NOT NULL DEFAULT '{}',
    databases TEXT[] NOT NULL DEFAULT '{}',
    cloud_platforms TEXT[] NOT NULL DEFAULT '{}',
    devops_tools TEXT[] NOT NULL DEFAULT '{}',
    
    -- Experience Requirements
    required_years_experience INTEGER,
    seniority_level TEXT, -- 'junior', 'mid', 'senior', 'lead', 'principal'
    experience_domains TEXT[] NOT NULL DEFAULT '{}', -- ['backend', 'frontend', 'devops', 'security']
    
    -- Qualifications
    required_qualifications TEXT[] NOT NULL DEFAULT '{}',
    preferred_qualifications TEXT[] NOT NULL DEFAULT '{}',
    required_certifications TEXT[] NOT NULL DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT job_profiles_job_id_unique UNIQUE(job_id),
    CONSTRAINT job_profiles_seniority_check CHECK (
        seniority_level IS NULL OR 
        seniority_level IN ('junior', 'mid', 'senior', 'lead', 'principal')
    )
);

-- Indexes for job_profiles
CREATE INDEX idx_job_profiles_job_id ON job_profiles(job_id);
CREATE INDEX idx_job_profiles_seniority ON job_profiles(seniority_level) WHERE seniority_level IS NOT NULL;

-- ============================================================================
-- CV PROFILES TABLE
-- ============================================================================
-- Stores normalized, structured CV capabilities extracted from parsed CV sections
-- One profile per CV, created after CV parsing

CREATE TABLE cv_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    
    -- Normalized Skills (lowercase, deduplicated)
    technical_skills TEXT[] NOT NULL DEFAULT '{}',
    soft_skills TEXT[] NOT NULL DEFAULT '{}',
    
    -- Technologies by Category
    programming_languages TEXT[] NOT NULL DEFAULT '{}',
    frameworks TEXT[] NOT NULL DEFAULT '{}',
    databases TEXT[] NOT NULL DEFAULT '{}',
    cloud_platforms TEXT[] NOT NULL DEFAULT '{}',
    devops_tools TEXT[] NOT NULL DEFAULT '{}',
    
    -- Experience Profile
    total_years_experience INTEGER,
    seniority_level TEXT, -- 'junior', 'mid', 'senior', 'lead', 'principal'
    experience_domains TEXT[] NOT NULL DEFAULT '{}', -- ['backend', 'cybersecurity']
    role_history TEXT[] NOT NULL DEFAULT '{}', -- ['Software Engineer', 'Security Engineer']
    
    -- Qualifications
    degrees TEXT[] NOT NULL DEFAULT '{}',
    certifications TEXT[] NOT NULL DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT cv_profiles_cv_id_unique UNIQUE(cv_id),
    CONSTRAINT cv_profiles_seniority_check CHECK (
        seniority_level IS NULL OR 
        seniority_level IN ('junior', 'mid', 'senior', 'lead', 'principal')
    )
);

-- Indexes for cv_profiles
CREATE INDEX idx_cv_profiles_cv_id ON cv_profiles(cv_id);
CREATE INDEX idx_cv_profiles_seniority ON cv_profiles(seniority_level) WHERE seniority_level IS NOT NULL;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to job_profiles
CREATE TRIGGER update_job_profiles_updated_at
    BEFORE UPDATE ON job_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to cv_profiles
CREATE TRIGGER update_cv_profiles_updated_at
    BEFORE UPDATE ON cv_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE job_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_profiles ENABLE ROW LEVEL SECURITY;

-- Job Profiles: Users can only access profiles for their own jobs
CREATE POLICY "Users can view their own job profiles"
    ON job_profiles FOR SELECT
    USING (
        job_id IN (
            SELECT id FROM jobs WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their own job profiles"
    ON job_profiles FOR INSERT
    WITH CHECK (
        job_id IN (
            SELECT id FROM jobs WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own job profiles"
    ON job_profiles FOR UPDATE
    USING (
        job_id IN (
            SELECT id FROM jobs WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their own job profiles"
    ON job_profiles FOR DELETE
    USING (
        job_id IN (
            SELECT id FROM jobs WHERE user_id = auth.uid()
        )
    );

-- CV Profiles: Users can only access profiles for their own CVs
CREATE POLICY "Users can view their own cv profiles"
    ON cv_profiles FOR SELECT
    USING (
        cv_id IN (
            SELECT id FROM cvs WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their own cv profiles"
    ON cv_profiles FOR INSERT
    WITH CHECK (
        cv_id IN (
            SELECT id FROM cvs WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own cv profiles"
    ON cv_profiles FOR UPDATE
    USING (
        cv_id IN (
            SELECT id FROM cvs WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their own cv profiles"
    ON cv_profiles FOR DELETE
    USING (
        cv_id IN (
            SELECT id FROM cvs WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE job_profiles IS 'Normalized, structured job requirements for deterministic matching';
COMMENT ON TABLE cv_profiles IS 'Normalized, structured CV capabilities for deterministic matching';

COMMENT ON COLUMN job_profiles.required_skills IS 'Normalized required skills (lowercase, no duplicates)';
COMMENT ON COLUMN job_profiles.preferred_skills IS 'Normalized preferred/nice-to-have skills';
COMMENT ON COLUMN job_profiles.seniority_level IS 'Inferred seniority level from job description';
COMMENT ON COLUMN job_profiles.experience_domains IS 'Required experience areas (backend, frontend, etc.)';

COMMENT ON COLUMN cv_profiles.technical_skills IS 'Normalized technical skills from CV (lowercase, no duplicates)';
COMMENT ON COLUMN cv_profiles.total_years_experience IS 'Total years of professional experience';
COMMENT ON COLUMN cv_profiles.seniority_level IS 'Inferred seniority level from experience and titles';
COMMENT ON COLUMN cv_profiles.role_history IS 'List of job titles held';