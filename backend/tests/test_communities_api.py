import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.communities.models import Community
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


def test_discover_communities_returns_a_bounded_page() -> None:
    community = Community(
        id=uuid4(),
        owner_id=uuid4(),
        name="GATE Quant Lab",
        slug="gate-quant-lab",
        topic="Exam prep",
        description="Focused study sessions.",
        access_type="open",
        expires_at=None,
        created_at=datetime.now(UTC),
    )
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = 3
    rows = MagicMock()
    rows.all.return_value = [community]
    session.scalars.return_value = rows

    response = get(
        make_test_app(session),
        "/api/v1/communities?q=GATE&topic=Exam%20prep&limit=1&offset=2",
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": str(community.id),
                "slug": "gate-quant-lab",
                "name": "GATE Quant Lab",
                "topic": "Exam prep",
                "description": "Focused study sessions.",
                "access_type": "open",
                "expires_at": None,
                "created_at": community.created_at.isoformat().replace("+00:00", "Z"),
            }
        ],
        "total": 3,
        "limit": 1,
        "offset": 2,
    }
    session.scalar.assert_awaited_once()
    session.scalars.assert_awaited_once()


def test_community_discovery_fails_closed_without_database() -> None:
    response = get(make_test_app(None), "/api/v1/communities")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not configured"}


def test_discover_validates_pagination_before_querying() -> None:
    session = AsyncMock(spec=AsyncSession)

    response = get(make_test_app(session), "/api/v1/communities?limit=101")

    assert response.status_code == 422
    session.scalar.assert_not_awaited()
    session.scalars.assert_not_awaited()
