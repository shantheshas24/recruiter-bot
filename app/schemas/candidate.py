"""Pydantic schemas for Candidate API request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CandidateCreate(BaseModel):
    """Request body for creating a candidate."""

    name: str = Field(..., min_length=1, max_length=150, examples=["Sherlock H."])
    skills: list[str] = Field(
        ..., min_length=1,
        description="List of skill names (e.g. 'deduction', 'forensics')",
        examples=[["deduction", "pattern-recognition", "forensics"]],
    )
    experience_years: int = Field(..., ge=0, examples=[8])
    availability: Literal["immediate", "2 weeks", "not looking"] = Field(
        default="immediate",
        examples=["immediate"],
    )
    traits: list[str] = Field(
        default=[],
        description="Candidate personality traits",
        examples=[["analytical", "blunt"]],
    )
    quirk: str | None = Field(
        default=None,
        max_length=500,
        examples=["Solves problems by eliminating the impossible."],
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CandidateResponse(BaseModel):
    """Response schema for a single candidate."""

    id: int
    name: str
    skills: list[str]
    experience_years: int
    availability: str
    traits: list[str]
    quirk: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
