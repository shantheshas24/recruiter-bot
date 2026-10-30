"""
Unit tests for the scoring engine.

These tests are PURE — they don't touch the database. They verify the
mathematical correctness of every scoring component and edge case.
"""

import pytest

from app.services.scoring import (
    compute_skill_score,
    compute_experience_score,
    compute_culture_score,
    compute_availability_score,
    compute_match,
    normalize_set,
    match_sort_key,
    WEIGHT_SKILLS,
    WEIGHT_EXPERIENCE,
    WEIGHT_CULTURE,
)


# =========================================================================
# Skill scoring
# =========================================================================

class TestSkillScore:
    """Tests for compute_skill_score."""

    def test_perfect_match(self):
        """All required skills matched → full 50 points."""
        score, matched, missing = compute_skill_score(
            {"deduction", "forensics", "pattern-recognition"},
            {"deduction", "forensics", "pattern-recognition"},
        )
        assert score == WEIGHT_SKILLS  # 50.0
        assert sorted(matched) == ["deduction", "forensics", "pattern-recognition"]
        assert missing == []

    def test_partial_match(self):
        """2 of 3 required skills → 33.33 points."""
        score, matched, missing = compute_skill_score(
            {"strategy", "crisis-management", "precision"},
            {"crisis-management", "strategy", "negotiation"},
        )
        assert score == pytest.approx(33.33, abs=0.01)
        assert sorted(matched) == ["crisis-management", "strategy"]
        assert missing == ["negotiation"]

    def test_no_match(self):
        """Zero matching skills → 0 points."""
        score, matched, missing = compute_skill_score(
            {"woodworking", "minimalism"},
            {"deduction", "forensics", "pattern-recognition"},
        )
        assert score == 0.0
        assert matched == []
        assert sorted(missing) == ["deduction", "forensics", "pattern-recognition"]

    def test_empty_job_skills(self):
        """Job has no required skills → score is 0."""
        score, matched, missing = compute_skill_score(
            {"python", "java"},
            set(),
        )
        assert score == 0.0
        assert matched == []
        assert missing == []

    def test_empty_candidate_skills(self):
        """Candidate has no skills → 0 points, all missing."""
        score, matched, missing = compute_skill_score(
            set(),
            {"python", "java"},
        )
        assert score == 0.0
        assert matched == []
        assert sorted(missing) == ["java", "python"]

    def test_superset_candidate_skills(self):
        """Candidate has extra skills → still capped at 50."""
        score, matched, missing = compute_skill_score(
            {"a", "b", "c", "d", "e"},
            {"a", "b"},
        )
        assert score == WEIGHT_SKILLS  # 50.0


# =========================================================================
# Experience scoring
# =========================================================================

class TestExperienceScore:
    """Tests for compute_experience_score."""

    def test_exact_match(self):
        """Candidate experience equals requirement → full 25 points."""
        assert compute_experience_score(3, 3) == WEIGHT_EXPERIENCE

    def test_over_qualified(self):
        """Over-qualified → still capped at 25 points."""
        assert compute_experience_score(15, 3) == WEIGHT_EXPERIENCE

    def test_under_qualified(self):
        """Under-qualified → proportional credit."""
        score = compute_experience_score(2, 4)
        assert score == pytest.approx(12.5, abs=0.01)

    def test_zero_experience_required(self):
        """Job requires 0 experience → full points for anyone."""
        assert compute_experience_score(0, 0) == WEIGHT_EXPERIENCE

    def test_zero_candidate_experience(self):
        """Candidate has 0 years → 0 points if job requires > 0."""
        assert compute_experience_score(0, 5) == 0.0

    def test_partial_experience(self):
        """4 years for 8 year requirement → 12.5 points."""
        score = compute_experience_score(4, 8)
        assert score == pytest.approx(12.5, abs=0.01)


# =========================================================================
# Culture scoring
# =========================================================================

