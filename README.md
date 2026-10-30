# RecruiterFlow Bot — Candidate-Job Matching Engine

An intelligent, explainable candidate-job matching engine built with FastAPI and PostgreSQL.

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Architecture](#architecture)
- [Technology Choices](#technology-choices)
- [Database Schema](#database-schema)
- [Matching Algorithm](#matching-algorithm)
- [Engineering Decisions and Trade-offs](#engineering-decisions-and-trade-offs)
- [Edge Case Handling](#edge-case-handling)
- [API Endpoints](#api-endpoints)
- [Installation & Setup](#installation--setup)
- [Running Tests](#running-tests)
- [SQL Analytics Challenges](#sql-analytics-challenges)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)

---

## Project Overview

RecruiterFlow Bot is a backend service that ingests candidate profiles and job openings, then ranks the best matches using a multi-factor, explainable scoring algorithm. The matching engine considers skill overlap, experience fit, culture alignment, and candidate availability — producing transparent, deterministic rankings with full score breakdowns.

The system is designed around three principles:
1. **Explainability** — every score can be traced to its components
2. **Correctness** — deterministic results, no hidden randomness
3. **Defensibility** — every design decision has a documented rationale

## Problem Statement

Given a set of fictional candidates (Sherlock Holmes, Hermione Granger, etc.) and job openings (Backend Detective, Incident Commander, etc.), build a backend that:
- Ingests and stores candidate/job data
- Computes match scores using a multi-factor algorithm
- Returns ranked results with explanations
- Handles edge cases gracefully

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │Candidates│  │   Jobs   │  │     Matching       │  │
│  │   API    │  │   API    │  │       API          │  │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘  │
│       │              │                 │             │
│  ┌────┴──────────────┴─────────────────┴──────────┐  │
│  │              Service Layer                     │  │
│  │  ┌──────────────────┐  ┌────────────────────┐  │  │
│  │  │ Matching Engine  │  │  Scoring Engine    │  │  │
│  │  │ (orchestration)  │  │  (pure functions)  │  │  │
│  │  └────────┬─────────┘  └────────────────────┘  │  │
│  └───────────┼────────────────────────────────────┘  │
│  ┌───────────┴────────────────────────────────────┐  │
│  │           Repository Layer (raw SQL)           │  │
│  │  ┌──────────────┐  ┌────────────────────────┐  │  │
│  │  │candidate_repo│  │       job_repo         │  │  │
│  │  └──────────────┘  └────────────────────────┘  │  │
│  └────────────────────────┬───────────────────────┘  │
└───────────────────────────┼─────────────────────────┘
                            │
                   ┌────────┴────────┐
                   │   PostgreSQL    │
                   │  (psycopg 3)   │
                   └─────────────────┘
```

**Layer responsibilities:**
- **API Layer** — thin HTTP handlers, request validation, response shaping
- **Service Layer** — matching orchestration + pure scoring functions
- **Repository Layer** — handwritten SQL with parameterized queries
- **Database** — PostgreSQL with connection pooling

## Technology Choices

| Technology | Purpose | Why |
|-----------|---------|-----|
| **Python 3.12** | Runtime | Modern features (type unions, match statements) |
| **FastAPI** | REST framework | Auto-generated OpenAPI docs, Pydantic integration, async support |
| **PostgreSQL 16** | Database | CHECK constraints, ARRAY_AGG, window functions, EXPLAIN ANALYZE |
| **psycopg 3** | DB driver | Modern async-capable driver with connection pooling |
| **Pydantic v2** | Validation | Type-safe request/response schemas with examples |
| **pytest** | Testing | Clean fixtures, parametrized tests |
| **Docker Compose** | Local infra | Reproducible PostgreSQL setup for dev and test |

## Database Schema

### Entity-Relationship Diagram

```
┌──────────────┐     ┌──────────────────┐     ┌──────────┐
│  candidates  │────<│ candidate_skills  │>────│  skills  │
│──────────────│     │──────────────────│     │──────────│
│ id (PK)      │     │ candidate_id (FK)│     │ id (PK)  │
│ name (UQ)    │     │ skill_id (FK)    │     │ name (UQ)│
│ experience   │     │ PK(cand,skill)   │     └──────────┘
│ availability │     └──────────────────┘          │
│ quirk        │                                   │
│ created_at   │     ┌──────────────────┐     ┌────┴────────────────┐
│              │────<│candidate_traits  │     │ job_required_skills │
└──────────────┘     │──────────────────│     │────────────────────│
                     │ candidate_id (FK)│     │ job_id (FK)        │>──┐
                     │ trait            │     │ skill_id (FK)      │   │
                     │ UQ(cand,trait)   │     │ PK(job,skill)      │   │
                     └──────────────────┘     └────────────────────┘   │
                                                                      │
                     ┌──────────────────┐     ┌──────────────┐        │
                     │job_culture_kwds  │>────│    jobs       │────────┘
                     │──────────────────│     │──────────────│
                     │ job_id (FK)      │     │ id (PK)      │
                     │ keyword          │     │ title        │
                     │ UQ(job,keyword)  │     │ min_experience│
                     └──────────────────┘     │ tagline      │
                                              │ created_at   │
                                              └──────────────┘
```

### Design decisions

- **Shared `skills` table**: Both candidates and jobs reference the same skill vocabulary, preventing typo-based mismatches and enabling efficient set-intersection queries.
- **Junction tables with composite PKs**: `candidate_skills(candidate_id, skill_id)` and `job_required_skills(job_id, skill_id)` prevent duplicate associations at the database level.
- **Separate traits/keywords tables**: Traits are candidate-specific, culture keywords are job-specific. They're matched by normalized string comparison, not FK relationship.
- **No precomputed match table**: With 15 candidates × 6 jobs = 90 pairs, dynamic computation takes <10ms. A cache would add invalidation complexity without measurable benefit.

## Matching Algorithm

### Formula

```
Total Score = Skill Score + Experience Score + Culture Score + Availability Score
              [0-50]        [0-25]             [0-15]          [0-10]
```

**Maximum possible score: 100**

### Component Details

#### Skill Match (50 points — 50% weight)

```
skill_score = (|candidate_skills ∩ job_required_skills| / |job_required_skills|) × 50
```

- Job with 0 required skills → 0 points (no skills to match)
- All comparisons use normalized (lowercase, trimmed) strings
- Duplicates are deduplicated before computation

#### Experience Fit (25 points — 25% weight)

```
experience_score = min(candidate_experience / job_min_experience, 1.0) × 25
```

- Capped at 1.0 — overqualification gives no bonus
- Job min = 0 → full 25 points for anyone
- Candidate at 0 years with job min > 0 → 0 points

#### Culture Alignment (15 points — 15% weight)

```
culture_score = (|normalized_traits ∩ normalized_culture_keywords| / |job_culture_keywords|) × 15
```

- Exact normalized string match (no fuzzy/semantic matching)
- Empty traits or keywords → 0 points

#### Availability (10 points — 10% weight)

| Availability | Points |
|-------------|--------|
| Immediate | 10 |
| 2 weeks | 7 |
| Not looking | 0 |
| NULL/unknown | 0 |

Candidates with "not looking" are **included in results** with a score penalty, not excluded.

### Tie-Breaking (deterministic)

1. Higher overall score
2. Higher skill score (prioritize technical fit)
3. Higher experience score
4. Alphabetical by name

### Scoring Example: Sherlock H. → Backend Detective

| Component | Calculation | Score |
|-----------|------------|-------|
| Skills | {deduction, pattern-recognition, forensics} ∩ {deduction, pattern-recognition, forensics} = 3/3 | 50.00 |
| Experience | min(8/3, 1.0) = 1.0 × 25 | 25.00 |
| Culture | {analytical, blunt} ∩ {analytical, autonomous} = 1/2 | 7.50 |
| Availability | immediate | 10.00 |
| **Total** | | **92.50** |

## Engineering Decisions and Trade-offs

| Decision | Chosen | Alternative | Why |
|----------|--------|-------------|-----|
| **Database** | PostgreSQL | SQLite | PostgreSQL offers CHECK constraints, ARRAY_AGG, window functions, concurrent access, and EXPLAIN ANALYZE for query optimization |
| **SQL approach** | Raw handwritten SQL | ORM (SQLAlchemy) | Direct SQL proficiency; zero ORM overhead and full control over query optimization and execution plans |
| **Matching** | Dynamic computation | Precomputed/cached | 15×6=90 pairs is trivial to compute in real-time; precomputing adds invalidation complexity without benefit |
| **Scoring model** | Weighted multi-factor | ML-based ranking | Deterministic, explainable, debuggable, requires no training data |
| **Architecture** | Modular monolith | Microservices | Single deployment unit appropriate for this scope; clear layer separation provides the benefits of modularity without operational overhead |
| **Pagination** | LIMIT/OFFSET | Cursor/keyset | Simpler implementation for small datasets; keyset would be preferable for large result sets to avoid deep-page performance degradation |
| **Trait matching** | Exact normalized match | Fuzzy/semantic matching | Deterministic results, no external NLP dependencies; fuzzy matching could produce inconsistent scores |
| **Unavailable candidates** | Score penalty (0 pts) | Exclude entirely | Keeps all candidates visible in rankings; recruiters may want to see strong-but-unavailable candidates for future outreach |
| **Normalization** | 3NF with junction tables | Denormalized arrays | Proper referential integrity prevents orphaned skills; trade-off is slightly more complex queries |
| **Connection pooling** | psycopg ConnectionPool | New connection per request | Pool amortizes connection setup cost; critical for production workloads |

## Edge Case Handling

| Scenario | Handling |
|----------|---------|
| Job has 0 required skills | skill_score = 0 (avoids ÷0) |
| Job has 0 culture keywords | culture_score = 0 |
| Candidate has 0 traits | culture_score = 0 |
| Candidate has 0 experience, job min > 0 | experience_score = 0 |
| NULL availability | Treated as 0 points (not silently treated as immediate) |
| Invalid candidate/job ID | HTTP 404 |
| Duplicate skill in insertion | ON CONFLICT DO NOTHING |
| Identical scores | Deterministic tie-breaking by skill_score → experience → name |
| Empty pagination page | Returns empty list with total_count, not 404 |
| Partial ingestion failure | Transaction ROLLBACK — no partial records |

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Create a Candidate
```bash
curl -X POST http://localhost:8000/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "James B.",
    "skills": ["espionage", "negotiation", "precision"],
    "experience_years": 15,
    "availability": "immediate",
    "traits": ["decisive", "calm"],
    "quirk": "Shaken, not stirred."
  }'
```

### Get a Candidate
```bash
curl http://localhost:8000/candidates/1
```

### Create a Job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Field Agent",
    "required_skills": ["espionage", "precision"],
    "min_experience": 5,
    "culture_keywords": ["decisive", "autonomous"],
    "tagline": "License to debug."
  }'
```

### Get a Job
```bash
curl http://localhost:8000/jobs/1
```

### Get Ranked Candidates for a Job
```bash
# All matches
curl http://localhost:8000/jobs/1/matches

# With pagination
curl "http://localhost:8000/jobs/1/matches?page=1&page_size=5"

# With minimum score filter
curl "http://localhost:8000/jobs/1/matches?min_score=50"
```

### Get Ranked Jobs for a Candidate
```bash
curl http://localhost:8000/candidates/1/matches
```

### Swagger UI
Open `http://localhost:8000/docs` in a browser for interactive API documentation.

## Installation & Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- pip

### 1. Clone and enter the project
```bash
git clone <repository-url>
cd recruiter-bot
```

### 2. Start PostgreSQL
```bash
docker compose up -d
```
This starts two PostgreSQL instances:
- **Dev DB** on port 5432
- **Test DB** on port 5433

### 3. Set up environment
```bash
cp .env.example .env
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the application
```bash
# Option A: Using uvicorn directly
uvicorn app.main:app --reload

# Option B: Using the module
python -m app.main
```

The app will automatically initialize the schema and load seed data on first startup.

### 6. Verify
```bash
curl http://localhost:8000/health
# → {"status":"healthy","database":"connected"}

curl http://localhost:8000/jobs/1/matches
# → Ranked candidates for "Backend Detective"
```

### Alternative: Seed manually
```bash
python -m scripts.seed_database
```

## Running Tests

### Prerequisites
Ensure the test database is running:
```bash
docker compose up db-test -d
```

### Run all tests
```bash
pytest -v
```

### Run only unit tests (no database needed)
```bash
pytest tests/test_scoring.py -v
```

### Run integration tests
```bash
pytest tests/test_api.py -v
```

## SQL Analytics Challenges

Solutions are in [`sql/sql_detective.sql`](sql/sql_detective.sql).

### Summary of Findings

1. **Open job postings**: 4 open postings owned by Priya Shah (2), Daniel Ortiz, and Wei Zhang.

2. **Final-stage applicant counts**: Ranges from 0 (jobs 5, 6) to 4 (job 4).

3. **Multi-job applicants** (data quality edge case): Ananya Rao appears as two rows with different email capitalizations. After normalizing with `LOWER(TRIM(email))`, three people applied to multiple jobs:
   - Ananya Rao (jobs 1, 4)
   - Ben Turner (jobs 1, 3)
   - Elena Popescu (jobs 2, 7)

4. **Conversion rates**: Only recruiters with 3+ Final interviews qualify:
   - Priya Shah: 75% (3/4 passed)
   - Daniel Ortiz: 50% (2/4 passed)

5. **Top recruiter per department** (window function): Uses `RANK()` over `ROW_NUMBER()` to handle ties fairly — if two recruiters have equal placements, both are reported.

## Known Limitations

1. **No authentication/authorization** — prototype scope; production deployment would integrate OAuth2/JWT.
2. **LIMIT/OFFSET pagination** — degrades for deep pages; keyset pagination would be better at scale.
3. **No rate limiting** — vulnerable to abuse without request throttling.
4. **In-memory sorting** — match scoring fetches all candidates/jobs, sorts in Python. Works for 15×6; would need database-side scoring for thousands.
5. **No caching** — every match request recomputes scores. Acceptable for current scale.
6. **Culture matching is exact** — "calm" won't match "calm-under-pressure". Semantic matching could improve relevance.

## Future Improvements

With additional development time, priority enhancements include:
1. **Keyset pagination** for scalable deep-page queries
2. **Database-side scoring** using SQL CTEs for large datasets
3. **Configurable scoring weights via API** instead of module constants
4. **Bulk ingestion endpoint** for batch candidate/job imports
5. **Query performance profiling** with EXPLAIN ANALYZE reports
6. **Fuzzy culture matching** (e.g., "calm" partially matches "calm-under-pressure")
7. **API versioning** (e.g., `/api/v1/...`)
8. **Health check with detailed diagnostics** (pool stats, DB latency)
9. **Structured logging** with correlation IDs
10. **GitHub Actions CI pipeline** for automated testing
