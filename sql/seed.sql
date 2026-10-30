-- ============================================================================
-- RecruiterFlow Bot — Seed Data
-- ============================================================================
-- Initial seed dataset for candidates, jobs, skills, and junction tables.
-- This script is idempotent: uses ON CONFLICT DO NOTHING throughout.
-- ============================================================================

-- ============================================================================
-- Skills (union of all candidate skills and job required skills)
-- ============================================================================
INSERT INTO skills (name) VALUES
    ('deduction'),
    ('pattern-recognition'),
    ('forensics'),
    ('research'),
    ('time-management'),
    ('public-speaking'),
    ('systems-design'),
    ('rapid-prototyping'),
    ('leadership'),
    ('project-management'),
    ('stakeholder-management'),
    ('woodworking'),
    ('minimalism'),
    ('negotiation'),
    ('chemistry'),
    ('persuasion'),
    ('resourcefulness'),
    ('theoretical-analysis'),
    ('precision'),
    ('strategy'),
    ('crisis-management'),
    ('sales'),
    ('team-building'),
    ('optimism'),
    ('mentorship'),
    ('security'),
    ('loyalty')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- Candidates (15 total, exact from PDF)
-- ============================================================================
INSERT INTO candidates (name, experience_years, availability, quirk) VALUES
    ('Sherlock H.',  8,  'immediate',   'Solves problems by eliminating the impossible; occasionally insufferable in standups.'),
    ('Hermione G.',  4,  '2 weeks',     'Reads the entire documentation before writing a single line of code.'),
    ('Tony S.',      12, 'not looking', 'Ships an MVP overnight, refuses to write tests.'),
    ('Leslie K.',    6,  'immediate',   'Has a binder for everything, including the binder.'),
    ('Ron S.',       15, 'not looking', 'Refuses to use more than one monitor.'),
    ('Rick S.',      20, 'immediate',   'Solution works, mechanism deeply concerning.'),
    ('Elle W.',      3,  'immediate',   'Underestimated in every standup, correct in every retro.'),
    ('MacGyver',     10, '2 weeks',     'Fixes production outages with duct tape and a paperclip metaphor.'),
    ('Sheldon C.',   9,  'immediate',   'Correct 95% of the time, insufferable 100% of the time.'),
    ('Katniss E.',   5,  'immediate',   'Excellent under pressure, terrible with public speaking.'),
    ('Michael S.',   11, 'not looking', 'World''s best boss, according to a mug he bought himself.'),
    ('Olivia P.',    13, '2 weeks',     'Handles it. Whatever it is.'),
    ('Ted L.',       7,  'immediate',   'Turns every technical setback into a folksy metaphor.'),
    ('Miranda P.',   18, 'not looking', 'Reviews every PR personally. Says nothing. Everyone panics.'),
    ('Dwight S.',    9,  'immediate',   'Assistant to the regional backend engineer.')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- Candidate Skills
-- ============================================================================
-- Helper: we use subqueries to resolve IDs so the seed file doesn't depend
-- on auto-increment ordering.
-- ============================================================================

-- Sherlock H.: deduction, pattern-recognition, forensics
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Sherlock H.' AND s.name IN ('deduction', 'pattern-recognition', 'forensics')
ON CONFLICT DO NOTHING;

-- Hermione G.: research, time-management, public-speaking
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Hermione G.' AND s.name IN ('research', 'time-management', 'public-speaking')
ON CONFLICT DO NOTHING;

-- Tony S.: systems-design, rapid-prototyping, leadership
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Tony S.' AND s.name IN ('systems-design', 'rapid-prototyping', 'leadership')
ON CONFLICT DO NOTHING;

-- Leslie K.: project-management, stakeholder-management, public-speaking
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Leslie K.' AND s.name IN ('project-management', 'stakeholder-management', 'public-speaking')
ON CONFLICT DO NOTHING;

-- Ron S.: woodworking, minimalism, negotiation
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Ron S.' AND s.name IN ('woodworking', 'minimalism', 'negotiation')
ON CONFLICT DO NOTHING;

-- Rick S.: systems-design, rapid-prototyping, chemistry
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Rick S.' AND s.name IN ('systems-design', 'rapid-prototyping', 'chemistry')
ON CONFLICT DO NOTHING;

-- Elle W.: persuasion, research, public-speaking
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Elle W.' AND s.name IN ('persuasion', 'research', 'public-speaking')
ON CONFLICT DO NOTHING;

