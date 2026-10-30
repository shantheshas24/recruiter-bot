-- ============================================================================
-- RecruiterFlow Bot — Database Schema (DDL)
-- ============================================================================
-- Design: 3NF normalized schema with a shared skills vocabulary table.
-- Skills are referenced by both candidates and jobs through junction tables,
-- ensuring consistent naming and enabling efficient set-intersection queries
-- for the matching engine.
-- ============================================================================

-- Drop tables in reverse dependency order for idempotent re-runs
DROP TABLE IF EXISTS job_culture_keywords CASCADE;
DROP TABLE IF EXISTS job_required_skills  CASCADE;
DROP TABLE IF EXISTS candidate_traits     CASCADE;
DROP TABLE IF EXISTS candidate_skills     CASCADE;
DROP TABLE IF EXISTS jobs                 CASCADE;
DROP TABLE IF EXISTS candidates           CASCADE;
DROP TABLE IF EXISTS skills               CASCADE;

-- ============================================================================
-- Skills: shared vocabulary for both candidates and jobs
-- ============================================================================
-- Rationale: A single source of truth for skill names prevents mismatches
-- from typos or inconsistent casing. Both candidate_skills and
-- job_required_skills reference this table via FK.
-- ============================================================================
CREATE TABLE skills (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================================
-- Candidates
-- ============================================================================
-- availability is constrained to known values; experience must be non-negative.
-- quirk is a fun description stored as text (not used for scoring).
-- ============================================================================
CREATE TABLE candidates (
    id               SERIAL       PRIMARY KEY,
    name             VARCHAR(150) NOT NULL UNIQUE,
    experience_years INTEGER      NOT NULL CHECK (experience_years >= 0),
    availability     VARCHAR(20)  NOT NULL DEFAULT 'immediate'
                     CHECK (availability IN ('immediate', '2 weeks', 'not looking')),
    quirk            TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Candidate ↔ Skill (many-to-many junction)
-- ============================================================================
CREATE TABLE candidate_skills (
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id     INTEGER NOT NULL REFERENCES skills(id)     ON DELETE CASCADE,
    PRIMARY KEY (candidate_id, skill_id)
);

-- ============================================================================
-- Candidate traits (one-to-many)
-- ============================================================================
-- Traits are candidate-specific descriptors (e.g. "analytical", "blunt").
-- They are NOT a shared vocabulary — different candidates may use the same
-- word, but there's no master "traits" table. They are matched against
-- job culture keywords by normalized string comparison.
-- ============================================================================
CREATE TABLE candidate_traits (
    id           SERIAL       PRIMARY KEY,
    candidate_id INTEGER      NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    trait         VARCHAR(100) NOT NULL,
    UNIQUE (candidate_id, trait)
);

-- ============================================================================
-- Jobs
-- ============================================================================
CREATE TABLE jobs (
    id              SERIAL       PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    min_experience  INTEGER      NOT NULL CHECK (min_experience >= 0),
    tagline         TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Job ↔ Required Skill (many-to-many junction)
-- ============================================================================
CREATE TABLE job_required_skills (
    job_id   INTEGER NOT NULL REFERENCES jobs(id)   ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, skill_id)
);

-- ============================================================================
-- Job culture keywords (one-to-many)
-- ============================================================================
-- Culture keywords are job-specific and matched against candidate traits
-- using normalized string comparison during scoring.
-- ============================================================================
CREATE TABLE job_culture_keywords (
    id      SERIAL       PRIMARY KEY,
    job_id  INTEGER      NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    UNIQUE (job_id, keyword)
);
