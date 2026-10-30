"""
Scoring engine — pure-function computation of match scores.

This module contains ZERO database or HTTP logic. It operates on plain
Python data structures (dicts, sets, lists) and is fully testable in
isolation.

Weights are defined as module-level constants so they can be reconfigured
in one place without touching the formulas.
"""

from __future__ import annotations

# ============================================================================
# Configurable scoring weights
# ============================================================================
# Changing these values changes the relative importance of each factor.
# They must sum to 100 for the score to stay in the [0, 100] range.

WEIGHT_SKILLS: float = 50.0
WEIGHT_EXPERIENCE: float = 25.0
WEIGHT_CULTURE: float = 15.0
WEIGHT_AVAILABILITY: float = 10.0

AVAILABILITY_SCORES: dict[str, float] = {
    "immediate": 10.0,
    "2 weeks": 7.0,
    "not looking": 0.0,
}

# Default for NULL or unknown availability
DEFAULT_AVAILABILITY_SCORE: float = 0.0


# ============================================================================
# Individual scoring components
# ============================================================================

def compute_skill_score(
    candidate_skills: set[str],
    job_required_skills: set[str],
) -> tuple[float, list[str], list[str]]:
    """
    Compute skill match score.

    Returns: (score, matched_skills, missing_skills)

    Formula: (|intersection| / |job_required|) × WEIGHT_SKILLS
    Edge case: if job has no required skills, score is 0.
    """
    if not job_required_skills:
        return 0.0, [], []

    matched = sorted(candidate_skills & job_required_skills)
    missing = sorted(job_required_skills - candidate_skills)
    ratio = len(matched) / len(job_required_skills)
    score = round(ratio * WEIGHT_SKILLS, 2)

    return score, matched, missing


def compute_experience_score(
    candidate_experience: int,
    job_min_experience: int,
) -> float:
    """
    Compute experience fit score.

    Formula: min(candidate_exp / job_min_exp, 1.0) × WEIGHT_EXPERIENCE
    Edge cases:
    - Job min = 0 → full credit (any experience is sufficient)
    - Candidate exp = 0, job min > 0 → 0 points
    - Over-qualified → capped at 1.0 (no bonus for excess)
    """
    if job_min_experience == 0:
        return WEIGHT_EXPERIENCE

    ratio = min(candidate_experience / job_min_experience, 1.0)
    return round(ratio * WEIGHT_EXPERIENCE, 2)


def compute_culture_score(
    candidate_traits: set[str],
    job_culture_keywords: set[str],
) -> tuple[float, list[str]]:
    """
    Compute culture alignment score.

    Returns: (score, matched_culture_keywords)

    Formula: (|intersection| / |job_culture|) × WEIGHT_CULTURE
    Edge cases:
    - Job has no culture keywords → score is 0
    - Candidate has no traits → score is 0
    """
    if not job_culture_keywords:
        return 0.0, []

    if not candidate_traits:
        return 0.0, []

    matched = sorted(candidate_traits & job_culture_keywords)
    ratio = len(matched) / len(job_culture_keywords)
    score = round(ratio * WEIGHT_CULTURE, 2)

    return score, matched


def compute_availability_score(availability: str | None) -> float:
    """
    Compute availability score from lookup table.

    Unknown or NULL availability → 0 points (explicit, not silent).
    """
    if availability is None:
        return DEFAULT_AVAILABILITY_SCORE

    normalized = availability.strip().lower()
    return AVAILABILITY_SCORES.get(normalized, DEFAULT_AVAILABILITY_SCORE)


# ============================================================================
# Full match computation
# ============================================================================

def normalize_set(items: list[str] | None) -> set[str]:
    """Normalize a list of strings to a lowercase, trimmed set."""
    if not items:
        return set()
    return {item.strip().lower() for item in items if item and item.strip()}