-- MacGyver: rapid-prototyping, resourcefulness, chemistry, systems-design
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'MacGyver' AND s.name IN ('rapid-prototyping', 'resourcefulness', 'chemistry', 'systems-design')
ON CONFLICT DO NOTHING;

-- Sheldon C.: theoretical-analysis, pattern-recognition, research
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Sheldon C.' AND s.name IN ('theoretical-analysis', 'pattern-recognition', 'research')
ON CONFLICT DO NOTHING;

-- Katniss E.: precision, strategy, crisis-management
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Katniss E.' AND s.name IN ('precision', 'strategy', 'crisis-management')
ON CONFLICT DO NOTHING;

-- Michael S.: sales, public-speaking, team-building
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Michael S.' AND s.name IN ('sales', 'public-speaking', 'team-building')
ON CONFLICT DO NOTHING;

-- Olivia P.: crisis-management, negotiation, strategy, leadership
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Olivia P.' AND s.name IN ('crisis-management', 'negotiation', 'strategy', 'leadership')
ON CONFLICT DO NOTHING;

-- Ted L.: team-building, optimism, mentorship, public-speaking
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Ted L.' AND s.name IN ('team-building', 'optimism', 'mentorship', 'public-speaking')
ON CONFLICT DO NOTHING;

-- Miranda P.: leadership, negotiation, stakeholder-management, precision
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Miranda P.' AND s.name IN ('leadership', 'negotiation', 'stakeholder-management', 'precision')
ON CONFLICT DO NOTHING;

-- Dwight S.: sales, negotiation, security, loyalty
INSERT INTO candidate_skills (candidate_id, skill_id)
SELECT c.id, s.id FROM candidates c, skills s
WHERE c.name = 'Dwight S.' AND s.name IN ('sales', 'negotiation', 'security', 'loyalty')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Candidate Traits
-- ============================================================================

-- Sherlock H.: analytical, blunt
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('analytical'), ('blunt')) AS t(trait)
WHERE c.name = 'Sherlock H.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Hermione G.: detail-oriented, overachiever
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('detail-oriented'), ('overachiever')) AS t(trait)
WHERE c.name = 'Hermione G.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Tony S.: confident, innovative
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('confident'), ('innovative')) AS t(trait)
WHERE c.name = 'Tony S.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Leslie K.: tenacious, organized
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('tenacious'), ('organized')) AS t(trait)
WHERE c.name = 'Leslie K.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Ron S.: stubborn, principled
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('stubborn'), ('principled')) AS t(trait)
WHERE c.name = 'Ron S.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Rick S.: genius, reckless
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('genius'), ('reckless')) AS t(trait)
WHERE c.name = 'Rick S.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Elle W.: optimistic, sharp
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('optimistic'), ('sharp')) AS t(trait)
WHERE c.name = 'Elle W.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- MacGyver: calm, improviser
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('calm'), ('improviser')) AS t(trait)
WHERE c.name = 'MacGyver'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Sheldon C.: rigid, brilliant
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('rigid'), ('brilliant')) AS t(trait)
WHERE c.name = 'Sheldon C.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Katniss E.: resilient, decisive
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('resilient'), ('decisive')) AS t(trait)
WHERE c.name = 'Katniss E.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Michael S.: enthusiastic, chaotic
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('enthusiastic'), ('chaotic')) AS t(trait)
WHERE c.name = 'Michael S.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Olivia P.: decisive, intense
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('decisive'), ('intense')) AS t(trait)
WHERE c.name = 'Olivia P.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Ted L.: empathetic, persistent
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('empathetic'), ('persistent')) AS t(trait)
WHERE c.name = 'Ted L.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Miranda P.: demanding, decisive
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('demanding'), ('decisive')) AS t(trait)
WHERE c.name = 'Miranda P.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- Dwight S.: intense, loyal
INSERT INTO candidate_traits (candidate_id, trait)
SELECT c.id, t.trait FROM candidates c, (VALUES ('intense'), ('loyal')) AS t(trait)
WHERE c.name = 'Dwight S.'
ON CONFLICT (candidate_id, trait) DO NOTHING;

-- ============================================================================
-- Jobs (6 total, exact from PDF)
-- ============================================================================
INSERT INTO jobs (title, min_experience, tagline) VALUES
    ('Backend Detective',                3,  'We have a bug. We have no leads. We have you.'),
    ('Rapid Prototyping Engineer',       2,  'Ship first, document never (kidding — please document).'),
    ('Developer Relations Lead',         2,  'Explain complex things to confused humans, cheerfully.'),
    ('Engineering Manager, Chaos Team',  5,  'Herd cats. The cats are senior engineers.'),
    ('Incident Commander',               4,  '3am page. You''re the one who picks up.'),
    ('Sales Engineer',                   3,  'Sell the vision, then go build it.')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Job Required Skills
