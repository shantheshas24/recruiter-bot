-- ============================================================================
-- SQL Analytics & Data Quality Challenges (Advanced PostgreSQL Queries)
-- ============================================================================
-- Analytical queries for candidate pipelines, conversion metrics, and data quality.
-- Each query includes documented approach, trap analysis, and expected output.
-- ============================================================================

-- =============================================
-- Schema Definition
-- =============================================

CREATE TABLE IF NOT EXISTS recruiters (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  region VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS job_postings (
  id INT PRIMARY KEY,
  title VARCHAR(100),
  recruiter_id INT,
  department VARCHAR(50),
  opened_date DATE,
  status VARCHAR(20) -- 'open', 'closed', 'on_hold'
);

CREATE TABLE IF NOT EXISTS applicants (
  id INT PRIMARY KEY,
  full_name VARCHAR(100),
  email VARCHAR(100),
  source VARCHAR(50), -- nullable
  applied_date DATE
);

CREATE TABLE IF NOT EXISTS interviews (
  id INT PRIMARY KEY,
  applicant_id INT,
  job_posting_id INT,
  stage VARCHAR(20),      -- 'Screen', 'Technical', 'Final'
  scheduled_date DATE,
  outcome VARCHAR(20)     -- 'passed', 'failed', 'no_show', NULL (pending)
);

-- =============================================
-- Seed Data
-- =============================================

INSERT INTO recruiters VALUES
(1, 'Priya Shah', 'APAC'),
(2, 'Daniel Ortiz', 'NA'),
(3, 'Fatima Al-Sayed', 'EMEA'),
(4, 'Wei Zhang', 'APAC'),
(5, 'Grace Okafor', 'EMEA')
ON CONFLICT (id) DO NOTHING;

INSERT INTO job_postings VALUES
(1, 'Backend Engineer I', 1, 'Engineering', '2026-01-05', 'open'),
(2, 'Backend Engineer I', 2, 'Engineering', '2026-01-10', 'open'),
(3, 'Data Analyst', 3, 'Data', '2026-01-08', 'closed'),
(4, 'Backend Engineer II', 1, 'Engineering', '2026-02-01', 'open'),
(5, 'DevOps Engineer', 4, 'Infrastructure', '2026-01-20', 'open'),
(6, 'Data Analyst', 5, 'Data', '2026-02-05', 'on_hold'),
(7, 'Backend Engineer I', 2, 'Engineering', '2026-02-15', 'closed')
ON CONFLICT (id) DO NOTHING;

INSERT INTO applicants VALUES
(1, 'Ananya Rao', 'ananya.rao@mail.com', 'LinkedIn', '2026-01-06'),
(2, 'Ananya Rao', 'Ananya.Rao@mail.com', 'Referral', '2026-02-04'),
(3, 'Ben Turner', 'ben.turner@mail.com', 'Job Board', '2026-01-07'),
(4, 'Chloe Martin', 'chloe.martin@mail.com', NULL, '2026-01-09'),
(5, 'Devansh Patel', 'devansh.patel@mail.com', 'LinkedIn', '2026-01-11'),
(6, 'Elena Popescu', 'elena.popescu@mail.com', 'Referral', '2026-01-12'),
(7, 'Farid Haidari', 'farid.haidari@mail.com', 'Job Board', '2026-01-13'),
(8, 'Grace Lin', 'grace.lin@mail.com', 'LinkedIn', '2026-01-15'),
(9, 'Hassan Malik', 'hassan.malik@mail.com', NULL, '2026-01-16'),
(10, 'Isla Fraser', 'isla.fraser@mail.com', 'Referral', '2026-01-18'),
(11, 'Jonas Weber', 'jonas.weber@mail.com', 'Job Board', '2026-02-10')
ON CONFLICT (id) DO NOTHING;

INSERT INTO interviews VALUES
(1, 1, 1, 'Screen', '2026-01-10', 'passed'),
(2, 1, 1, 'Technical', '2026-01-15', 'passed'),
(3, 1, 1, 'Final', '2026-01-22', 'passed'),
(4, 2, 4, 'Screen', '2026-02-05', 'passed'),
(5, 3, 1, 'Screen', '2026-01-11', 'passed'),
(6, 3, 1, 'Technical', '2026-01-16', 'failed'),
(7, 3, 3, 'Final', '2026-01-28', 'passed'),
(8, 4, 1, 'Screen', '2026-01-12', 'passed'),
(9, 4, 1, 'Final', '2026-01-24', 'failed'),
(10, 5, 2, 'Screen', '2026-01-14', 'passed'),
(11, 5, 2, 'Technical', '2026-01-19', 'passed'),
(12, 5, 2, 'Final', '2026-01-25', 'passed'),
(13, 6, 2, 'Screen', '2026-01-15', 'passed'),
(14, 6, 2, 'Final', '2026-01-26', 'failed'),
(15, 7, 2, 'Screen', '2026-01-16', 'no_show'),
(16, 8, 4, 'Screen', '2026-02-03', 'passed'),
(17, 8, 4, 'Technical', '2026-02-08', 'passed'),
(18, 8, 4, 'Final', '2026-02-12', 'passed'),
(19, 9, 4, 'Screen', '2026-02-04', 'passed'),
(20, 9, 4, 'Final', '2026-02-14', 'passed'),
(21, 10, 5, 'Screen', '2026-01-22', 'passed'),
(22, 10, 5, 'Technical', '2026-01-28', NULL),
(23, 11, 7, 'Final', '2026-02-20', 'passed'),
(24, 6, 7, 'Final', '2026-02-21', 'failed')
ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- QUESTION 1: List all currently open job postings, along with the name of
--             the recruiter who owns each one.
-- ============================================================================
-- Approach: Simple INNER JOIN on recruiter_id, filtered by status = 'open'.
-- Result: 4 rows (job_postings 1, 2, 4, 5).

SELECT
    jp.id          AS job_posting_id,
    jp.title       AS job_title,
    jp.department,
    jp.opened_date,
    r.name         AS recruiter_name,
    r.region       AS recruiter_region
FROM job_postings jp
INNER JOIN recruiters r ON r.id = jp.recruiter_id
WHERE jp.status = 'open'
ORDER BY jp.id;


-- ============================================================================
-- QUESTION 2: For each job posting, how many applicants reached the Final
--             interview stage?
-- ============================================================================
-- Approach: LEFT JOIN job_postings to interviews filtered to stage = 'Final',
--           then COUNT DISTINCT applicant_id. LEFT JOIN ensures jobs with
--           zero Final-stage applicants still appear (with count 0).
-- Result: All 7 job postings, with counts.

SELECT
    jp.id                                    AS job_posting_id,
    jp.title                                 AS job_title,
    COUNT(DISTINCT i.applicant_id)           AS final_stage_applicants
FROM job_postings jp
LEFT JOIN interviews i
    ON i.job_posting_id = jp.id
    AND i.stage = 'Final'
GROUP BY jp.id, jp.title
ORDER BY jp.id;


-- ============================================================================
-- QUESTION 3: Find every person who effectively applied to more than one
--             job posting.
-- ============================================================================
-- TRAP: Ananya Rao appears as two separate applicant rows (id=1 and id=2)
-- with different email capitalization ('ananya.rao@mail.com' vs
-- 'Ananya.Rao@mail.com'). These represent the SAME person.
--
-- Approach:
--   1. Normalize email with LOWER(TRIM(email)) to unify duplicate identities.
--   2. Use interviews to find which job_postings each normalized applicant
--      is associated with (interviews link applicant_id → job_posting_id).
--   3. COUNT DISTINCT job_posting_id per normalized email.
--   4. HAVING > 1 means they effectively applied to multiple jobs.
--
-- Why use interviews, not just applicants? The applicants table has no
-- direct job reference. The interview records establish which job postings
-- each applicant engaged with.
--
-- Result: Ananya Rao (jobs 1 and 4), Ben Turner (jobs 1 and 3),
--         Elena Popescu (jobs 2 and 7).

SELECT
    LOWER(TRIM(a.email))                     AS normalized_email,
    MIN(a.full_name)                         AS applicant_name,
    COUNT(DISTINCT i.job_posting_id)         AS distinct_jobs_applied,
    ARRAY_AGG(DISTINCT i.job_posting_id ORDER BY i.job_posting_id) AS job_posting_ids
FROM applicants a
INNER JOIN interviews i ON i.applicant_id = a.id
GROUP BY LOWER(TRIM(a.email))
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY normalized_email;


-- ============================================================================
-- QUESTION 4: For each recruiter, compute their Final-stage conversion rate
--             (passed ÷ total Final-stage interviews), but only include
--             recruiters with at least 3 Final-stage interviews.
-- ============================================================================
-- Approach:
--   1. Join interviews (stage='Final') → job_postings → recruiters.
--   2. Count total Final interviews and passed Final interviews per recruiter.
--   3. Conversion rate = passed / total × 100.
--   4. HAVING total >= 3 filters out recruiters without enough data.
--
-- Counting logic: outcome = 'passed' counts as a pass. 'failed', 'no_show',
-- and NULL do not count as passed but DO count toward the total.
--
-- Result: Only recruiters with 3+ Final interviews are included.
--   - Priya Shah:   3 Final interviews (jobs 1, 4) → Ananya passed, Chloe failed,
--                   Grace Lin passed, Hassan passed → 3 passed / 4 total = 75%
--     Wait, let me recount: Priya owns jobs 1 and 4.
--     Final interviews for job 1: interview 3 (applicant 1, passed), interview 9 (applicant 4, failed) = 2
--     Final interviews for job 4: interview 18 (applicant 8, passed), interview 20 (applicant 9, passed) = 2
--     Total = 4, passed = 3 → 75%
--   - Daniel Ortiz: owns jobs 2 and 7.
--     Final for job 2: interview 12 (applicant 5, passed), interview 14 (applicant 6, failed) = 2
--     Final for job 7: interview 23 (applicant 11, passed), interview 24 (applicant 6, failed) = 2
--     Total = 4, passed = 2 → 50%

SELECT
    r.id                                     AS recruiter_id,
    r.name                                   AS recruiter_name,
    COUNT(*)                                 AS total_final_interviews,
    COUNT(*) FILTER (WHERE i.outcome = 'passed')
                                             AS passed_final_interviews,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE i.outcome = 'passed') / COUNT(*),
        2
    )                                        AS conversion_rate_pct
