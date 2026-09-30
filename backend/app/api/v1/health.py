import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app import __version__

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok", "ready"]
    service: Literal["community-api"]
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API process liveness",
    tags=["health"],
)
def get_health() -> HealthResponse:
    """Report that this API process is alive; this does not probe dependencies."""
    return HealthResponse(status="ok", service="community-api", version=__version__)


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Check API and PostgreSQL readiness",
    tags=["health"],
)
async def get_readiness(request: Request) -> HealthResponse:
    """Report ready only when PostgreSQL can execute a simple query."""
    engine: AsyncEngine | None = request.app.state.database_engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Readiness check failed because PostgreSQL is unavailable")
        raise HTTPException(status_code=503, detail="Database is unavailable") from None

    return HealthResponse(status="ready", service="community-api", version=__version__)
