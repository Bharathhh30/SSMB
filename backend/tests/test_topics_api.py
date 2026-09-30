import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.main import create_app


def make_test_app(session: AsyncSession | None) -> FastAPI:
    app = create_app()
    if session is not None:

        async def override_session() -> AsyncIterator[AsyncSession]:
            yield session

        app.dependency_overrides[get_database_session] = override_session
    return app


async def request(app: FastAPI, path: str) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.get(path)


def get(app: FastAPI, path: str) -> Response:
    return asyncio.run(request(app, path))


def test_public_topics_returns_distinct_discoverable_topics() -> None:
    session = AsyncMock(spec=AsyncSession)
    rows = MagicMock()
    rows.all.return_value = ["Exam prep", "Languages", "Technology"]
    session.scalars.return_value = rows

    response = get(make_test_app(session), "/api/v1/topics")

    assert response.status_code == 200
    assert response.json() == {"items": ["Exam prep", "Languages", "Technology"]}
    session.scalars.assert_awaited_once()


def test_public_topics_fails_closed_without_database() -> None:
    response = get(make_test_app(None), "/api/v1/topics")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not configured"}
