import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.features.auth.dependencies import require_authenticated_principal
from app.features.communities.models import Community, CommunityMembership, CommunityRoleChange
from app.features.users.models import User
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_owner_role_changes_are_scoped_idempotent_concurrent_and_audited() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id = uuid4()
        member_id = uuid4()
        moderator_id = uuid4()
        other_owner_id = uuid4()
        other_member_id = uuid4()
        community_id = uuid4()
        other_community_id = uuid4()
        community_public_id = uuid4()
        other_community_public_id = uuid4()
        user_public_ids = {
            user_id: uuid4()
            for user_id in (owner_id, member_id, moderator_id, other_owner_id, other_member_id)
        }
        user_ids = list(user_public_ids)
        community_public_ids = [community_public_id, other_community_public_id]
        suffix = uuid4().hex
        community_slug = f"role-management-{suffix}"
        other_community_slug = f"other-role-group-{suffix}"
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        User(
                            id=user_id,
                            public_id=public_id,
                            display_name=f"Role test {index}",
                            email=f"{user_id.hex}@example.test",
                        )
                        for index, (user_id, public_id) in enumerate(user_public_ids.items())
                    ]
                )
                await session.flush()
                session.add_all(
                    [
                        Community(
                            id=community_id,
                            public_id=community_public_id,
                            owner_id=owner_id,
                            name=f"Role management {suffix}",
                            slug=community_slug,
                            topic="Role tests",
                            description="Owner-only role management integration test.",
                            access_type="open",
                        ),
                        Community(
                            id=other_community_id,
                            public_id=other_community_public_id,
                            owner_id=other_owner_id,
                            name=f"Other role community {suffix}",
                            slug=other_community_slug,
                            topic="Role tests",
                            description="Community for cross-scope target tests.",
                            access_type="open",
                        ),
                        CommunityMembership(
                            community_id=community_id,
                            user_id=owner_id,
                            role="owner",
                        ),
                        CommunityMembership(
                            community_id=community_id,
                            user_id=member_id,
                            role="member",
                        ),
                        CommunityMembership(
                            community_id=community_id,
                            user_id=moderator_id,
                            role="moderator",
                        ),
                        CommunityMembership(
                            community_id=other_community_id,
                            user_id=other_owner_id,
                            role="owner",
                        ),
                        CommunityMembership(
                            community_id=other_community_id,
                            user_id=other_member_id,
                            role="member",
                        ),
                    ]
                )
                await session.commit()

            settings = Settings(
                app_env="test",
                database_url=SecretStr(TEST_DATABASE_URL),
            )
            app = create_app(settings)
            active_user_id = {"value": owner_id}
            app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
                user=SimpleNamespace(
                    id=active_user_id["value"],
                    public_id=user_public_ids[active_user_id["value"]],
                )
            )
            member_role_path = (
                f"/api/v1/communities/{community_slug}/members/{user_public_ids[member_id]}/role"
            )
            moderator_role_path = (
                f"/api/v1/communities/{community_slug}/members/{user_public_ids[moderator_id]}/role"
            )

            async with app.router.lifespan_context(app):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    promoted = await client.put(member_role_path, json={"role": "moderator"})
                    repeated_promotion = await client.put(
                        member_role_path,
                        json={"role": "moderator"},
                    )
                    demoted = await client.put(moderator_role_path, json={"role": "member"})
                    repeated_demotion = await client.put(
                        moderator_role_path,
                        json={"role": "member"},
                    )
                    invalid_owner_promotion = await client.put(
                        f"/api/v1/communities/{community_slug}/members/"
                        f"{user_public_ids[owner_id]}/role",
                        json={"role": "moderator"},
                    )
                    cross_community_target = await client.put(
                        f"/api/v1/communities/{community_slug}/members/"
                        f"{user_public_ids[other_member_id]}/role",
                        json={"role": "moderator"},
                    )
                    unknown_target = await client.put(
                        f"/api/v1/communities/{community_slug}/members/{uuid4()}/role",
                        json={"role": "moderator"},
                    )
                    unknown_community = await client.put(
                        f"/api/v1/communities/missing-{suffix}/members/"
                        f"{user_public_ids[member_id]}/role",
                        json={"role": "moderator"},
                    )
                    invalid_owner_role = await client.put(
                        member_role_path,
                        json={"role": "owner"},
                    )
                    extra_body_field = await client.put(
                        member_role_path,
                        json={"role": "moderator", "user_id": str(member_id)},
                    )
                    malformed_target = await client.put(
                        f"/api/v1/communities/{community_slug}/members/not-a-uuid/role",
                        json={"role": "moderator"},
                    )

                    concurrent_changes = await asyncio.gather(
                        client.put(moderator_role_path, json={"role": "moderator"}),
                        client.put(moderator_role_path, json={"role": "moderator"}),
                    )

                    active_user_id["value"] = moderator_id
                    moderator_attempt = await client.put(
                        member_role_path,
                        json={"role": "member"},
                    )
                    active_user_id["value"] = member_id
                    member_attempt = await client.put(
                        moderator_role_path,
                        json={"role": "moderator"},
                    )
                    app.dependency_overrides.pop(require_authenticated_principal)
                    anonymous_attempt = await client.put(
                        member_role_path,
                        json={"role": "moderator"},
                    )

            assert promoted.status_code == 200
            assert promoted.json() == {
                "user_public_id": str(user_public_ids[member_id]),
                "previous_role": "member",
                "role": "moderator",
                "changed": True,
            }
            assert repeated_promotion.status_code == 200
            assert repeated_promotion.json()["changed"] is False
            assert demoted.status_code == 200
            assert demoted.json() == {
                "user_public_id": str(user_public_ids[moderator_id]),
                "previous_role": "moderator",
                "role": "member",
                "changed": True,
            }
            assert repeated_demotion.status_code == 200
            assert repeated_demotion.json()["changed"] is False
            assert invalid_owner_promotion.status_code == 409
            assert invalid_owner_promotion.json() == {
                "detail": "The community owner role can only be changed through ownership transfer."
            }
            assert cross_community_target.status_code == unknown_target.status_code == 404
            assert cross_community_target.json() == {"detail": "Community member not found"}
            assert unknown_community.status_code == 404
            assert unknown_community.json() == {"detail": "Community not found"}
            assert invalid_owner_role.status_code == extra_body_field.status_code == 422
            assert malformed_target.status_code == 422
            assert sorted(response.status_code for response in concurrent_changes) == [200, 200]
            assert sorted(response.json()["changed"] for response in concurrent_changes) == [
                False,
                True,
            ]
            assert moderator_attempt.status_code == member_attempt.status_code == 403
            assert anonymous_attempt.status_code == 401

            async with session_factory() as session:
                events_result = await session.scalars(
                    select(CommunityRoleChange)
                    .where(CommunityRoleChange.community_public_id == community_public_id)
                    .order_by(CommunityRoleChange.changed_at.asc(), CommunityRoleChange.id.asc())
                )
                events = list(events_result.all())
                assert len(events) == 3
                assert {
                    (event.target_public_id, event.previous_role, event.new_role)
                    for event in events
                } == {
                    (user_public_ids[member_id], "member", "moderator"),
                    (user_public_ids[moderator_id], "moderator", "member"),
                    (user_public_ids[moderator_id], "member", "moderator"),
                }
                assert all(event.actor_public_id == user_public_ids[owner_id] for event in events)
                assert all(event.community_id == community_id for event in events)

        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(CommunityRoleChange).where(
                        CommunityRoleChange.community_public_id.in_(community_public_ids)
                    )
                )
                await session.execute(
                    delete(Community).where(Community.public_id.in_(community_public_ids))
                )
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
