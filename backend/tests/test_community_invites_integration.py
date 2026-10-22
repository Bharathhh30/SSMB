import asyncio
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.features.auth.dependencies import require_authenticated_principal
from app.features.auth.models import AuthRateLimitBucket
from app.features.auth.security import hash_one_time_token
from app.features.communities.models import Community, CommunityInvite, CommunityMembership
from app.features.communities.service import COMMUNITY_INVITE_ACCEPT_LIMIT
from app.features.users.models import User
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_owner_invites_are_single_use_revocable_expiring_and_rate_limited() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id, first_member_id, replay_user_id, race_user_a, race_user_b, brute_user_id = (
            uuid4() for _ in range(6)
        )
        user_ids = [
            owner_id,
            first_member_id,
            replay_user_id,
            race_user_a,
            race_user_b,
            brute_user_id,
        ]
        community_public_ids: list[UUID] = []
        rate_limit_secret = uuid4().hex
        rate_limit_hashes = {
            hmac.new(
                rate_limit_secret.encode(),
                f"{purpose}\0{user_id}".encode(),
                hashlib.sha256,
            ).hexdigest()
            for purpose in ("community_invite_create", "community_invite_accept")
            for user_id in user_ids
        }
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        User(id=user_id, display_name=f"Invite test {index}")
                        for index, user_id in enumerate(user_ids)
                    ]
                )
                await session.commit()

            settings = Settings(
                app_env="test",
                database_url=SecretStr(TEST_DATABASE_URL),
                auth_rate_limit_secret=SecretStr(rate_limit_secret),
                auth_rate_limit_window_seconds=3600,
            )
            app = create_app(settings)

            async def test_principal(request: Request) -> SimpleNamespace:
                return SimpleNamespace(
                    user=SimpleNamespace(id=UUID(request.headers["x-test-user-id"]))
                )

            app.dependency_overrides[require_authenticated_principal] = test_principal

            async with app.router.lifespan_context(app):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:

                    def headers(user_id: UUID) -> dict[str, str]:
                        return {"x-test-user-id": str(user_id)}

                    private = await client.post(
                        "/api/v1/communities",
                        headers=headers(owner_id),
                        json={
                            "name": f"Invite-only {uuid4().hex[:8]}",
                            "topic": "Testing",
                            "access_type": "invite_only",
                        },
                    )
                    assert private.status_code == 201
                    private_data = private.json()
                    assert "id" not in private_data
                    community_public_id = UUID(private_data["public_id"])
                    community_public_ids.append(community_public_id)
                    slug = private_data["slug"]

                    open_community = await client.post(
                        "/api/v1/communities",
                        headers=headers(owner_id),
                        json={
                            "name": f"Open {uuid4().hex[:8]}",
                            "topic": "Testing",
                            "access_type": "open",
                        },
                    )
                    assert open_community.status_code == 201
                    open_community_data = open_community.json()
                    assert "id" not in open_community_data
                    community_public_ids.append(UUID(open_community_data["public_id"]))

                    first_invite_response = await client.post(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )
                    assert first_invite_response.status_code == 201
                    first_invite = first_invite_response.json()
                    first_invite_public_id = UUID(first_invite["invite_public_id"])
                    assert "id" not in first_invite
                    assert "invite_id" not in first_invite
                    raw_token = first_invite["invite_token"]
                    expires_at = datetime.fromisoformat(
                        first_invite["expires_at"].replace("Z", "+00:00")
                    )
                    assert datetime.now(UTC) + timedelta(days=6) < expires_at
                    assert expires_at <= datetime.now(UTC) + timedelta(days=7)

                    async with session_factory() as session:
                        stored_invite = await session.scalar(
                            select(CommunityInvite).where(
                                CommunityInvite.public_id == first_invite_public_id
                            )
                        )
                        assert stored_invite is not None
                        assert stored_invite.token_hash == hash_one_time_token(raw_token)
                        assert stored_invite.token_hash != raw_token
                        assert stored_invite.id != first_invite_public_id

                    initial_invite_list = await client.get(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )
                    assert initial_invite_list.status_code == 200
                    assert initial_invite_list.json()["total"] == 1
                    assert initial_invite_list.json()["items"][0]["status"] == "active"
                    assert "invite_token" not in initial_invite_list.json()["items"][0]

                    non_owner_create = await client.post(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(first_member_id),
                    )
                    non_owner_list = await client.get(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(first_member_id),
                    )
                    open_invite = await client.post(
                        f"/api/v1/communities/{open_community.json()['slug']}/invites",
                        headers=headers(owner_id),
                    )

                    first_accept = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(first_member_id),
                        json={"invite_token": raw_token},
                    )
                    same_user_retry = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(first_member_id),
                        json={"invite_token": raw_token},
                    )
                    replay_by_other_user = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(replay_user_id),
                        json={"invite_token": raw_token},
                    )
                    revoke_accepted = await client.delete(
                        f"/api/v1/communities/{slug}/invites/{first_invite_public_id}",
                        headers=headers(owner_id),
                    )

                    revoke_invite_response = await client.post(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )
                    revoke_invite_public_id = UUID(
                        revoke_invite_response.json()["invite_public_id"]
                    )
                    revoke_active = await client.delete(
                        f"/api/v1/communities/{slug}/invites/{revoke_invite_public_id}",
                        headers=headers(owner_id),
                    )
                    repeat_revoke = await client.delete(
                        f"/api/v1/communities/{slug}/invites/{revoke_invite_public_id}",
                        headers=headers(owner_id),
                    )
                    accept_revoked = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(first_member_id),
                        json={"invite_token": revoke_invite_response.json()["invite_token"]},
                    )

                    expire_invite_response = await client.post(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )
                    expire_invite_public_id = UUID(
                        expire_invite_response.json()["invite_public_id"]
                    )
                    async with session_factory() as session:
                        expired_created_at = datetime.now(UTC) - timedelta(days=2)
                        expired_at = datetime.now(UTC) - timedelta(minutes=1)
                        await session.execute(
                            update(CommunityInvite)
                            .where(CommunityInvite.public_id == expire_invite_public_id)
                            .values(
                                created_at=expired_created_at,
                                expires_at=expired_at,
                            )
                        )
                        await session.commit()
                    accept_expired = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(first_member_id),
                        json={"invite_token": expire_invite_response.json()["invite_token"]},
                    )

                    short_community_expiry = datetime.now(UTC) + timedelta(days=2)
                    short_community_response = await client.post(
                        "/api/v1/communities",
                        headers=headers(owner_id),
                        json={
                            "name": f"Short-lived {uuid4().hex[:8]}",
                            "topic": "Testing",
                            "access_type": "invite_only",
                            "expires_at": short_community_expiry.isoformat(),
                        },
                    )
                    short_community = short_community_response.json()
                    short_community_public_id = UUID(short_community["public_id"])
                    community_public_ids.append(short_community_public_id)
                    short_invite_response = await client.post(
                        f"/api/v1/communities/{short_community['slug']}/invites",
                        headers=headers(owner_id),
                    )
                    short_invite = short_invite_response.json()
                    short_invite_expires_at = datetime.fromisoformat(
                        short_invite["expires_at"].replace("Z", "+00:00")
                    )
                    async with session_factory() as session:
                        await session.execute(
                            update(Community)
                            .where(Community.public_id == short_community_public_id)
                            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
                        )
                        await session.commit()
                    accept_for_expired_community = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(first_member_id),
                        json={"invite_token": short_invite["invite_token"]},
                    )

                    race_invite_response = await client.post(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )
                    race_token = race_invite_response.json()["invite_token"]
                    concurrent_accepts = await asyncio.gather(
                        client.post(
                            "/api/v1/communities/invites/accept",
                            headers=headers(race_user_a),
                            json={"invite_token": race_token},
                        ),
                        client.post(
                            "/api/v1/communities/invites/accept",
                            headers=headers(race_user_b),
                            json={"invite_token": race_token},
                        ),
                    )

                    additional_invites = [
                        await client.post(
                            f"/api/v1/communities/{slug}/invites",
                            headers=headers(owner_id),
                        )
                        for _ in range(4)
                    ]
                    rate_limited_create = await client.post(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )

                    invalid_accepts = [
                        await client.post(
                            "/api/v1/communities/invites/accept",
                            headers=headers(brute_user_id),
                            json={"invite_token": secrets.token_urlsafe(32)},
                        )
                        for _ in range(COMMUNITY_INVITE_ACCEPT_LIMIT)
                    ]
                    rate_limited_accept = await client.post(
                        "/api/v1/communities/invites/accept",
                        headers=headers(brute_user_id),
                        json={"invite_token": secrets.token_urlsafe(32)},
                    )

                    final_invite_list = await client.get(
                        f"/api/v1/communities/{slug}/invites",
                        headers=headers(owner_id),
                    )

            assert non_owner_create.status_code == 403
            assert non_owner_list.status_code == 403
            assert open_invite.status_code == 409
            assert open_invite.json() == {
                "detail": "Invites can only be created for invite-only communities"
            }
            assert first_accept.status_code == 201
            assert first_accept.json()["role"] == "member"
            assert first_accept.json()["community_slug"] == slug
            assert "community_id" not in first_accept.json()
            assert "id" not in first_accept.json()
            assert same_user_retry.status_code == 200
            assert replay_by_other_user.status_code == 409
            assert replay_by_other_user.json() == {
                "detail": "This invite has already been used by another account."
            }
            assert revoke_accepted.status_code == 409
            assert revoke_active.status_code == repeat_revoke.status_code == 204
            assert accept_revoked.status_code == 404
            assert accept_expired.status_code == 404
            assert short_community_response.status_code == 201
            assert short_invite_response.status_code == 201
            assert short_invite_expires_at <= short_community_expiry
            assert accept_for_expired_community.status_code == 404
            assert sorted(response.status_code for response in concurrent_accepts) == [201, 409]
            assert all(response.status_code == 201 for response in additional_invites)
            assert rate_limited_create.status_code == 429
            assert "Retry-After" in rate_limited_create.headers
            assert all(response.status_code == 404 for response in invalid_accepts)
            assert rate_limited_accept.status_code == 429
            assert "Retry-After" in rate_limited_accept.headers
            statuses = {item["status"] for item in final_invite_list.json()["items"]}
            assert {"accepted", "revoked", "expired", "active"} <= statuses

            async with session_factory() as session:
                private_community = await session.scalar(
                    select(Community).where(Community.public_id == community_public_id)
                )
                assert private_community is not None
                memberships = await session.scalars(
                    select(CommunityMembership).where(
                        CommunityMembership.community_id == private_community.id
                    )
                )
                member_ids = {membership.user_id for membership in memberships.all()}
                assert owner_id in member_ids
                assert first_member_id in member_ids
                assert replay_user_id not in member_ids
                assert (race_user_a in member_ids) != (race_user_b in member_ids)
        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(Community).where(Community.public_id.in_(community_public_ids))
                )
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                await session.execute(
                    delete(AuthRateLimitBucket).where(
                        AuthRateLimitBucket.bucket_key_hash.in_(rate_limit_hashes)
                    )
                )
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
