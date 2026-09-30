import asyncio
import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import Settings
from app.main import create_app


def make_test_app() -> FastAPI:
    return create_app(Settings(app_env="test", database_url=None))


async def request(app: FastAPI, path: str) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.get(path)


def get(app: FastAPI, path: str) -> Response:
    return asyncio.run(request(app, path))


def request_log(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    records = [record for record in caplog.records if record.name == "app.http"]
    assert len(records) == 1
    return json.loads(records[0].message)


def test_request_logs_use_route_templates_and_exclude_query_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = make_test_app()
    caplog.set_level(logging.INFO, logger="app.http")

    response = get(app, "/api/v1/health?access_token=must-not-be-logged")

    record = request_log(caplog)
    assert response.status_code == 200
    assert response.headers["x-request-id"] == record["request_id"]
    assert len(str(record["request_id"])) == 32
    assert record["event"] == "http.request"
    assert record["method"] == "GET"
    assert record["route"] == "/health"
    assert record["status_code"] == 200
    assert "must-not-be-logged" not in caplog.text


def test_unhandled_errors_return_safe_response_and_correlate_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = make_test_app()

    def raise_unexpected_error() -> None:
        raise RuntimeError("internal details must not reach the client or access log")

    app.add_api_route("/api/v1/test-failure", raise_unexpected_error, methods=["GET"])
    caplog.set_level(logging.ERROR, logger="app.http")

    response = get(app, "/api/v1/test-failure")

    record = request_log(caplog)
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers["x-request-id"] == record["request_id"]
    assert record["failed"] is True
    assert record["error_type"] == "RuntimeError"
    assert record["route"] == "/api/v1/test-failure"
    assert record["status_code"] == 500
    assert "internal details" not in caplog.text
