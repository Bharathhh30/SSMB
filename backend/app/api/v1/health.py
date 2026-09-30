from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]
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