FROM interviews i
INNER JOIN job_postings jp ON jp.id = i.job_posting_id
INNER JOIN recruiters r    ON r.id = jp.recruiter_id
WHERE i.stage = 'Final'
GROUP BY r.id, r.name
HAVING COUNT(*) >= 3
ORDER BY conversion_rate_pct DESC, r.name;


-- ============================================================================
-- QUESTION 5 (Bonus): Using a window function, find the recruiter with the
--                      most successful placements (passed at Final stage)
--                      per department.
-- ============================================================================
-- Approach:
--   1. Count passed Final interviews per (recruiter, department).
--   2. Use RANK() window function partitioned by department, ordered by
--      placement count DESC.
--   3. Filter to rank = 1 (top recruiter per department).
--
-- Tie-handling decision: RANK() is chosen over ROW_NUMBER() because if two
-- recruiters have the same number of placements in a department, both should
-- be reported. ROW_NUMBER() would arbitrarily exclude one. DENSE_RANK() would
-- also work identically here since we only filter rank = 1, but RANK() is
-- the most semantically correct choice for "most placements" ties.

WITH placements AS (
    SELECT
        r.id                         AS recruiter_id,
        r.name                       AS recruiter_name,
        jp.department,
        COUNT(*)                     AS successful_placements
    FROM interviews i
    INNER JOIN job_postings jp ON jp.id = i.job_posting_id
    INNER JOIN recruiters r    ON r.id = jp.recruiter_id
    WHERE i.stage = 'Final'
      AND i.outcome = 'passed'
    GROUP BY r.id, r.name, jp.department
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY department
            ORDER BY successful_placements DESC
        ) AS dept_rank
    FROM placements
)
SELECT
    department,
    recruiter_id,
    recruiter_name,
    successful_placements,
    dept_rank
FROM ranked
WHERE dept_rank = 1
ORDER BY department, recruiter_name;
