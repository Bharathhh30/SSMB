import asyncio

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import Settings
from app.main import create_app


async def request(app: FastAPI, path: str) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.get(path)


def get(app: FastAPI, path: str) -> Response:
    return asyncio.run(request(app, path))


def test_health_endpoint_reports_liveness() -> None:
    response = get(create_app(Settings(app_env="test")), "/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "community-api",
        "version": "0.1.0",
    }


def test_api_routes_are_versioned() -> None:
    response = get(create_app(Settings(app_env="test")), "/health")
    assert response.status_code == 404


def test_interactive_docs_are_not_exposed_outside_development() -> None:
    app = create_app(Settings(app_env="production"))
    assert get(app, "/docs").status_code == 404
    assert get(app, "/openapi.json").status_code == 404


def test_interactive_docs_are_available_in_development() -> None:
    app = create_app(Settings(app_env="development"))
    assert get(app, "/docs").status_code == 200
    assert get(app, "/openapi.json").status_code == 200
