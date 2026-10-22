import asyncio
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete
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
def test_community_roster_is_limited_to_owner_and_moderators() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id = uuid4()
        moderator_id = uuid4()
        member_id = uuid4()
        outsider_id = uuid4()
        other_owner_id = uuid4()
        community_id = uuid4()
        other_community_id = uuid4()
        community_public_id = uuid4()
        other_community_public_id = uuid4()
        user_public_ids = {
            owner_id: uuid4(),
            moderator_id: uuid4(),
            member_id: uuid4(),
            outsider_id: uuid4(),
            other_owner_id: uuid4(),
        }
        user_names = {
            owner_id: "Roster owner",
            moderator_id: "Roster moderator",
            member_id: "Roster member",
            outsider_id: "Roster outsider",
            other_owner_id: "Other community owner",
        }
        suffix = uuid4().hex
        community_slug = f"private-roster-{suffix}"
        other_community_slug = f"other-roster-{suffix}"
        community_public_ids = [community_public_id, other_community_public_id]
        user_ids = list(user_public_ids)
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        User(
                            id=user_id,
                            public_id=public_id,
                            display_name=user_names[user_id],
                            email=f"{user_id.hex}@example.test",
                        )
                        for user_id, public_id in user_public_ids.items()
                    ]
                )
                await session.flush()
                community = Community(
                    id=community_id,
                    public_id=community_public_id,
                    owner_id=owner_id,
                    name=f"Private roster {suffix}",
                    slug=community_slug,
                    topic="Roster testing",
                    description="Owner and moderator access only.",
                    access_type="invite_only",
                    expires_at=datetime.now(UTC) - timedelta(minutes=1),
                )
                other_community = Community(
                    id=other_community_id,
                    public_id=other_community_public_id,
                    owner_id=other_owner_id,
                    name=f"Other roster {suffix}",
                    slug=other_community_slug,
                    topic="Roster testing",
                    description="Separate community for access isolation.",
                    access_type="open",
                )
                joined_at = datetime.now(UTC) - timedelta(hours=1)
                memberships = [
                    CommunityMembership(
                        id=uuid4(),
                        community_id=community_id,
                        user_id=owner_id,
                        role="owner",
                        joined_at=joined_at,
                    ),
                    CommunityMembership(
                        id=uuid4(),
                        community_id=community_id,
                        user_id=moderator_id,
                        role="moderator",
                        joined_at=joined_at + timedelta(minutes=1),
                    ),
                    CommunityMembership(
                        id=uuid4(),
                        community_id=community_id,
                        user_id=member_id,
                        role="member",
                        joined_at=joined_at + timedelta(minutes=2),
                    ),
                    CommunityMembership(
                        id=uuid4(),
                        community_id=other_community_id,
                        user_id=other_owner_id,
                        role="owner",
                        joined_at=joined_at,
                    ),
                ]
                session.add_all([community, other_community, *memberships])
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
                    owner_first_page = await client.get(
                        f"/api/v1/communities/{community_slug}/members?limit=2&offset=0"
                    )
                    owner_second_page = await client.get(
                        f"/api/v1/communities/{community_slug}/members?limit=2&offset=2"
                    )
                    moderator_page = None
                    member_response = None
                    outsider_response = None
                    other_owner_response = None
                    unknown_response = await client.get(
                        f"/api/v1/communities/missing-{suffix}/members"
                    )
                    invalid_limit = await client.get(
                        f"/api/v1/communities/{community_slug}/members?limit=0"
                    )

                    active_user_id["value"] = moderator_id
                    moderator_page = await client.get(
                        f"/api/v1/communities/{community_slug}/members"
                    )
                    active_user_id["value"] = member_id
                    member_response = await client.get(
                        f"/api/v1/communities/{community_slug}/members"
                    )
                    active_user_id["value"] = outsider_id
                    outsider_response = await client.get(
                        f"/api/v1/communities/{community_slug}/members"
                    )
                    active_user_id["value"] = other_owner_id
                    other_owner_response = await client.get(
                        f"/api/v1/communities/{community_slug}/members"
                    )

                    app.dependency_overrides.pop(require_authenticated_principal)
                    anonymous_response = await client.get(
                        f"/api/v1/communities/{community_slug}/members"
                    )

            assert owner_first_page.status_code == owner_second_page.status_code == 200
            first_items = owner_first_page.json()["items"]
            second_items = owner_second_page.json()["items"]
            assert owner_first_page.json()["total"] == owner_second_page.json()["total"] == 3
            assert [(item["display_name"], item["role"]) for item in first_items] == [
                ("Roster owner", "owner"),
                ("Roster moderator", "moderator"),
            ]
            assert [(item["display_name"], item["role"]) for item in second_items] == [
                ("Roster member", "member")
            ]
            assert {item["user_public_id"] for item in first_items + second_items} == {
                str(user_public_ids[owner_id]),
                str(user_public_ids[moderator_id]),
                str(user_public_ids[member_id]),
            }
            assert all(
                set(item) == {"user_public_id", "display_name", "role", "joined_at"}
                for item in first_items + second_items
            )
            assert all(
                "id" not in item and "email" not in item for item in first_items + second_items
            )
            assert moderator_page is not None and moderator_page.status_code == 200
            assert moderator_page.json()["total"] == 3
            assert [item["user_public_id"] for item in moderator_page.json()["items"]] == [
                item["user_public_id"] for item in first_items + second_items
            ]
            assert member_response is not None and member_response.status_code == 403
            assert member_response.json() == {
                "detail": "You are not authorized to view this community's member roster."
            }
            assert outsider_response is not None and outsider_response.status_code == 403
            assert other_owner_response is not None and other_owner_response.status_code == 403
            assert unknown_response.status_code == 404
            assert unknown_response.json() == {"detail": "Community not found"}
            assert invalid_limit.status_code == 422
            assert anonymous_response.status_code == 401
        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(Community).where(Community.public_id.in_(community_public_ids))
                )
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
