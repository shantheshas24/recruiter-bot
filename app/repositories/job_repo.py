"""
Job repository — all job-related SQL queries.

Every function accepts a psycopg connection and uses parameterized queries.
No ORM, no query builder — handwritten SQL only.
"""

from __future__ import annotations

import logging
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


def get_job_by_id(conn: psycopg.Connection, job_id: int) -> dict[str, Any] | None:
    """
    Fetch a single job with its required skills and culture keywords.

    Returns None if the job does not exist.
    Uses a single query with array aggregation to avoid N+1.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                j.id,
                j.title,
                j.min_experience,
                j.tagline,
                j.created_at,
                COALESCE(
                    ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL),
                    '{}'
                ) AS required_skills,
                COALESCE(
                    ARRAY_AGG(DISTINCT ck.keyword) FILTER (WHERE ck.keyword IS NOT NULL),
                    '{}'
                ) AS culture_keywords
            FROM jobs j
            LEFT JOIN job_required_skills jrs ON jrs.job_id = j.id
            LEFT JOIN skills s               ON s.id = jrs.skill_id
            LEFT JOIN job_culture_keywords ck ON ck.job_id = j.id
            WHERE j.id = %(job_id)s
            GROUP BY j.id
            """,
            {"job_id": job_id},
        )
        return cur.fetchone()


def get_all_jobs_with_details(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """
    Fetch ALL jobs with their required skills and culture keywords in a single query.

    Used by the matching engine to score all jobs against a candidate
    without N+1 queries.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                j.id,
                j.title,
                j.min_experience,
                j.tagline,
                j.created_at,
                COALESCE(
                    ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL),
                    '{}'
                ) AS required_skills,
                COALESCE(
                    ARRAY_AGG(DISTINCT ck.keyword) FILTER (WHERE ck.keyword IS NOT NULL),
                    '{}'
                ) AS culture_keywords
            FROM jobs j
            LEFT JOIN job_required_skills jrs ON jrs.job_id = j.id
            LEFT JOIN skills s               ON s.id = jrs.skill_id
            LEFT JOIN job_culture_keywords ck ON ck.job_id = j.id
            GROUP BY j.id
            ORDER BY j.id
            """
        )
        return cur.fetchall()


def create_job(
    conn: psycopg.Connection,
    title: str,
    min_experience: int,
    required_skills: list[str],
    culture_keywords: list[str],
    tagline: str | None,
) -> dict[str, Any]:
    """
    Insert a new job with required skills and culture keywords in a single transaction.

    - Skills are inserted into the shared `skills` table with ON CONFLICT.
    - All inserts are atomic — partial failure rolls back everything.
    - Returns the full job record.
    """
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            # 1. Insert job
            cur.execute(
                """
                INSERT INTO jobs (title, min_experience, tagline)
                VALUES (%(title)s, %(min_experience)s, %(tagline)s)
                RETURNING id, title, min_experience, tagline, created_at
                """,
                {
                    "title": title,
                    "min_experience": min_experience,
                    "tagline": tagline,
                },
            )
            job = cur.fetchone()
            job_id = job["id"]

            # 2. Ensure skills exist, then link them
            normalized_skills: list[str] = []
            for skill_name in required_skills:
                normalized = skill_name.strip().lower()
                if not normalized or normalized in normalized_skills:
                    continue
                normalized_skills.append(normalized)

                cur.execute(
                    """
                    INSERT INTO skills (name) VALUES (%(name)s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id
                    """,
                    {"name": normalized},
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "SELECT id FROM skills WHERE name = %(name)s",
                        {"name": normalized},
                    )
                    row = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO job_required_skills (job_id, skill_id)
                    VALUES (%(job_id)s, %(skill_id)s)
                    ON CONFLICT DO NOTHING
                    """,
                    {"job_id": job_id, "skill_id": row["id"]},
                )

            # 3. Insert culture keywords
            seen_keywords: set[str] = set()
            for keyword in culture_keywords:
                normalized_kw = keyword.strip().lower()
                if not normalized_kw or normalized_kw in seen_keywords:
                    continue
                seen_keywords.add(normalized_kw)

                cur.execute(
                    """
                    INSERT INTO job_culture_keywords (job_id, keyword)
                    VALUES (%(job_id)s, %(keyword)s)
                    ON CONFLICT (job_id, keyword) DO NOTHING
                    """,
                    {"job_id": job_id, "keyword": normalized_kw},
                )

            # 4. Return full job with skills and keywords
            job["required_skills"] = normalized_skills
            job["culture_keywords"] = list(seen_keywords)
            return job
