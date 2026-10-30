"""
Database connection management using psycopg 3 connection pool.

Provides:
- A connection pool that lives for the lifetime of the application
- A context manager `get_db_connection()` for request-scoped connections
- Schema/seed initialization helpers
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings

# Module-level pool, initialized on app startup
_pool: ConnectionPool | None = None

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def init_pool(database_url: str | None = None) -> None:
    """Create the connection pool. Called once during app startup."""
    global _pool
    url = database_url or settings.database_url
    _pool = ConnectionPool(
        conninfo=url,
        min_size=settings.db_min_pool_size,
        max_size=settings.db_max_pool_size,
        kwargs={"row_factory": dict_row},
    )
    _pool.wait()  # Block until min_size connections are ready


def close_pool() -> None:
    """Shut down the connection pool. Called during app shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Yield a connection from the pool.

    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
    """
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_pool() first.")
    with _pool.connection() as conn:
        yield conn


def run_sql_file(filepath: Path, conn: psycopg.Connection) -> None:
    """Execute a .sql file within the given connection."""
    sql = filepath.read_text(encoding="utf-8")
    conn.execute(sql)


def init_schema(conn: psycopg.Connection) -> None:
    """Run schema.sql, seed.sql, and indexes.sql in a single transaction."""
    with conn.transaction():
        run_sql_file(SQL_DIR / "schema.sql", conn)
        run_sql_file(SQL_DIR / "seed.sql", conn)
        run_sql_file(SQL_DIR / "indexes.sql", conn)
