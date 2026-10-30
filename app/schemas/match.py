"""Pydantic schemas for match results."""

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown by component."""

    skills: float = Field(..., ge=0, le=50, description="Skill match score (0-50)")
    experience: float = Field(..., ge=0, le=25, description="Experience fit score (0-25)")
    culture: float = Field(..., ge=0, le=15, description="Culture alignment score (0-15)")
    availability: float = Field(..., ge=0, le=10, description="Availability score (0-10)")


class CandidateMatchResult(BaseModel):
    """A single candidate's match result for a job."""

    candidate_id: int
    candidate_name: str
    overall_score: float = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    matched_culture: list[str]
    reason: str = Field(..., description="Human-readable explanation of the match")


class JobMatchResult(BaseModel):
    """A single job's match result for a candidate."""

    job_id: int
    job_title: str
    overall_score: float = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    matched_culture: list[str]
    reason: str = Field(..., description="Human-readable explanation of the match")


class PaginatedCandidateMatches(BaseModel):
    """Paginated response for candidate matches against a job."""

    job_id: int
    job_title: str
    matches: list[CandidateMatchResult]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedJobMatches(BaseModel):
    """Paginated response for job matches against a candidate."""

    candidate_id: int
    candidate_name: str
    matches: list[JobMatchResult]
    total: int
    page: int
    page_size: int
    total_pages: int
