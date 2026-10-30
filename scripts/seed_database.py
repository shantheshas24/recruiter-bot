"""
Standalone seed script — run schema.sql + seed.sql + indexes.sql.

Usage:
    python -m scripts.seed_database

Idempotent: safe to run multiple times. Uses ON CONFLICT throughout.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.database import SQL_DIR

import psycopg


def main() -> None:
    print(f"Connecting to: {settings.database_url}")
    with psycopg.connect(settings.database_url) as conn:
        print("Running schema.sql ...")
        conn.execute(SQL_DIR.joinpath("schema.sql").read_text(encoding="utf-8"))

        print("Running seed.sql ...")
        conn.execute(SQL_DIR.joinpath("seed.sql").read_text(encoding="utf-8"))

        print("Running indexes.sql ...")
        conn.execute(SQL_DIR.joinpath("indexes.sql").read_text(encoding="utf-8"))

        conn.commit()

    print("Done — database seeded successfully.")


if __name__ == "__main__":
    main()
