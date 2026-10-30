"""
Test configuration and fixtures.

Provides:
- A separate test database (port 5433) that is reset between test sessions
- Shared fixtures for database connections
- FastAPI test client

NOTE: The DB fixtures only activate when tests actually request them.
Pure unit tests (like test_scoring.py) skip DB setup entirely.
"""

import pytest
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from fastapi.testclient import TestClient

from app.config import settings
from app.database import SQL_DIR, init_pool, close_pool


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Return the test database URL."""
    return settings.test_database_url


@pytest.fixture(scope="session")
def _setup_test_database(test_db_url: str):
    """
    Session-scoped fixture: create schema + seed data in the test DB once.
    NOT autouse — only triggers when a test depends on it (directly or
    via db_conn / test_client).
    """
    with psycopg.connect(test_db_url) as conn:
        conn.execute(SQL_DIR.joinpath("schema.sql").read_text(encoding="utf-8"))
        conn.execute(SQL_DIR.joinpath("seed.sql").read_text(encoding="utf-8"))
        conn.execute(SQL_DIR.joinpath("indexes.sql").read_text(encoding="utf-8"))
        conn.commit()

    yield

    # Cleanup: drop tables
    with psycopg.connect(test_db_url) as conn:
        conn.execute(
            """
            DROP TABLE IF EXISTS job_culture_keywords CASCADE;
            DROP TABLE IF EXISTS job_required_skills CASCADE;
            DROP TABLE IF EXISTS candidate_traits CASCADE;
            DROP TABLE IF EXISTS candidate_skills CASCADE;
            DROP TABLE IF EXISTS jobs CASCADE;
            DROP TABLE IF EXISTS candidates CASCADE;
            DROP TABLE IF EXISTS skills CASCADE;
            """
        )
        conn.commit()


@pytest.fixture(scope="session")
def db_conn(test_db_url: str, _setup_test_database):
    """Session-scoped connection for repo/service tests."""
    with psycopg.connect(test_db_url, row_factory=dict_row) as conn:
        yield conn


@pytest.fixture(scope="session")
def test_client(test_db_url: str, _setup_test_database):
    """
    Session-scoped FastAPI test client.
    Initializes the connection pool with the test DB URL.
    """
    init_pool(test_db_url)
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    close_pool()
