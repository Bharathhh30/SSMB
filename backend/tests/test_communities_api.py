import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.auth.dependencies import require_authenticated_principal
from app.features.communities import service as community_service
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


async def post_json(app: FastAPI, path: str, payload: dict[str, object]) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.post(path, json=payload)


async def delete_path(app: FastAPI, path: str) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.delete(path)


async def patch_json(app: FastAPI, path: str, payload: dict[str, object]) -> Response:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.patch(path, json=payload)


def get(app: FastAPI, path: str) -> Response:
    return asyncio.run(request(app, path))


def post(app: FastAPI, path: str, payload: dict[str, object]) -> Response:
    return asyncio.run(post_json(app, path, payload))


def delete(app: FastAPI, path: str) -> Response:
    return asyncio.run(delete_path(app, path))


def patch(app: FastAPI, path: str, payload: dict[str, object]) -> Response:
    return asyncio.run(patch_json(app, path, payload))


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


@pytest.mark.parametrize(
    "query",
    [
        "limit=not-an-integer",
        "offset=1.5",
        "limit=0",
        "limit=101",
        "limit=-1",
        "offset=-1",
        f"q={'q' * 121}",
        f"topic={'t' * 81}",
    ],
)
def test_discover_rejects_out_of_range_query_parameters(query: str) -> None:
    session = AsyncMock(spec=AsyncSession)

    response = get(make_test_app(session), f"/api/v1/communities?{query}")

    assert response.status_code == 422
    session.scalar.assert_not_awaited()
    session.scalars.assert_not_awaited()


def test_discover_accepts_blank_filters_as_noops() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = 0
    rows = MagicMock()
    rows.all.return_value = []
    session.scalars.return_value = rows

    response = get(make_test_app(session), "/api/v1/communities?q=&topic=%20%20")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 30, "offset": 0}
    statement = session.scalars.await_args.args[0]
    sql = str(statement)
    assert "ILIKE" not in sql
    assert "trim(communities.topic)" not in sql


def test_discover_accepts_inclusive_query_bounds() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = 0
    rows = MagicMock()
    rows.all.return_value = []
    session.scalars.return_value = rows

    response = get(
        make_test_app(session),
        f"/api/v1/communities?q={'q' * 120}&topic={'t' * 80}&limit=100&offset=0",
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 100, "offset": 0}


def test_public_community_detail_returns_a_safe_preview() -> None:
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
    session.scalar.return_value = community

    response = get(make_test_app(session), "/api/v1/communities/gate-quant-lab")

    assert response.status_code == 200
    assert response.json()["slug"] == "gate-quant-lab"
    assert response.json()["access_type"] == "open"
    assert "owner_id" not in response.json()
    session.scalar.assert_awaited_once()


def test_private_or_unknown_community_detail_is_not_disclosed() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None

    response = get(make_test_app(session), "/api/v1/communities/private-circle")

    assert response.status_code == 404
    assert response.json() == {"detail": "Community not found"}


@pytest.mark.parametrize(
    "slug",
    [
        "Not-A-Slug",
        "-leading-hyphen",
        "trailing-hyphen-",
        "double--hyphen",
        "a" * 141,
    ],
)
def test_community_detail_rejects_invalid_slugs(slug: str) -> None:
    session = AsyncMock(spec=AsyncSession)

    response = get(make_test_app(session), f"/api/v1/communities/{slug}")

    assert response.status_code == 422
    session.scalar.assert_not_awaited()


def test_community_detail_accepts_maximum_length_slug() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None

    response = get(make_test_app(session), f"/api/v1/communities/{'a' * 140}")

    assert response.status_code == 404
    session.scalar.assert_awaited_once()


def test_community_creation_requires_authentication() -> None:
    session = AsyncMock(spec=AsyncSession)
    payload = {
        "name": "Study Circle",
        "topic": "Biology",
        "access_type": "open",
    }

    response = post(make_test_app(session), "/api/v1/communities", payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    session.add_all.assert_not_called()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("join", "/api/v1/communities/study-circle/join"),
        ("leave", "/api/v1/communities/study-circle/leave"),
    ],
)
def test_membership_changes_require_authentication(method: str, path: str) -> None:
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)

    response = post(app, path, {}) if method == "join" else delete(app, path)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    session.add_all.assert_not_called()


def test_owner_management_requires_authentication() -> None:
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)

    read = get(app, "/api/v1/communities/study-circle/manage")
    update = patch(
        app,
        "/api/v1/communities/study-circle",
        {"name": "Updated study circle"},
    )

    assert read.status_code == update.status_code == 401
    assert read.json() == update.json() == {"detail": "Authentication required"}
    session.scalar.assert_not_awaited()