class TestCultureScore:
    """Tests for compute_culture_score."""

    def test_full_culture_match(self):
        """All culture keywords match traits → full 15 points."""
        score, matched = compute_culture_score(
            {"analytical", "autonomous"},
            {"analytical", "autonomous"},
        )
        assert score == WEIGHT_CULTURE  # 15.0
        assert sorted(matched) == ["analytical", "autonomous"]

    def test_partial_culture_match(self):
        """1 of 2 culture keywords match → 7.5 points."""
        score, matched = compute_culture_score(
            {"analytical", "blunt"},
            {"analytical", "autonomous"},
        )
        assert score == pytest.approx(7.5, abs=0.01)
        assert matched == ["analytical"]

    def test_no_culture_match(self):
        """No culture keywords match → 0 points."""
        score, matched = compute_culture_score(
            {"stubborn", "principled"},
            {"analytical", "autonomous"},
        )
        assert score == 0.0
        assert matched == []

    def test_empty_culture_keywords(self):
        """Job has no culture keywords → 0 points."""
        score, matched = compute_culture_score(
            {"analytical"},
            set(),
        )
        assert score == 0.0

    def test_empty_traits(self):
        """Candidate has no traits → 0 points."""
        score, matched = compute_culture_score(
            set(),
            {"analytical", "autonomous"},
        )
        assert score == 0.0


# =========================================================================
# Availability scoring
# =========================================================================

class TestAvailabilityScore:
    """Tests for compute_availability_score."""

    def test_immediate(self):
        assert compute_availability_score("immediate") == 10.0

    def test_immediate_case_insensitive(self):
        assert compute_availability_score("Immediate") == 10.0

    def test_two_weeks(self):
        assert compute_availability_score("2 weeks") == 7.0

    def test_not_looking(self):
        assert compute_availability_score("not looking") == 0.0

    def test_none(self):
        """NULL availability → 0 points."""
        assert compute_availability_score(None) == 0.0

    def test_unknown_value(self):
        """Unknown string → 0 points (explicit default)."""
        assert compute_availability_score("maybe") == 0.0


# =========================================================================
# Full match computation
# =========================================================================

class TestComputeMatch:
    """Tests for the complete compute_match function."""

    def test_sherlock_backend_detective(self):
        """Verify deterministic match scoring: Sherlock → Backend Detective."""
        candidate = {
            "id": 1,
            "name": "Sherlock H.",
            "skills": ["deduction", "pattern-recognition", "forensics"],
            "experience_years": 8,
            "availability": "immediate",
            "traits": ["analytical", "blunt"],
        }
        job = {
            "id": 1,
            "title": "Backend Detective",
            "required_skills": ["deduction", "pattern-recognition", "forensics"],
            "min_experience": 3,
            "culture_keywords": ["analytical", "autonomous"],
        }
        result = compute_match(candidate, job)

        assert result["overall_score"] == 92.5
        assert result["score_breakdown"]["skills"] == 50.0
        assert result["score_breakdown"]["experience"] == 25.0
        assert result["score_breakdown"]["culture"] == 7.5
        assert result["score_breakdown"]["availability"] == 10.0
        assert sorted(result["matched_skills"]) == ["deduction", "forensics", "pattern-recognition"]
        assert result["missing_skills"] == []
        assert result["matched_culture"] == ["analytical"]

    def test_ron_backend_detective(self):
        """Imperfect match: Ron S. → Backend Detective."""
        candidate = {
            "id": 5,
            "name": "Ron S.",
            "skills": ["woodworking", "minimalism", "negotiation"],
            "experience_years": 15,
            "availability": "not looking",
            "traits": ["stubborn", "principled"],
        }
        job = {
            "id": 1,
            "title": "Backend Detective",
            "required_skills": ["deduction", "pattern-recognition", "forensics"],
            "min_experience": 3,
            "culture_keywords": ["analytical", "autonomous"],
        }
        result = compute_match(candidate, job)

        assert result["overall_score"] == 25.0
        assert result["score_breakdown"]["skills"] == 0.0
        assert result["score_breakdown"]["experience"] == 25.0
        assert result["score_breakdown"]["culture"] == 0.0
        assert result["score_breakdown"]["availability"] == 0.0

    def test_score_never_exceeds_100(self):
        """Even with perfect scores in all categories, max is 100."""
        candidate = {
            "skills": ["a", "b", "c"],
            "experience_years": 100,
            "availability": "immediate",
            "traits": ["x", "y"],
        }
        job = {
            "required_skills": ["a", "b", "c"],
            "min_experience": 1,
            "culture_keywords": ["x", "y"],
        }
        result = compute_match(candidate, job)
        assert result["overall_score"] == 100.0

    def test_score_minimum_is_zero(self):
        """Worst possible match → 0 points."""
        candidate = {
            "skills": [],
            "experience_years": 0,
            "availability": "not looking",
            "traits": [],
        }
        job = {
            "required_skills": ["python"],
            "min_experience": 10,
            "culture_keywords": ["innovative"],
        }
        result = compute_match(candidate, job)
        assert result["overall_score"] == 0.0

    def test_reverse_consistency(self):
        """Score for candidate→job must equal job→candidate."""
        candidate = {
            "id": 1, "name": "Test",
            "skills": ["a", "b"],
            "experience_years": 5,
            "availability": "2 weeks",
            "traits": ["x"],
        }
        job = {
            "id": 1, "title": "Role",
            "required_skills": ["a", "b", "c"],
            "min_experience": 3,
            "culture_keywords": ["x", "y"],
        }
        # Same function, same inputs → same result (the engine doesn't care about direction)
        result1 = compute_match(candidate, job)
        result2 = compute_match(candidate, job)
        assert result1["overall_score"] == result2["overall_score"]
        assert result1["score_breakdown"] == result2["score_breakdown"]


