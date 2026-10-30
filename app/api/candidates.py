"""Candidate API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from psycopg.errors import UniqueViolation

from app.database import get_db_connection
from app.repositories import candidate_repo
from app.schemas.candidate import CandidateCreate, CandidateResponse
from app.utils.exceptions import DuplicateError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new candidate",
    description="Creates a candidate with skills, traits, and availability. "
                "Skills are normalized to lowercase. Duplicate names are rejected.",
)
def create_candidate(body: CandidateCreate) -> CandidateResponse:
    try:
        with get_db_connection() as conn:
            result = candidate_repo.create_candidate(
                conn,
                name=body.name,
                experience_years=body.experience_years,
                availability=body.availability,
                skills=body.skills,
                traits=body.traits,
                quirk=body.quirk,
            )
            return CandidateResponse(**result)
    except UniqueViolation:
        raise DuplicateError(f"Candidate '{body.name}' already exists.")
    except DuplicateError:
        raise
    except Exception:
        logger.exception("Failed to create candidate")
        raise DatabaseError()


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Get a candidate by ID",
    description="Returns the candidate with all skills, traits, and metadata.",
)
def get_candidate(candidate_id: int) -> CandidateResponse:
    try:
        with get_db_connection() as conn:
            result = candidate_repo.get_candidate_by_id(conn, candidate_id)
            if result is None:
                raise NotFoundError("Candidate", candidate_id)
            return CandidateResponse(**result)
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to fetch candidate")
        raise DatabaseError()
