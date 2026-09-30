import asyncio

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import Settings
from app.main import create_app


def make_test_app(app_env: str = "test") -> FastAPI:
    return create_app(Settings(app_env=app_env, database_url=None))


async def request(app: FastAPI, path: str) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.get(path)


def get(app: FastAPI, path: str) -> Response:
    return asyncio.run(request(app, path))


def test_health_endpoint_reports_liveness() -> None:
    response = get(make_test_app(), "/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "community-api",
        "version": "0.1.0",
    }


def test_api_routes_are_versioned() -> None:
    response = get(make_test_app(), "/health")
    assert response.status_code == 404


def test_readiness_fails_closed_without_database_configuration() -> None:
    app = make_test_app()

    response = get(app, "/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not configured"}


def test_interactive_docs_are_not_exposed_outside_development() -> None:
    app = make_test_app("production")
    assert get(app, "/docs").status_code == 404
    assert get(app, "/openapi.json").status_code == 404


def test_interactive_docs_are_available_in_development() -> None:
    app = make_test_app("development")
    assert get(app, "/docs").status_code == 200
    assert get(app, "/openapi.json").status_code == 200
