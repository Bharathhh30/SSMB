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
from app.features.communities.models import (
    Community,
    CommunityMembership,
    CommunityOwnershipChange,
)
from app.features.users.models import User
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_owner_can_atomically_transfer_community_ownership_to_a_member() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id = uuid4()
        moderator_candidate_id = uuid4()
        member_candidate_id = uuid4()
        outsider_id = uuid4()
        other_owner_id = uuid4()
        other_member_id = uuid4()
        community_id = uuid4()
        other_community_id = uuid4()
        community_public_id = uuid4()
        other_community_public_id = uuid4()
        user_public_ids = {
            user_id: uuid4()
            for user_id in (
                owner_id,
                moderator_candidate_id,
                member_candidate_id,
                outsider_id,
                other_owner_id,
                other_member_id,
            )
        }
        user_ids = list(user_public_ids)
        community_public_ids = [community_public_id, other_community_public_id]
        suffix = uuid4().hex
        community_slug = f"ownership-transfer-{suffix}"
        other_community_slug = f"other-ownership-{suffix}"
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        User(
                            id=user_id,
                            public_id=public_id,
                            display_name=f"Transfer test {index}",
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
                            name=f"Transfer community {suffix}",
                            slug=community_slug,
                            topic="Ownership tests",
                            description="Test the atomic ownership-transfer workflow.",
                            access_type="open",
                        ),
                        Community(
                            id=other_community_id,
                            public_id=other_community_public_id,
                            owner_id=other_owner_id,
                            name=f"Other transfer community {suffix}",
                            slug=other_community_slug,
                            topic="Ownership tests",
                            description="Used to verify community-scoped targets.",
                            access_type="open",
                        ),
                        CommunityMembership(
                            community_id=community_id,
                            user_id=owner_id,
                            role="owner",
                        ),
                        CommunityMembership(
                            community_id=community_id,
                            user_id=moderator_candidate_id,
                            role="moderator",
                        ),
                        CommunityMembership(
                            community_id=community_id,
                            user_id=member_candidate_id,
                            role="member",
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
            transfer_path = f"/api/v1/communities/{community_slug}/transfer-ownership"
            moderator_target_body = {
                "new_owner_public_id": str(user_public_ids[moderator_candidate_id])
            }
            member_target_body = {"new_owner_public_id": str(user_public_ids[member_candidate_id])}

            async with app.router.lifespan_context(app):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    self_transfer = await client.post(
                        transfer_path,
                        json={"new_owner_public_id": str(user_public_ids[owner_id])},
                    )
                    unknown_target = await client.post(
                        transfer_path,
                        json={"new_owner_public_id": str(uuid4())},
                    )
                    cross_community_target = await client.post(
                        transfer_path,
                        json={"new_owner_public_id": str(user_public_ids[other_member_id])},
                    )
                    unknown_community = await client.post(
                        f"/api/v1/communities/missing-{suffix}/transfer-ownership",
                        json=member_target_body,
                    )
                    missing_body_field = await client.post(transfer_path, json={})
                    extra_body_field = await client.post(
                        transfer_path,
                        json={**member_target_body, "user_id": str(member_candidate_id)},
                    )
                    malformed_target = await client.post(
                        transfer_path,
                        json={"new_owner_public_id": "not-a-uuid"},
                    )

                    active_user_id["value"] = moderator_candidate_id
                    moderator_transfer = await client.post(
                        transfer_path,
                        json=member_target_body,
                    )
                    active_user_id["value"] = member_candidate_id
                    member_transfer = await client.post(
                        transfer_path,
                        json=moderator_target_body,
                    )
                    active_user_id["value"] = owner_id
                    concurrent_transfers = await asyncio.gather(
                        client.post(transfer_path, json=moderator_target_body),
                        client.post(transfer_path, json=member_target_body),
                    )
                    successful_transfer = next(
                        response for response in concurrent_transfers if response.status_code == 200
                    )
                    transferred_data = successful_transfer.json()
                    new_owner_id = next(
                        user_id
                        for user_id, public_id in user_public_ids.items()
                        if str(public_id) == transferred_data["new_owner_public_id"]
                    )
                    old_owner_view = await client.get(
                        f"/api/v1/communities/{community_slug}/manage"
                    )
                    old_owner_memberships = await client.get("/api/v1/communities/memberships/me")
                    old_owner_leave = await client.delete(
                        f"/api/v1/communities/{community_slug}/leave"
                    )
                    active_user_id["value"] = new_owner_id
                    new_owner_view = await client.get(
                        f"/api/v1/communities/{community_slug}/manage"
                    )
                    new_owner_memberships = await client.get("/api/v1/communities/memberships/me")
                    new_owner_leave = await client.delete(
                        f"/api/v1/communities/{community_slug}/leave"
                    )
                    app.dependency_overrides.pop(require_authenticated_principal)
                    anonymous_transfer = await client.post(
                        transfer_path,
                        json=member_target_body,
                    )

            assert self_transfer.status_code == 409
            assert self_transfer.json() == {
                "detail": "Select a different member as the new community owner."
            }
            assert unknown_target.status_code == cross_community_target.status_code == 404
            assert unknown_target.json() == {
                "detail": "The new owner must already be a member of this community."
            }
            assert cross_community_target.json() == unknown_target.json()
            assert unknown_community.status_code == 404
            assert unknown_community.json() == {"detail": "Community not found"}
            assert missing_body_field.status_code == extra_body_field.status_code == 422
            assert malformed_target.status_code == 422
            assert moderator_transfer.status_code == member_transfer.status_code == 403
            assert sorted(response.status_code for response in concurrent_transfers) == [200, 403]
            assert set(transferred_data) == {
                "community_public_id",
                "previous_owner_public_id",
                "new_owner_public_id",
                "transferred_at",
            }
            assert transferred_data["community_public_id"] == str(community_public_id)
            assert transferred_data["previous_owner_public_id"] == str(user_public_ids[owner_id])
            assert transferred_data["new_owner_public_id"] == str(user_public_ids[new_owner_id])
            assert transferred_data["transferred_at"]
            assert "community_id" not in transferred_data
            assert "previous_owner_user_id" not in transferred_data
            assert "new_owner_user_id" not in transferred_data
            assert old_owner_view.status_code == 403
            assert old_owner_memberships.status_code == 200
            assert old_owner_memberships.json()["items"][0]["role"] == "member"
            assert old_owner_leave.status_code == 204
            assert new_owner_view.status_code == 200
            assert new_owner_view.json()["public_id"] == str(community_public_id)
            assert new_owner_memberships.status_code == 200
            assert new_owner_memberships.json()["items"][0]["role"] == "owner"
            assert new_owner_leave.status_code == 409
            assert anonymous_transfer.status_code == 401

            async with session_factory() as session:
                community = await session.scalar(
                    select(Community).where(Community.id == community_id)
                )
                assert community is not None
                assert community.owner_id == new_owner_id
                memberships_result = await session.scalars(
                    select(CommunityMembership).where(
                        CommunityMembership.community_id == community_id
                    )
                )
                memberships = list(memberships_result.all())
                roles_by_user = {membership.user_id: membership.role for membership in memberships}
                assert owner_id not in roles_by_user
                assert roles_by_user[new_owner_id] == "owner"
                assert sum(role == "owner" for role in roles_by_user.values()) == 1
                changes_result = await session.scalars(
                    select(CommunityOwnershipChange).where(
                        CommunityOwnershipChange.community_public_id == community_public_id
                    )
                )
                changes = list(changes_result.all())
                assert len(changes) == 1
                assert changes[0].previous_owner_public_id == user_public_ids[owner_id]
                assert changes[0].new_owner_public_id == user_public_ids[new_owner_id]
                assert changes[0].previous_owner_user_id == owner_id
                assert changes[0].new_owner_user_id == new_owner_id

        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(CommunityOwnershipChange).where(
                        CommunityOwnershipChange.community_public_id.in_(community_public_ids)
                    )
                )
                await session.execute(
                    delete(Community).where(Community.public_id.in_(community_public_ids))
                )
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
