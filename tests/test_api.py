"""
Integration tests for the Matching API endpoints.

These tests require a running test database (docker-compose db-test).
They verify end-to-end behavior through the FastAPI test client.
"""

import pytest


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_check(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestCandidateEndpoints:
    """Tests for candidate CRUD endpoints."""

    def test_get_candidate_exists(self, test_client):
        """Sherlock H. should be seeded as candidate 1."""
        response = test_client.get("/candidates/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Sherlock H."
        assert "deduction" in data["skills"]
        assert data["experience_years"] == 8
        assert data["availability"] == "immediate"

    def test_get_candidate_not_found(self, test_client):
        response = test_client.get("/candidates/9999")
        assert response.status_code == 404

    def test_get_candidate_invalid_id(self, test_client):
        response = test_client.get("/candidates/abc")
        assert response.status_code == 422

    def test_create_candidate_success(self, test_client):
        """Create a new candidate via the API."""
        body = {
            "name": "Test Candidate API",
            "skills": ["python", "testing"],
            "experience_years": 5,
            "availability": "immediate",
            "traits": ["curious"],
            "quirk": "Writes tests before code.",
        }
        response = test_client.post("/candidates", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Candidate API"
        assert "python" in data["skills"]

    def test_create_candidate_duplicate(self, test_client):
        """Duplicate name → 409 conflict."""
        body = {
            "name": "Sherlock H.",
            "skills": ["deduction"],
            "experience_years": 8,
            "availability": "immediate",
        }
        response = test_client.post("/candidates", json=body)
        assert response.status_code == 409

    def test_create_candidate_invalid_availability(self, test_client):
        """Invalid availability value → 422."""
        body = {
            "name": "Bad Availability",
            "skills": ["python"],
            "experience_years": 3,
            "availability": "maybe tomorrow",
        }
        response = test_client.post("/candidates", json=body)
        assert response.status_code == 422

    def test_create_candidate_negative_experience(self, test_client):
        """Negative experience → 422."""
        body = {
            "name": "Negative Exp",
            "skills": ["python"],
            "experience_years": -1,
            "availability": "immediate",
        }
        response = test_client.post("/candidates", json=body)
        assert response.status_code == 422

    def test_create_candidate_empty_skills(self, test_client):
        """Empty skills list → 422."""
        body = {
            "name": "No Skills",
            "skills": [],
            "experience_years": 3,
            "availability": "immediate",
        }
        response = test_client.post("/candidates", json=body)
        assert response.status_code == 422


class TestJobEndpoints:
    """Tests for job CRUD endpoints."""

    def test_get_job_exists(self, test_client):
        """Backend Detective should be seeded as job 1."""
        response = test_client.get("/jobs/1")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Backend Detective"
        assert "deduction" in data["required_skills"]

    def test_get_job_not_found(self, test_client):
        response = test_client.get("/jobs/9999")
        assert response.status_code == 404

    def test_create_job_success(self, test_client):
        body = {
            "title": "Test Job API",
            "required_skills": ["python", "sql"],
            "min_experience": 2,
            "culture_keywords": ["collaborative"],
            "tagline": "Build things.",
        }
        response = test_client.post("/jobs", json=body)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Job API"


class TestMatchingEndpoints:
    """Tests for the matching API."""

    def test_job_matches_returns_ranked_results(self, test_client):
        """GET /jobs/1/matches should return all 15+ candidates ranked."""
        response = test_client.get("/jobs/1/matches")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == 1
        assert data["job_title"] == "Backend Detective"
        assert len(data["matches"]) > 0
        assert data["total"] > 0

        # First result should have highest score
        scores = [m["overall_score"] for m in data["matches"]]
        assert scores == sorted(scores, reverse=True)

        # Sherlock should be the top match for Backend Detective
        top = data["matches"][0]
        assert top["candidate_name"] == "Sherlock H."
        assert top["overall_score"] == 92.5

    def test_job_matches_score_breakdown(self, test_client):
        """Each match result should include a full score breakdown."""
        response = test_client.get("/jobs/1/matches")
        data = response.json()
        first_match = data["matches"][0]

        assert "score_breakdown" in first_match
        breakdown = first_match["score_breakdown"]
        assert "skills" in breakdown
        assert "experience" in breakdown
        assert "culture" in breakdown
        assert "availability" in breakdown

        # Verify breakdown sums to overall
        total = (
            breakdown["skills"]
            + breakdown["experience"]
            + breakdown["culture"]
            + breakdown["availability"]
        )
        assert total == pytest.approx(first_match["overall_score"], abs=0.01)

    def test_job_matches_explainability(self, test_client):
        """Each match should have matched/missing skills and a reason."""
        response = test_client.get("/jobs/1/matches")
        data = response.json()
        first_match = data["matches"][0]

        assert "matched_skills" in first_match
        assert "missing_skills" in first_match
        assert "matched_culture" in first_match
        assert "reason" in first_match
        assert len(first_match["reason"]) > 0

    def test_job_matches_not_found(self, test_client):
        response = test_client.get("/jobs/9999/matches")
        assert response.status_code == 404

    def test_candidate_matches_returns_ranked_results(self, test_client):
        """GET /candidates/1/matches should return ranked jobs for Sherlock."""
        response = test_client.get("/candidates/1/matches")
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_id"] == 1
        assert data["candidate_name"] == "Sherlock H."
        assert len(data["matches"]) > 0

        # Scores should be descending
        scores = [m["overall_score"] for m in data["matches"]]
        assert scores == sorted(scores, reverse=True)

    def test_candidate_matches_not_found(self, test_client):
        response = test_client.get("/candidates/9999/matches")
        assert response.status_code == 404

    def test_bidirectional_score_consistency(self, test_client):
        """
        Score for Sherlock→Backend Detective via job matches must equal
        the score for Backend Detective→Sherlock via candidate matches.
        """
        # Get Sherlock's score against Backend Detective from job matches
        response_job = test_client.get("/jobs/1/matches")
        job_matches = response_job.json()["matches"]
        sherlock_from_job = next(
            m for m in job_matches if m["candidate_name"] == "Sherlock H."
        )

        # Get Backend Detective's score for Sherlock from candidate matches
        response_cand = test_client.get("/candidates/1/matches")
        cand_matches = response_cand.json()["matches"]
        detective_from_cand = next(
            m for m in cand_matches if m["job_title"] == "Backend Detective"
        )

        assert sherlock_from_job["overall_score"] == detective_from_cand["overall_score"]
        assert sherlock_from_job["score_breakdown"] == detective_from_cand["score_breakdown"]

    def test_pagination(self, test_client):
        """Pagination should work with page and page_size params."""
        # Get page 1 with 5 results
        r1 = test_client.get("/jobs/1/matches?page=1&page_size=5")
        assert r1.status_code == 200
        d1 = r1.json()
        assert len(d1["matches"]) == 5
        assert d1["page"] == 1

        # Get page 2
        r2 = test_client.get("/jobs/1/matches?page=2&page_size=5")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["page"] == 2

        # No overlap between pages
        names_p1 = {m["candidate_name"] for m in d1["matches"]}
        names_p2 = {m["candidate_name"] for m in d2["matches"]}
        assert names_p1.isdisjoint(names_p2)

    def test_min_score_filter(self, test_client):
        """min_score filter should exclude low-scoring matches."""
        r_all = test_client.get("/jobs/1/matches")
        r_filtered = test_client.get("/jobs/1/matches?min_score=50")

        all_matches = r_all.json()
        filtered_matches = r_filtered.json()

        # Filtered should have fewer or equal results
        assert filtered_matches["total"] <= all_matches["total"]

        # All filtered results should meet the threshold
        for match in filtered_matches["matches"]:
            assert match["overall_score"] >= 50

    def test_empty_pagination(self, test_client):
        """Page beyond available results → empty list, not 404."""
        response = test_client.get("/jobs/1/matches?page=100&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert data["matches"] == []
        assert data["total"] > 0  # Total count should still reflect all matches

    def test_not_looking_candidates_included(self, test_client):
        """Candidates with 'not looking' availability should still appear."""
        response = test_client.get("/jobs/2/matches")  # Rapid Prototyping Engineer
        data = response.json()
        names = [m["candidate_name"] for m in data["matches"]]
        # Tony S. is "not looking" but has perfect skills for this job
        assert "Tony S." in names

    def test_deterministic_ordering(self, test_client):
        """Same query twice should return identical ordering."""
        r1 = test_client.get("/jobs/1/matches")
        r2 = test_client.get("/jobs/1/matches")

        names1 = [m["candidate_name"] for m in r1.json()["matches"]]
        names2 = [m["candidate_name"] for m in r2.json()["matches"]]
        assert names1 == names2
