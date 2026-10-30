"""
Application configuration loaded from environment variables.

Uses pydantic-settings so every value can be overridden via .env or
shell exports. Secrets never have defaults — they must be supplied.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, loaded from environment or .env file."""

    # Database
    database_url: str = "postgresql://recruiter:recruiter_pass@localhost:5432/recruiterbot"
    test_database_url: str = "postgresql://recruiter:recruiter_pass@localhost:5433/recruiterbot_test"

    # Connection pool
    db_min_pool_size: int = 2
    db_max_pool_size: int = 10

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Singleton — imported by other modules
settings = Settings()
