"""
Matching engine — orchestrates scoring across candidates and jobs.

This is the service layer that bridges repositories (data access) and
the scoring engine (pure computation). It fetches the data, runs the
scoring, and returns structured results.
"""

from __future__ import annotations

import math
from typing import Any

import psycopg

from app.repositories import candidate_repo, job_repo
from app.services.scoring import compute_match, match_sort_key


def get_matches_for_job(
    conn: psycopg.Connection,
    job_id: int,
    page: int = 1,
    page_size: int = 20,
    min_score: float | None = None,
) -> dict[str, Any]:
    """
    Rank all candidates against a specific job.

    Returns paginated, sorted match results with full explainability.
    """
    # Fetch job details (raises if not found — caller handles 404)
    job = job_repo.get_job_by_id(conn, job_id)
    if job is None:
        return None

    # Fetch ALL candidates in a single query (avoids N+1)
    candidates = candidate_repo.get_all_candidates_with_details(conn)

    # Score each candidate against the job
    results: list[dict[str, Any]] = []
    for candidate in candidates:
        match = compute_match(candidate, job)
        match["candidate_id"] = candidate["id"]
        match["candidate_name"] = candidate["name"]
        results.append(match)

    # Filter by minimum score if requested
    if min_score is not None:
        results = [r for r in results if r["overall_score"] >= min_score]

    # Sort with deterministic tie-breaking
    results.sort(key=match_sort_key)

    # Paginate
    total = len(results)
    total_pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]

    return {
        "job_id": job["id"],
        "job_title": job["title"],
        "matches": page_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_matches_for_candidate(
    conn: psycopg.Connection,
    candidate_id: int,
    page: int = 1,
    page_size: int = 20,
    min_score: float | None = None,
) -> dict[str, Any]:
    """
    Rank all jobs against a specific candidate.

    Uses the SAME scoring engine as get_matches_for_job to guarantee
    score consistency regardless of direction.
    """
    # Fetch candidate details
    candidate = candidate_repo.get_candidate_by_id(conn, candidate_id)
    if candidate is None:
        return None

    # Fetch ALL jobs in a single query
    jobs = job_repo.get_all_jobs_with_details(conn)

    # Score each job against the candidate (same compute_match function)
    results: list[dict[str, Any]] = []
    for job in jobs:
        match = compute_match(candidate, job)
        match["job_id"] = job["id"]
        match["job_title"] = job["title"]
        results.append(match)

    # Filter by minimum score if requested
    if min_score is not None:
        results = [r for r in results if r["overall_score"] >= min_score]

    # Sort with deterministic tie-breaking
    results.sort(key=match_sort_key)

    # Paginate
    total = len(results)
    total_pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]

    return {
        "candidate_id": candidate["id"],
        "candidate_name": candidate["name"],
        "matches": page_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
