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
        created_public_ids: list[UUID] = []
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
                    first_slug = first_data["slug"]
                    first_public_id = UUID(first_data["public_id"])
                    created_public_ids.append(first_public_id)
                    initial_public_preview = await client.get(f"/api/v1/communities/{first_slug}")
                    duplicate_name = await client.post(
                        "/api/v1/communities",
                        json={
                            "name": f" study circle {suffix[:8].upper()} ",
                            "topic": "Another topic",
                            "access_type": "invite_only",
                        },
                    )
                    second = await client.post(
                        "/api/v1/communities",
                        json={
                            "name": f"Private Circle {suffix[:8]}",
                            "topic": "Biology",
                            "access_type": "invite_only",
                        },
                    )
                    assert second.status_code == 201
                    second_data = second.json()
                    second_slug = second_data["slug"]
                    second_public_id = UUID(second_data["public_id"])
                    created_public_ids.append(second_public_id)
                    concurrent_creations = await asyncio.gather(
                        *[
                            client.post(
                                "/api/v1/communities",
                                json={
                                    "name": f"Concurrent Group {suffix[:8]}",
                                    "topic": "Concurrency",
                                    "access_type": "open",
                                },
                            )
                            for _ in range(2)
                        ]
                    )
                    successful_creation = next(
                        response for response in concurrent_creations if response.status_code == 201
                    )
                    concurrent_data = successful_creation.json()
                    concurrent_slug = concurrent_data["slug"]
                    concurrent_public_id = UUID(concurrent_data["public_id"])
                    created_public_ids.append(concurrent_public_id)
                    owned_communities = await client.get("/api/v1/communities/mine")
                    active_user_id["value"] = joiner_id
                    no_owned_communities = await client.get("/api/v1/communities/mine")
                    concurrent_joins = await asyncio.gather(
                        client.post(f"/api/v1/communities/{first_slug}/join"),
                        client.post(f"/api/v1/communities/{first_slug}/join"),
                    )
                    private_join = await client.post(f"/api/v1/communities/{second_slug}/join")
                    private_leave = await client.delete(f"/api/v1/communities/{second_slug}/leave")
                    first_leave = await client.delete(f"/api/v1/communities/{first_slug}/leave")
                    repeated_leave = await client.delete(f"/api/v1/communities/{first_slug}/leave")
                    rejoin = await client.post(f"/api/v1/communities/{first_slug}/join")
                    joined_public_preview = await client.get(f"/api/v1/communities/{first_slug}")
                    expired_join = await client.post(f"/api/v1/communities/expired-{suffix}/join")
                    active_user_id["value"] = owner_id
                    unknown_owner_view = await client.get(
                        "/api/v1/communities/unknown-community/manage"
                    )
                    unknown_owner_edit = await client.patch(
                        "/api/v1/communities/unknown-community",
                        json={"name": "No such community"},
                    )
                    owner_leave = await client.delete(f"/api/v1/communities/{first_slug}/leave")
                    private_owner_view = await client.get(
                        f"/api/v1/communities/{second_slug}/manage"
                    )
                    private_public_view = await client.get(f"/api/v1/communities/{second_slug}")
                    active_user_id["value"] = joiner_id
                    member_owner_view = await client.get(f"/api/v1/communities/{first_slug}/manage")
                    member_edit = await client.patch(
                        f"/api/v1/communities/{first_slug}",
                        json={"name": "Unauthorized rename"},
                    )
                    active_user_id["value"] = owner_id
                    owner_edit = await client.patch(
                        f"/api/v1/communities/{first_slug}",
                        json={
                            "name": f"Renamed Circle {suffix[:8]}",
                            "topic": "Updated biology",
                            "description": "Updated description",
                            "expires_at": None,
                        },
                    )

            assert first.status_code == 201
            assert second.status_code == 201
            assert duplicate_name.status_code == 409
            assert duplicate_name.json() == {
                "detail": "A community with this name already exists. Choose a different name."
            }
            assert sorted(response.status_code for response in concurrent_creations) == [201, 409]
            conflicting_creation = next(
                response for response in concurrent_creations if response.status_code == 409
            )
            assert conflicting_creation.json() == {
                "detail": "A community with this name already exists. Choose a different name."
            }
            assert initial_public_preview.status_code == 200
            assert initial_public_preview.json()["member_count"] == 1
            assert first_slug == f"study-circle-{suffix[:8]}-{first_public_id.hex}"
            assert second_slug == f"private-circle-{suffix[:8]}-{second_public_id.hex}"
            assert concurrent_slug == (f"concurrent-group-{suffix[:8]}-{concurrent_public_id.hex}")
            assert owned_communities.status_code == 200
            assert owned_communities.json()["total"] == 4
            assert {item["slug"] for item in owned_communities.json()["items"]} == {
                f"expired-{suffix}",
                first_slug,
                second_slug,
                concurrent_slug,
            }
            assert all("id" not in item for item in owned_communities.json()["items"])
            assert no_owned_communities.status_code == 200
            assert no_owned_communities.json()["items"] == []
            assert no_owned_communities.json()["total"] == 0
            assert second_data["access_type"] == "invite_only"
            assert "id" not in first_data
            assert "id" not in second_data
            assert "id" not in concurrent_data
            assert "owner_id" not in first_data
            assert sorted(response.status_code for response in concurrent_joins) == [200, 201], [
                response.text for response in concurrent_joins
            ]
            created_join = next(
                response for response in concurrent_joins if response.status_code == 201
            )
            assert created_join.json()["community_slug"] == first_slug
            assert "community_id" not in created_join.json()
            assert "id" not in created_join.json()
            assert created_join.json()["role"] == "member"
            assert "user_id" not in created_join.json()
            assert private_join.status_code == 404
            assert private_leave.status_code == 404
            assert first_leave.status_code == repeated_leave.status_code == 204
            assert rejoin.status_code == 201
            assert joined_public_preview.status_code == 200
            assert joined_public_preview.json()["member_count"] == 2
            assert expired_join.status_code == 404
            assert unknown_owner_view.status_code == 404
            assert unknown_owner_view.json() == {"detail": "Community not found"}
            assert unknown_owner_edit.status_code == 404
            assert unknown_owner_edit.json() == {"detail": "Community not found"}
            assert owner_leave.status_code == 409
            assert private_owner_view.status_code == 200
            assert private_owner_view.json()["access_type"] == "invite_only"
            assert private_public_view.status_code == 404
            assert member_owner_view.status_code == 403
            assert member_owner_view.json() == {
                "detail": "You are not authorized to manage this community."
            }
            assert member_edit.status_code == 403
            assert member_edit.json() == {
                "detail": "You are not authorized to manage this community."
            }
            assert owner_edit.status_code == 200
            assert owner_edit.json()["name"] == f"Renamed Circle {suffix[:8]}"
            assert owner_edit.json()["topic"] == "Updated biology"
            assert owner_edit.json()["description"] == "Updated description"
            assert owner_edit.json()["expires_at"] is None
            assert owner_edit.json()["slug"] == first_data["slug"]

            async with session_factory() as session:
                created_communities = await session.scalars(
                    select(Community).where(Community.public_id.in_(created_public_ids))
                )
                created_community_rows = list(created_communities.all())
                assert len(created_community_rows) == 3
                assert all(row.public_id != row.id for row in created_community_rows)
                assert all(row.slug.endswith(row.public_id.hex) for row in created_community_rows)
                memberships = await session.scalars(
                    select(CommunityMembership).where(
                        CommunityMembership.community_id.in_(
                            [row.id for row in created_community_rows]
                        )
                    )
                )
                rows = list(memberships.all())
                assert len(rows) == 4
                assert sum(row.user_id == owner_id for row in rows) == 3
                assert sum(row.user_id == joiner_id for row in rows) == 1
                assert sum(row.role == "owner" for row in rows) == 3

            with pytest.raises(IntegrityError):
                async with session_factory() as session:
                    session.add(
                        CommunityMembership(
                            community_id=created_community_rows[0].id,
                            user_id=owner_id,
                            role="member",
                        )
                    )
                    await session.flush()

            with pytest.raises(IntegrityError):
                async with session_factory() as session:
                    session.add(
                        Community(
                            owner_id=owner_id,
                            name=f" RENAMED CIRCLE {suffix[:8].upper()} ",
                            slug=f"name-collision-{suffix}",
                            topic="Another topic",
                            access_type="open",
                        )
                    )
                    await session.flush()
        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(Community).where(
                        Community.public_id.in_(created_public_ids)
                        | (Community.id == expired_community_id)
                    )
                )
                await session.execute(delete(User).where(User.id.in_([owner_id, joiner_id])))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