-- ============================================================================

-- Backend Detective: deduction, pattern-recognition, forensics
INSERT INTO job_required_skills (job_id, skill_id)
SELECT j.id, s.id FROM jobs j, skills s
WHERE j.title = 'Backend Detective' AND s.name IN ('deduction', 'pattern-recognition', 'forensics')
ON CONFLICT DO NOTHING;

-- Rapid Prototyping Engineer: rapid-prototyping, systems-design
INSERT INTO job_required_skills (job_id, skill_id)
SELECT j.id, s.id FROM jobs j, skills s
WHERE j.title = 'Rapid Prototyping Engineer' AND s.name IN ('rapid-prototyping', 'systems-design')
ON CONFLICT DO NOTHING;

-- Developer Relations Lead: public-speaking, research
INSERT INTO job_required_skills (job_id, skill_id)
SELECT j.id, s.id FROM jobs j, skills s
WHERE j.title = 'Developer Relations Lead' AND s.name IN ('public-speaking', 'research')
ON CONFLICT DO NOTHING;

-- Engineering Manager, Chaos Team: team-building, stakeholder-management, leadership
INSERT INTO job_required_skills (job_id, skill_id)
SELECT j.id, s.id FROM jobs j, skills s
WHERE j.title = 'Engineering Manager, Chaos Team' AND s.name IN ('team-building', 'stakeholder-management', 'leadership')
ON CONFLICT DO NOTHING;

-- Incident Commander: crisis-management, strategy, negotiation
INSERT INTO job_required_skills (job_id, skill_id)
SELECT j.id, s.id FROM jobs j, skills s
WHERE j.title = 'Incident Commander' AND s.name IN ('crisis-management', 'strategy', 'negotiation')
ON CONFLICT DO NOTHING;

-- Sales Engineer: sales, public-speaking, negotiation
INSERT INTO job_required_skills (job_id, skill_id)
SELECT j.id, s.id FROM jobs j, skills s
WHERE j.title = 'Sales Engineer' AND s.name IN ('sales', 'public-speaking', 'negotiation')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Job Culture Keywords
-- ============================================================================

-- Backend Detective: analytical, autonomous
INSERT INTO job_culture_keywords (job_id, keyword)
SELECT j.id, k.keyword FROM jobs j, (VALUES ('analytical'), ('autonomous')) AS k(keyword)
WHERE j.title = 'Backend Detective'
ON CONFLICT (job_id, keyword) DO NOTHING;

-- Rapid Prototyping Engineer: innovative, fast-paced
INSERT INTO job_culture_keywords (job_id, keyword)
SELECT j.id, k.keyword FROM jobs j, (VALUES ('innovative'), ('fast-paced')) AS k(keyword)
WHERE j.title = 'Rapid Prototyping Engineer'
ON CONFLICT (job_id, keyword) DO NOTHING;

-- Developer Relations Lead: energetic, curious
INSERT INTO job_culture_keywords (job_id, keyword)
SELECT j.id, k.keyword FROM jobs j, (VALUES ('energetic'), ('curious')) AS k(keyword)
WHERE j.title = 'Developer Relations Lead'
ON CONFLICT (job_id, keyword) DO NOTHING;

-- Engineering Manager, Chaos Team: empathetic, organized
INSERT INTO job_culture_keywords (job_id, keyword)
SELECT j.id, k.keyword FROM jobs j, (VALUES ('empathetic'), ('organized')) AS k(keyword)
WHERE j.title = 'Engineering Manager, Chaos Team'
ON CONFLICT (job_id, keyword) DO NOTHING;

-- Incident Commander: decisive, calm-under-pressure
INSERT INTO job_culture_keywords (job_id, keyword)
SELECT j.id, k.keyword FROM jobs j, (VALUES ('decisive'), ('calm-under-pressure')) AS k(keyword)
WHERE j.title = 'Incident Commander'
ON CONFLICT (job_id, keyword) DO NOTHING;

-- Sales Engineer: enthusiastic, persistent
INSERT INTO job_culture_keywords (job_id, keyword)
SELECT j.id, k.keyword FROM jobs j, (VALUES ('enthusiastic'), ('persistent')) AS k(keyword)
WHERE j.title = 'Sales Engineer'
ON CONFLICT (job_id, keyword) DO NOTHING;
