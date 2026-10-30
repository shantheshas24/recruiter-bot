"""Job API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from psycopg.errors import UniqueViolation

from app.database import get_db_connection
from app.repositories import job_repo
from app.schemas.job import JobCreate, JobResponse
from app.utils.exceptions import DuplicateError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job",
    description="Creates a job posting with required skills, culture keywords, and tagline. "
                "Skills are normalized to lowercase.",
)
def create_job(body: JobCreate) -> JobResponse:
    try:
        with get_db_connection() as conn:
            result = job_repo.create_job(
                conn,
                title=body.title,
                min_experience=body.min_experience,
                required_skills=body.required_skills,
                culture_keywords=body.culture_keywords,
                tagline=body.tagline,
            )
            return JobResponse(**result)
    except DuplicateError:
        raise
    except Exception:
        logger.exception("Failed to create job")
        raise DatabaseError()


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get a job by ID",
    description="Returns the job posting with all required skills, culture keywords, and metadata.",
)
def get_job(job_id: int) -> JobResponse:
    try:
        with get_db_connection() as conn:
            result = job_repo.get_job_by_id(conn, job_id)
            if result is None:
                raise NotFoundError("Job", job_id)
            return JobResponse(**result)
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to fetch job")
        raise DatabaseError()