def compute_match(
    candidate: dict,
    job: dict,
) -> dict:
    """
    Compute the full match between a candidate and a job.

    Both `candidate` and `job` are dicts as returned by the repositories:
    - candidate: {id, name, skills: [...], experience_years, availability, traits: [...]}
    - job: {id, title, required_skills: [...], min_experience, culture_keywords: [...]}

    Returns a dict with all score components and explainability fields.
    """
    # Normalize all string-based comparisons
    cand_skills = normalize_set(candidate.get("skills"))
    job_skills = normalize_set(job.get("required_skills"))
    cand_traits = normalize_set(candidate.get("traits"))
    job_culture = normalize_set(job.get("culture_keywords"))

    # Compute each component
    skill_score, matched_skills, missing_skills = compute_skill_score(cand_skills, job_skills)
    experience_score = compute_experience_score(
        candidate.get("experience_years", 0),
        job.get("min_experience", 0),
    )
    culture_score, matched_culture = compute_culture_score(cand_traits, job_culture)
    availability_score = compute_availability_score(candidate.get("availability"))

    overall = round(skill_score + experience_score + culture_score + availability_score, 2)

    # Generate deterministic explanation
    reason = generate_reason(
        skill_score=skill_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        total_required=len(job_skills),
        experience_score=experience_score,
        candidate_exp=candidate.get("experience_years", 0),
        job_min_exp=job.get("min_experience", 0),
        culture_score=culture_score,
        matched_culture=matched_culture,
        availability=candidate.get("availability"),
    )

    return {
        "overall_score": overall,
        "score_breakdown": {
            "skills": skill_score,
            "experience": experience_score,
            "culture": culture_score,
            "availability": availability_score,
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_culture": matched_culture,
        "reason": reason,
    }


# ============================================================================
# Deterministic explanation generator (no LLM)
# ============================================================================

def generate_reason(
    *,
    skill_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    total_required: int,
    experience_score: float,
    candidate_exp: int,
    job_min_exp: int,
    culture_score: float,
    matched_culture: list[str],
    availability: str | None,
) -> str:
    """
    Build a human-readable explanation from score components.

    Uses deterministic templates — the explanation always matches the score.
    """
    parts: list[str] = []

    # Skill assessment
    if total_required == 0:
        parts.append("No specific skills required for this role")
    elif len(matched_skills) == total_required:
        parts.append(f"Perfect skill alignment ({len(matched_skills)}/{total_required} skills matched)")
    elif len(matched_skills) > 0:
        parts.append(
            f"Partial skill alignment ({len(matched_skills)}/{total_required} skills matched, "
            f"missing: {', '.join(missing_skills)})"
        )
    else:
        parts.append(f"No matching skills (0/{total_required} required skills)")

    # Experience assessment
    if job_min_exp == 0:
        parts.append("no minimum experience required")
    elif candidate_exp >= job_min_exp:
        parts.append("meets or exceeds experience requirement")
    else:
        parts.append(f"below experience requirement ({candidate_exp}/{job_min_exp} years)")

    # Culture assessment
    if culture_score > 0:
        parts.append(f"culture alignment on: {', '.join(matched_culture)}")
    else:
        parts.append("no culture keyword alignment")

    # Availability assessment
    normalized_avail = (availability or "unknown").strip().lower()
    if normalized_avail == "immediate":
        parts.append("available immediately")
    elif normalized_avail == "2 weeks":
        parts.append("available in 2 weeks")
    elif normalized_avail == "not looking":
        parts.append("not currently looking")
    else:
        parts.append("availability unknown")

    # Join with proper capitalization
    result = ". ".join(parts) + "."

    # Capitalize first letter
    return result[0].upper() + result[1:] if result else ""


# ============================================================================
# Sorting / tie-breaking
# ============================================================================

def match_sort_key(match: dict) -> tuple:
    """
    Sort key for deterministic ranking.

    Priority:
    1. Overall score (descending — negate for ascending sort)
    2. Skill score (descending)
    3. Experience score (descending)
    4. Name (ascending — alphabetical tie-breaker)

    The name field is either 'candidate_name' or 'job_title'.
    """
    return (
        -match["overall_score"],
        -match["score_breakdown"]["skills"],
        -match["score_breakdown"]["experience"],
        match.get("candidate_name", match.get("job_title", "")),
    )
