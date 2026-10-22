import asyncio
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.features.auth.dependencies import require_authenticated_principal
from app.features.auth.models import AuthRateLimitBucket
from app.features.auth.security import create_one_time_token
from app.features.communities.models import (
    Community,
    CommunityInvite,
    CommunityLifecycleEvent,
    CommunityMembership,
)
from app.features.users.models import User
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_archive_is_reversible_hides_community_and_revokes_unused_invites() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id = uuid4()
        member_id = uuid4()
        invitee_id = uuid4()
        outsider_id = uuid4()
        owner_public_id = uuid4()
        member_public_id = uuid4()
        invitee_public_id = uuid4()
        outsider_public_id = uuid4()
        open_community_id = uuid4()
        private_community_id = uuid4()
        expired_community_id = uuid4()
        open_community_public_id = uuid4()
        private_community_public_id = uuid4()
        expired_community_public_id = uuid4()
        user_public_ids = {
            owner_id: owner_public_id,
            member_id: member_public_id,
            invitee_id: invitee_public_id,
            outsider_id: outsider_public_id,
        }
        user_ids = list(user_public_ids)
        community_public_ids = [
            open_community_public_id,
            private_community_public_id,
            expired_community_public_id,
        ]
        suffix = uuid4().hex
        open_slug = f"archive-open-{suffix}"
        private_slug = f"archive-private-{suffix}"
        expired_slug = f"archive-expired-{suffix}"
        now = datetime.now(UTC)
        rate_limit_secret = uuid4().hex
        active_token, active_token_hash = create_one_time_token()
        expired_token, expired_token_hash = create_one_time_token()
        consumed_token, consumed_token_hash = create_one_time_token()
        active_invite_public_id = uuid4()
        expired_invite_public_id = uuid4()
        consumed_invite_public_id = uuid4()
        rate_limit_bucket_keys = {
            hmac.new(
                rate_limit_secret.encode(),
                f"{purpose}\0{identity}".encode(),
                hashlib.sha256,
            ).hexdigest()
            for purpose, identity in (
                ("community_invite_create", str(owner_id)),
                ("community_invite_accept", str(invitee_id)),
            )
        }
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        User(
                            id=user_id,
                            public_id=public_id,
                            display_name=f"Archive test {index}",
                            email=f"{user_id.hex}@example.test",
                        )
                        for index, (user_id, public_id) in enumerate(user_public_ids.items())
                    ]
                )
                await session.flush()
                session.add_all(
                    [
                        Community(
                            id=open_community_id,
                            public_id=open_community_public_id,
                            owner_id=owner_id,
                            name=f"Archive open {suffix}",
                            slug=open_slug,
                            topic=f"Archive open topic {suffix}",
                            description="Reversible open-community archive test.",
                            access_type="open",
                        ),
                        Community(
                            id=private_community_id,
                            public_id=private_community_public_id,
                            owner_id=owner_id,
                            name=f"Archive private {suffix}",
                            slug=private_slug,
                            topic=f"Archive private topic {suffix}",
                            description="Invite links are revoked while archived.",
                            access_type="invite_only",
                        ),
                        Community(
                            id=expired_community_id,
                            public_id=expired_community_public_id,
                            owner_id=owner_id,
                            name=f"Archive expired {suffix}",
                            slug=expired_slug,
                            topic=f"Archive expired topic {suffix}",
                            description="Expired community stays expired after restore.",
                            access_type="open",
                            expires_at=now - timedelta(days=1),
                        ),
                        CommunityMembership(
                            community_id=open_community_id,
                            user_id=owner_id,
                            role="owner",
                        ),
                        CommunityMembership(
                            community_id=open_community_id,
                            user_id=member_id,
                            role="member",
                        ),
                        CommunityMembership(
                            community_id=private_community_id,
                            user_id=owner_id,
                            role="owner",
                        ),
                        CommunityMembership(
                            community_id=private_community_id,
                            user_id=member_id,
                            role="member",
                        ),
                        CommunityMembership(
                            community_id=expired_community_id,
                            user_id=owner_id,
                            role="owner",
                        ),
                        CommunityInvite(
                            id=uuid4(),
                            public_id=active_invite_public_id,
                            community_id=private_community_id,
                            created_by_user_id=owner_id,
                            token_hash=active_token_hash,
                            created_at=now,
                            expires_at=now + timedelta(days=2),
                        ),
                        CommunityInvite(
                            id=uuid4(),
                            public_id=expired_invite_public_id,
                            community_id=private_community_id,
                            created_by_user_id=owner_id,
                            token_hash=expired_token_hash,
                            created_at=now - timedelta(days=2),
                            expires_at=now - timedelta(days=1),
                        ),
                        CommunityInvite(
                            id=uuid4(),
                            public_id=consumed_invite_public_id,
                            community_id=private_community_id,
                            created_by_user_id=owner_id,
                            accepted_by_user_id=member_id,
                            token_hash=consumed_token_hash,
                            created_at=now,
                            expires_at=now + timedelta(days=2),
                            consumed_at=now - timedelta(minutes=1),
                        ),
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
            active_user_id = {"value": owner_id}
            app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
                user=SimpleNamespace(
                    id=active_user_id["value"],
                    public_id=user_public_ids[active_user_id["value"]],
                )
            )
            open_detail_path = f"/api/v1/communities/{open_slug}"
            archive_open_path = f"/api/v1/communities/{open_slug}/archive"
            restore_open_path = f"/api/v1/communities/{open_slug}/restore"
            archive_private_path = f"/api/v1/communities/{private_slug}/archive"
            restore_private_path = f"/api/v1/communities/{private_slug}/restore"

            async with app.router.lifespan_context(app):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    topic_before = await client.get("/api/v1/topics")
                    open_detail_before = await client.get(open_detail_path)
                    archive_open = await client.put(archive_open_path)
                    repeat_archive_open = await client.put(archive_open_path)
                    discovery_after_archive = await client.get(
                        f"/api/v1/communities?topic=Archive%20open%20topic%20{suffix}"
                    )
                    topics_after_archive = await client.get("/api/v1/topics")
                    detail_after_archive = await client.get(open_detail_path)
                    manager_view_after_archive = await client.get(
                        f"/api/v1/communities/{open_slug}/manage"
                    )
                    owner_communities_after_archive = await client.get("/api/v1/communities/mine")
                    owner_memberships_after_archive = await client.get(
                        "/api/v1/communities/memberships/me"
                    )

                    active_user_id["value"] = member_id
                    member_memberships_after_archive = await client.get(
                        "/api/v1/communities/memberships/me"
                    )
                    member_archive_attempt = await client.put(archive_open_path)
                    archived_join_attempt = await client.post(
                        f"/api/v1/communities/{open_slug}/join"
                    )
                    member_leave_archived = await client.delete(
                        f"/api/v1/communities/{open_slug}/leave"
                    )

                    active_user_id["value"] = owner_id
                    owner_leave_archived = await client.delete(
                        f"/api/v1/communities/{open_slug}/leave"
                    )
                    restore_open = await client.put(restore_open_path)
                    repeat_restore_open = await client.put(restore_open_path)
                    discovery_after_restore = await client.get(
                        f"/api/v1/communities?topic=Archive%20open%20topic%20{suffix}"
                    )

                    archive_private = await client.put(archive_private_path)
                    create_invite_while_archived = await client.post(
                        f"/api/v1/communities/{private_slug}/invites"
                    )
                    archived_invites = await client.get(
                        f"/api/v1/communities/{private_slug}/invites"
                    )
                    accept_while_archived = await client.post(
                        "/api/v1/communities/invites/accept",
                        json={"invite_token": active_token},
                    )
                    restore_private = await client.put(restore_private_path)
                    accept_old_revoked_invite = await client.post(
                        "/api/v1/communities/invites/accept",
                        json={"invite_token": active_token},
                    )
                    fresh_invite = await client.post(f"/api/v1/communities/{private_slug}/invites")

                    active_user_id["value"] = invitee_id
                    accept_fresh_invite = await client.post(
                        "/api/v1/communities/invites/accept",
                        json={"invite_token": fresh_invite.json()["invite_token"]},
                    )

                    active_user_id["value"] = outsider_id
                    outsider_restore_attempt = await client.put(restore_open_path)
                    active_user_id["value"] = owner_id
                    archive_expired = await client.put(
                        f"/api/v1/communities/{expired_slug}/archive"
                    )
                    restore_expired = await client.put(
                        f"/api/v1/communities/{expired_slug}/restore"
                    )
                    expired_public_detail = await client.get(f"/api/v1/communities/{expired_slug}")
                    unknown_archive = await client.put(
                        f"/api/v1/communities/missing-{suffix}/archive"
                    )

            assert topic_before.status_code == 200
            assert f"Archive open topic {suffix}" in topic_before.json()["items"]
            assert open_detail_before.status_code == 200
            assert archive_open.status_code == 200
            assert archive_open.json()["status"] == "archived"
            assert archive_open.json()["changed"] is True
            assert archive_open.json()["revoked_invite_count"] == 0
            assert repeat_archive_open.status_code == 200
            assert repeat_archive_open.json()["changed"] is False
            assert discovery_after_archive.status_code == 200
            assert discovery_after_archive.json()["total"] == 0
            assert f"Archive open topic {suffix}" not in topics_after_archive.json()["items"]
            assert detail_after_archive.status_code == 404
            assert manager_view_after_archive.status_code == 200
            assert manager_view_after_archive.json()["archived_at"] is not None
            assert owner_communities_after_archive.status_code == 200
            assert (
                next(
                    item
                    for item in owner_communities_after_archive.json()["items"]
                    if item["slug"] == open_slug
                )["archived_at"]
                is not None
            )
            assert owner_memberships_after_archive.status_code == 200
            assert {
                item["community"]["slug"]: item["community_status"]
                for item in owner_memberships_after_archive.json()["items"]
            }[open_slug] == "archived"
            assert member_memberships_after_archive.status_code == 200
            assert {
                item["community"]["slug"]: item["community_status"]
                for item in member_memberships_after_archive.json()["items"]
            }[open_slug] == "archived"
            assert member_archive_attempt.status_code == 403
            assert archived_join_attempt.status_code == 404
            assert owner_leave_archived is not None and owner_leave_archived.status_code == 409
            assert restore_open.status_code == 200
            assert restore_open.json()["status"] == "active"
            assert restore_open.json()["changed"] is True
            assert repeat_restore_open.status_code == 200
            assert repeat_restore_open.json()["changed"] is False
            assert discovery_after_restore.status_code == 200
            assert discovery_after_restore.json()["total"] == 1

            assert archive_private.status_code == 200
            assert archive_private.json()["revoked_invite_count"] == 1
            assert create_invite_while_archived.status_code == 409
            assert archived_invites.status_code == 200
            invite_statuses = {
                str(item["invite_public_id"]): item["status"]
                for item in archived_invites.json()["items"]
            }
            assert invite_statuses[str(active_invite_public_id)] == "revoked"
            assert invite_statuses[str(expired_invite_public_id)] == "expired"
            assert invite_statuses[str(consumed_invite_public_id)] == "accepted"
            assert accept_while_archived.status_code == 404
            assert restore_private.status_code == 200
            assert restore_private.json()["status"] == "active"
            assert accept_old_revoked_invite.status_code == 404
            assert fresh_invite.status_code == 201
            assert accept_fresh_invite.status_code == 201
            assert accept_fresh_invite.json()["community_slug"] == private_slug
            assert member_leave_archived is not None and member_leave_archived.status_code == 204
            assert outsider_restore_attempt.status_code == 403
            assert archive_expired.status_code == restore_expired.status_code == 200
            assert archive_expired.json()["status"] == "archived"
            assert restore_expired.json()["status"] == "expired"
            assert expired_public_detail.status_code == 404
            assert unknown_archive.status_code == 404

            async with session_factory() as session:
                events_result = await session.scalars(
                    select(CommunityLifecycleEvent).where(
                        CommunityLifecycleEvent.community_public_id.in_(community_public_ids)
                    )
                )
                events = list(events_result.all())
                assert len(events) == 6
                assert {
                    (event.community_public_id, event.event_type, event.actor_public_id)
                    for event in events
                } == {
                    (open_community_public_id, "archived", owner_public_id),
                    (open_community_public_id, "restored", owner_public_id),
                    (private_community_public_id, "archived", owner_public_id),
                    (private_community_public_id, "restored", owner_public_id),
                    (expired_community_public_id, "archived", owner_public_id),
                    (expired_community_public_id, "restored", owner_public_id),
                }
        finally:
            async with session_factory() as session:
                await session.execute(
                    delete(CommunityLifecycleEvent).where(
                        CommunityLifecycleEvent.community_public_id.in_(community_public_ids)
                    )
                )
                await session.execute(
                    delete(AuthRateLimitBucket).where(
                        AuthRateLimitBucket.bucket_key_hash.in_(rate_limit_bucket_keys)
                    )
                )
                await session.execute(
                    delete(Community).where(Community.public_id.in_(community_public_ids))
                )
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
