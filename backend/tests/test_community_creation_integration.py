import asyncio
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.features.auth.dependencies import require_authenticated_principal
from app.features.communities.models import Community, CommunityMembership
from app.features.users.models import User
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_community_creation_membership_and_owner_controls_are_authorized() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id = uuid4()
        joiner_id = uuid4()
        created_ids: list[UUID] = []
        expired_community_id = uuid4()
        suffix = uuid4().hex
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        User(id=owner_id, display_name="Community creator"),
                        User(id=joiner_id, display_name="Community joiner"),
                    ]
                )
                await session.flush()
                session.add(
                    Community(
                        id=expired_community_id,
                        owner_id=owner_id,
                        name="Expired community",
                        slug=f"expired-{suffix}",
                        topic="Testing",
                        access_type="open",
                        expires_at=datetime.now(UTC) - timedelta(minutes=1),
                    )
                )
                await session.commit()

            settings = Settings(
                app_env="test",
                database_url=SecretStr(TEST_DATABASE_URL),
            )
            app = create_app(settings)
            active_user_id = {"value": owner_id}
            app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
                user=SimpleNamespace(id=active_user_id["value"])
            )

            async with app.router.lifespan_context(app):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    first = await client.post(
                        "/api/v1/communities",
                        json={
                            "name": f"Study Circle {suffix[:8]}",
                            "topic": "Biology",
                            "access_type": "open",
                            "expires_at": "2030-01-01T00:00:00Z",
                        },
                    )
                    assert first.status_code == 201
                    first_data = first.json()
                    created_ids.append(UUID(first_data["id"]))
                    second = await client.post(
                        "/api/v1/communities",
                        json={
                            "name": f"Study Circle {suffix[:8]}",
                            "topic": "Biology",
                            "access_type": "invite_only",
                        },
                    )
                    assert second.status_code == 201
                    second_data = second.json()
                    created_ids.append(UUID(second_data["id"]))
                    active_user_id["value"] = joiner_id
                    concurrent_joins = await asyncio.gather(
                        client.post(f"/api/v1/communities/study-circle-{suffix[:8]}/join"),
                        client.post(f"/api/v1/communities/study-circle-{suffix[:8]}/join"),
                    )
                    private_join = await client.post(
                        f"/api/v1/communities/{second.json()['slug']}/join"
                    )
                    private_leave = await client.delete(
                        f"/api/v1/communities/{second.json()['slug']}/leave"
                    )
                    first_leave = await client.delete(
                        f"/api/v1/communities/study-circle-{suffix[:8]}/leave"
                    )
                    repeated_leave = await client.delete(
                        f"/api/v1/communities/study-circle-{suffix[:8]}/leave"
                    )
                    rejoin = await client.post(
                        f"/api/v1/communities/study-circle-{suffix[:8]}/join"
                    )
                    expired_join = await client.post(f"/api/v1/communities/expired-{suffix}/join")
                    active_user_id["value"] = owner_id
                    owner_leave = await client.delete(
                        f"/api/v1/communities/study-circle-{suffix[:8]}/leave"
                    )
                    private_owner_view = await client.get(
                        f"/api/v1/communities/{second_data['slug']}/manage"
                    )
                    private_public_view = await client.get(
                        f"/api/v1/communities/{second_data['slug']}"
                    )
                    active_user_id["value"] = joiner_id
                    member_owner_view = await client.get(
                        f"/api/v1/communities/study-circle-{suffix[:8]}/manage"
                    )
                    member_edit = await client.patch(
                        f"/api/v1/communities/study-circle-{suffix[:8]}",
                        json={"name": "Unauthorized rename"},
                    )
                    active_user_id["value"] = owner_id
                    owner_edit = await client.patch(
                        f"/api/v1/communities/study-circle-{suffix[:8]}",
                        json={
                            "name": f"Renamed Circle {suffix[:8]}",
                            "topic": "Updated biology",
                            "description": "Updated description",
                            "expires_at": None,
                        },
                    )

            assert first.status_code == 201
            assert second.status_code == 201
            assert first_data["slug"] == f"study-circle-{suffix[:8]}"
            assert second_data["slug"].startswith(f"study-circle-{suffix[:8]}-")
            assert first_data["slug"] != second_data["slug"]
            assert second_data["access_type"] == "invite_only"
            assert "owner_id" not in first_data
            assert sorted(response.status_code for response in concurrent_joins) == [200, 201], [
                response.text for response in concurrent_joins
            ]
            created_join = next(
                response for response in concurrent_joins if response.status_code == 201
            )
            assert created_join.json()["community_id"] == first_data["id"]
            assert created_join.json()["role"] == "member"
            assert "user_id" not in created_join.json()
            assert private_join.status_code == 404
            assert private_leave.status_code == 404
            assert first_leave.status_code == repeated_leave.status_code == 204
            assert rejoin.status_code == 201
            assert expired_join.status_code == 404
            assert owner_leave.status_code == 409
            assert private_owner_view.status_code == 200
            assert private_owner_view.json()["access_type"] == "invite_only"
            assert private_public_view.status_code == 404
            assert member_owner_view.status_code == 404
            assert member_edit.status_code == 404
            assert owner_edit.status_code == 200
            assert owner_edit.json()["name"] == f"Renamed Circle {suffix[:8]}"
            assert owner_edit.json()["topic"] == "Updated biology"
            assert owner_edit.json()["description"] == "Updated description"
            assert owner_edit.json()["expires_at"] is None
            assert owner_edit.json()["slug"] == first_data["slug"]

            async with session_factory() as session:
                memberships = await session.scalars(
                    select(CommunityMembership).where(
                        CommunityMembership.community_id.in_(created_ids)
                    )
                )
                rows = list(memberships.all())
                assert len(rows) == 3
                assert sum(row.user_id == owner_id for row in rows) == 2
                assert sum(row.user_id == joiner_id for row in rows) == 1
                assert sum(row.role == "owner" for row in rows) == 2

            with pytest.raises(IntegrityError):
                async with session_factory() as session:
                    session.add(
                        CommunityMembership(
                            community_id=created_ids[0],
                            user_id=owner_id,
                            role="member",
                        )
                    )
                    await session.flush()
        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(Community).where(Community.id.in_([*created_ids, expired_community_id]))
                )
                await session.execute(delete(User).where(User.id.in_([owner_id, joiner_id])))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