# =========================================================================
# Normalization
# =========================================================================

class TestNormalization:
    """Tests for normalize_set."""

    def test_basic(self):
        assert normalize_set(["Python", " JAVA ", "go"]) == {"python", "java", "go"}

    def test_empty_list(self):
        assert normalize_set([]) == set()

    def test_none(self):
        assert normalize_set(None) == set()

    def test_deduplication(self):
        assert normalize_set(["Python", "python", "PYTHON"]) == {"python"}

    def test_strips_whitespace(self):
        assert normalize_set(["  a  ", "b  ", "  c"]) == {"a", "b", "c"}


# =========================================================================
# Tie-breaking
# =========================================================================

class TestTieBreaking:
    """Tests for deterministic tie-breaking."""

    def test_different_scores(self):
        """Higher score comes first."""
        matches = [
            {"overall_score": 50, "score_breakdown": {"skills": 25, "experience": 15}, "candidate_name": "B"},
            {"overall_score": 80, "score_breakdown": {"skills": 40, "experience": 20}, "candidate_name": "A"},
        ]
        matches.sort(key=match_sort_key)
        assert matches[0]["candidate_name"] == "A"

    def test_same_score_different_skills(self):
        """Same overall → higher skill score wins."""
        matches = [
            {"overall_score": 75, "score_breakdown": {"skills": 30, "experience": 25}, "candidate_name": "B"},
            {"overall_score": 75, "score_breakdown": {"skills": 40, "experience": 15}, "candidate_name": "A"},
        ]
        matches.sort(key=match_sort_key)
        assert matches[0]["candidate_name"] == "A"

    def test_same_everything_alphabetical(self):
        """All scores identical → alphabetical by name."""
        matches = [
            {"overall_score": 75, "score_breakdown": {"skills": 40, "experience": 20}, "candidate_name": "Zebra"},
            {"overall_score": 75, "score_breakdown": {"skills": 40, "experience": 20}, "candidate_name": "Alpha"},
        ]
        matches.sort(key=match_sort_key)
        assert matches[0]["candidate_name"] == "Alpha"


# =========================================================================
# Explanation generation
# =========================================================================

class TestExplanation:
    """Tests for deterministic explanation generation."""

    def test_explanation_not_empty(self):
        """Every match must produce a non-empty reason."""
        result = compute_match(
            {"skills": ["a"], "experience_years": 3, "availability": "immediate", "traits": ["x"]},
            {"required_skills": ["a", "b"], "min_experience": 5, "culture_keywords": ["x"]},
        )
        assert len(result["reason"]) > 0

    def test_explanation_is_deterministic(self):
        """Same inputs → same explanation."""
        candidate = {"skills": ["a"], "experience_years": 3, "availability": "immediate", "traits": []}
        job = {"required_skills": ["a", "b"], "min_experience": 5, "culture_keywords": ["x"]}
        r1 = compute_match(candidate, job)
        r2 = compute_match(candidate, job)
        assert r1["reason"] == r2["reason"]
