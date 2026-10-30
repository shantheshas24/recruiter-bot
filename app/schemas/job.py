"""Pydantic schemas for Job API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class JobCreate(BaseModel):
    """Request body for creating a job."""

    title: str = Field(..., min_length=1, max_length=200, examples=["Backend Detective"])
    required_skills: list[str] = Field(
        ..., min_length=1,
        description="List of required skill names",
        examples=[["deduction", "pattern-recognition", "forensics"]],
    )
    min_experience: int = Field(..., ge=0, examples=[3])
    culture_keywords: list[str] = Field(
        default=[],
        description="Culture fit keywords",
        examples=[["analytical", "autonomous"]],
    )
    tagline: str | None = Field(
        default=None,
        max_length=500,
        examples=["We have a bug. We have no leads. We have you."],
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class JobResponse(BaseModel):
    """Response schema for a single job."""

    id: int
    title: str
    required_skills: list[str]
    min_experience: int
    culture_keywords: list[str]
    tagline: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