def test_community_creation_returns_only_public_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    owner_id = uuid4()
    community = Community(
        id=uuid4(),
        owner_id=owner_id,
        name="Study Circle",
        slug="study-circle",
        topic="Biology",
        description="A study group.",
        access_type="open",
        expires_at=None,
        created_at=datetime.now(UTC),
    )
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)
    principal = SimpleNamespace(user=SimpleNamespace(id=owner_id))
    app.dependency_overrides[require_authenticated_principal] = lambda: principal
    create = AsyncMock(return_value=community)
    monkeypatch.setattr(community_service, "create_community", create)

    response = post(
        app,
        "/api/v1/communities",
        {
            "name": "  Study Circle  ",
            "topic": " Biology ",
            "description": " A study group. ",
            "access_type": "open",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(community.id),
        "slug": "study-circle",
        "name": "Study Circle",
        "topic": "Biology",
        "description": "A study group.",
        "access_type": "open",
        "expires_at": None,
        "created_at": community.created_at.isoformat().replace("+00:00", "Z"),
    }
    assert "owner_id" not in response.json()
    create.assert_awaited_once()
    assert create.await_args.kwargs["owner_id"] == owner_id
    assert create.await_args.kwargs["data"].name == "Study Circle"


@pytest.mark.parametrize(
    "payload",
    [
        {"topic": "Biology", "access_type": "open"},
        {"name": " ", "topic": "Biology", "access_type": "open"},
        {"name": "Study", "topic": "\t", "access_type": "open"},
        {"name": "Study", "topic": "Biology", "access_type": "public"},
        {"name": "s" * 121, "topic": "Biology", "access_type": "open"},
        {"name": "Study", "topic": "t" * 81, "access_type": "open"},
        {
            "name": "Study",
            "topic": "Biology",
            "description": "d" * 5001,
            "access_type": "open",
        },
        {
            "name": "Study",
            "topic": "Biology",
            "description": None,
            "access_type": "open",
        },
        {"name": "Study", "topic": "Biology", "access_type": None},
        {
            "name": "Study",
            "topic": "Biology",
            "access_type": "open",
            "unexpected": "value",
        },
        {
            "name": "Study",
            "topic": "Biology",
            "access_type": "open",
            "expires_at": "2030-01-01T00:00:00",
        },
    ],
)
def test_community_creation_rejects_invalid_payloads(
    payload: dict[str, object],
) -> None:
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)
    app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
        user=SimpleNamespace(id=uuid4())
    )

    response = post(app, "/api/v1/communities", payload)

    assert response.status_code == 422
    session.add_all.assert_not_called()


def test_community_creation_hides_slug_conflict_details(monkeypatch: pytest.MonkeyPatch) -> None:
    owner_id = uuid4()
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)
    app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
        user=SimpleNamespace(id=owner_id)
    )

    async def fail_with_slug_conflict(*_args: object, **_kwargs: object) -> Community:
        raise community_service.CommunitySlugConflict

    monkeypatch.setattr(community_service, "create_community", fail_with_slug_conflict)
    response = post(
        app,
        "/api/v1/communities",
        {
            "name": "Study Circle",
            "topic": "Biology",
            "access_type": "open",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "A community URL conflict occurred. Please retry."}


def test_owner_can_read_and_update_community_without_changing_its_slug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_id = uuid4()
    community = Community(
        id=uuid4(),
        owner_id=owner_id,
        name="Study Circle",
        slug="study-circle",
        topic="Biology",
        description="Original description",
        access_type="open",
        expires_at=None,
        created_at=datetime.now(UTC),
    )
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)
    app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
        user=SimpleNamespace(id=owner_id)
    )
    get_owned = AsyncMock(return_value=community)
    update_owned = AsyncMock(return_value=community)
    monkeypatch.setattr(community_service, "get_owned_community", get_owned)
    monkeypatch.setattr(community_service, "update_owned_community", update_owned)

    managed = get(app, "/api/v1/communities/study-circle/manage")
    updated = patch(
        app,
        "/api/v1/communities/study-circle",
        {
            "name": "  Updated Study Circle ",
            "description": " Updated description ",
            "expires_at": None,
        },
    )

    assert managed.status_code == 200
    assert managed.json()["slug"] == "study-circle"
    assert "owner_id" not in managed.json()
    assert updated.status_code == 200
    assert update_owned.await_args.kwargs["owner_id"] == owner_id
    update_data = update_owned.await_args.kwargs["data"]
    assert update_data.name == "Updated Study Circle"
    assert update_data.description == "Updated description"
    assert "expires_at" in update_data.model_fields_set
    assert update_data.expires_at is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
        {"topic": None},
        {"description": None},
        {"access_type": None},
        {"name": " "},
        {"name": "n" * 121},
        {"topic": "t" * 81},
        {"description": "d" * 5001},
        {"access_type": "public"},
        {"expires_at": "2030-01-01T00:00:00"},
        {"expires_at": "2020-01-01T00:00:00Z"},
        {"unexpected": "field"},
    ],
)
def test_owner_update_rejects_invalid_patch_payloads(payload: dict[str, object]) -> None:
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)
    app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
        user=SimpleNamespace(id=uuid4())
    )

    response = patch(app, "/api/v1/communities/study-circle", payload)

    assert response.status_code == 422
    session.execute.assert_not_awaited()


def test_community_creation_rejects_expired_timestamp() -> None:
    session = AsyncMock(spec=AsyncSession)
    app = make_test_app(session)
    app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
        user=SimpleNamespace(id=uuid4())
    )
    expired_at = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()

    response = post(
        app,
        "/api/v1/communities",
        {
            "name": "Study",
            "topic": "Biology",
            "access_type": "open",
            "expires_at": expired_at,
        },
    )

    assert response.status_code == 422
    session.add_all.assert_not_called()
