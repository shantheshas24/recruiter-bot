-- ============================================================================
-- RecruiterFlow Bot — Indexes
-- ============================================================================
-- These indexes target the most common query patterns in the matching engine:
--   1. Looking up candidate/job skills via junction tables (FK indexes)
--   2. Filtering candidates by availability
--   3. Looking up traits/keywords for culture matching
--
-- PostgreSQL automatically indexes PRIMARY KEY columns. UNIQUE constraints
-- also create indexes. So we only add indexes for FK columns and
-- frequently filtered non-key columns.
-- ============================================================================

-- Junction table FK indexes (PostgreSQL does NOT auto-index FK columns)
CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill_id
    ON candidate_skills (skill_id);

CREATE INDEX IF NOT EXISTS idx_job_required_skills_skill_id
    ON job_required_skills (skill_id);

-- Trait lookups by candidate (for matching engine)
CREATE INDEX IF NOT EXISTS idx_candidate_traits_candidate_id
    ON candidate_traits (candidate_id);

-- Culture keyword lookups by job (for matching engine)
CREATE INDEX IF NOT EXISTS idx_job_culture_keywords_job_id
    ON job_culture_keywords (job_id);

-- Candidate availability filter (used in match queries)
CREATE INDEX IF NOT EXISTS idx_candidates_availability
    ON candidates (availability);

-- Job minimum experience filter
CREATE INDEX IF NOT EXISTS idx_jobs_min_experience
    ON jobs (min_experience);
