"""Matching API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from app.database import get_db_connection
from app.schemas.match import PaginatedCandidateMatches, PaginatedJobMatches
from app.services.matching_engine import get_matches_for_job, get_matches_for_candidate
from app.utils.exceptions import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Matching"])


@router.get(
    "/jobs/{job_id}/matches",
    response_model=PaginatedCandidateMatches,
    summary="Get ranked candidates for a job",
    description="Returns all candidates ranked by match score for the specified job. "
                "Includes full score breakdown, matched/missing skills, culture alignment, "
                "and a human-readable explanation for each match.",
)
def get_job_matches(
    job_id: int,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    min_score: float | None = Query(
        default=None, ge=0, le=100,
        description="Minimum match score filter (0-100)",
    ),
) -> PaginatedCandidateMatches:
    try:
        with get_db_connection() as conn:
            result = get_matches_for_job(
                conn, job_id,
                page=page,
                page_size=page_size,
                min_score=min_score,
            )
            if result is None:
                raise NotFoundError("Job", job_id)
            return PaginatedCandidateMatches(**result)
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to compute matches for job %d", job_id)
        raise DatabaseError()


@router.get(
    "/candidates/{candidate_id}/matches",
    response_model=PaginatedJobMatches,
    summary="Get ranked jobs for a candidate",
    description="Returns all jobs ranked by match score for the specified candidate. "
                "Uses the same scoring engine as the job→candidate direction, "
                "guaranteeing consistent scores regardless of lookup direction.",
)
def get_candidate_matches(
    candidate_id: int,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    min_score: float | None = Query(
        default=None, ge=0, le=100,
        description="Minimum match score filter (0-100)",
    ),
) -> PaginatedJobMatches:
    try:
        with get_db_connection() as conn:
            result = get_matches_for_candidate(
                conn, candidate_id,
                page=page,
                page_size=page_size,
                min_score=min_score,
            )
            if result is None:
                raise NotFoundError("Candidate", candidate_id)
            return PaginatedJobMatches(**result)
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to compute matches for candidate %d", candidate_id)
        raise DatabaseError()
