"""
Candidate repository — all candidate-related SQL queries.

Every function accepts a psycopg connection and uses parameterized queries.
No ORM, no query builder — handwritten SQL only.
"""

from __future__ import annotations

import logging
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


def get_candidate_by_id(conn: psycopg.Connection, candidate_id: int) -> dict[str, Any] | None:
    """
    Fetch a single candidate with their skills and traits.

    Returns None if the candidate does not exist.
    Uses a single query with array aggregation to avoid N+1.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                c.id,
                c.name,
                c.experience_years,
                c.availability,
                c.quirk,
                c.created_at,
                COALESCE(
                    ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL),
                    '{}'
                ) AS skills,
                COALESCE(
                    ARRAY_AGG(DISTINCT ct.trait) FILTER (WHERE ct.trait IS NOT NULL),
                    '{}'
                ) AS traits
            FROM candidates c
            LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
            LEFT JOIN skills s            ON s.id = cs.skill_id
            LEFT JOIN candidate_traits ct ON ct.candidate_id = c.id
            WHERE c.id = %(candidate_id)s
            GROUP BY c.id
            """,
            {"candidate_id": candidate_id},
        )
        return cur.fetchone()


def get_all_candidates_with_details(conn: psycopg.Connection) -> list[dict[str, Any]]:
    """
    Fetch ALL candidates with their skills and traits in a single query.

    Used by the matching engine to score all candidates against a job
    without N+1 queries.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                c.id,
                c.name,
                c.experience_years,
                c.availability,
                c.quirk,
                c.created_at,
                COALESCE(
                    ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL),
                    '{}'
                ) AS skills,
                COALESCE(
                    ARRAY_AGG(DISTINCT ct.trait) FILTER (WHERE ct.trait IS NOT NULL),
                    '{}'
                ) AS traits
            FROM candidates c
            LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
            LEFT JOIN skills s            ON s.id = cs.skill_id
            LEFT JOIN candidate_traits ct ON ct.candidate_id = c.id
            GROUP BY c.id
            ORDER BY c.id
            """
        )
        return cur.fetchall()


def create_candidate(
    conn: psycopg.Connection,
    name: str,
    experience_years: int,
    availability: str,
    skills: list[str],
    traits: list[str],
    quirk: str | None,
) -> dict[str, Any]:
    """
    Insert a new candidate with skills and traits in a single transaction.

    - Skills are inserted into the shared `skills` table with ON CONFLICT.
    - All inserts are atomic — partial failure rolls back everything.
    - Returns the full candidate record.

    Raises psycopg.errors.UniqueViolation if the candidate name already exists.
    """
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            # 1. Insert candidate
            cur.execute(
                """
                INSERT INTO candidates (name, experience_years, availability, quirk)
                VALUES (%(name)s, %(experience_years)s, %(availability)s, %(quirk)s)
                RETURNING id, name, experience_years, availability, quirk, created_at
                """,
                {
                    "name": name,
                    "experience_years": experience_years,
                    "availability": availability,
                    "quirk": quirk,
                },
            )
            candidate = cur.fetchone()
            candidate_id = candidate["id"]

            # 2. Ensure skills exist, then link them
            normalized_skills: list[str] = []
            for skill_name in skills:
                normalized = skill_name.strip().lower()
                if not normalized or normalized in normalized_skills:
                    continue  # skip empty or duplicate skills
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
                    # Skill already existed — fetch its id
                    cur.execute(
                        "SELECT id FROM skills WHERE name = %(name)s",
                        {"name": normalized},
                    )
                    row = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO candidate_skills (candidate_id, skill_id)
                    VALUES (%(candidate_id)s, %(skill_id)s)
                    ON CONFLICT DO NOTHING
                    """,
                    {"candidate_id": candidate_id, "skill_id": row["id"]},
                )

            # 3. Insert traits
            seen_traits: set[str] = set()
            for trait in traits:
                normalized_trait = trait.strip().lower()
                if not normalized_trait or normalized_trait in seen_traits:
                    continue
                seen_traits.add(normalized_trait)

                cur.execute(
                    """
                    INSERT INTO candidate_traits (candidate_id, trait)
                    VALUES (%(candidate_id)s, %(trait)s)
                    ON CONFLICT (candidate_id, trait) DO NOTHING
                    """,
                    {"candidate_id": candidate_id, "trait": normalized_trait},
                )

            # 4. Return full candidate with skills and traits
            candidate["skills"] = normalized_skills
            candidate["traits"] = list(seen_traits)
            return candidate
