"""
RecruiterFlow Bot — FastAPI application entry point.

Sets up the application with:
- Connection pool lifecycle management
- Schema initialization on first run
- Router registration
- Health-check endpoint
- OpenAPI/Swagger documentation
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_pool, close_pool, get_db_connection, init_schema
from app.api.candidates import router as candidates_router
from app.api.jobs import router as jobs_router
from app.api.matching import router as matching_router

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage connection pool lifecycle."""
    logger.info("Starting RecruiterFlow Bot...")
    init_pool()
    logger.info("Database pool initialized.")

    # Initialize schema and seed data
    try:
        with get_db_connection() as conn:
            init_schema(conn)
        logger.info("Database schema and seed data loaded.")
    except Exception:
        logger.exception("Failed to initialize database schema.")
        raise

    yield

    logger.info("Shutting down RecruiterFlow Bot...")
    close_pool()
    logger.info("Database pool closed.")


app = FastAPI(
    title="RecruiterFlow Bot",
    description=(
        "An intelligent, explainable candidate-job matching engine. "
        "Ingests candidate profiles and job openings, then ranks the best matches "
        "using a multi-factor scoring algorithm with full explainability."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register routers
app.include_router(candidates_router)
app.include_router(jobs_router)
app.include_router(matching_router)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Verifies the API and database connection are operational.",
)
def health_check() -> dict:
    """Return health status including database connectivity."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"},
        )


# ---------------------------------------------------------------------------
# Entry point for `python -m app.main`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
