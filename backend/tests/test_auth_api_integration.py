import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete, select

from app.core.config import Settings
from app.features.auth.maintenance import delete_expired_rate_limit_buckets
from app.features.auth.models import (
    AuthActionToken,
    AuthRateLimitBucket,
    AuthRefreshToken,
    AuthSession,
)
from app.features.auth.security import hash_one_time_token
from app.features.users.models import User
from app.integrations.auth_email import AuthEmailSender, EmailDeliveryError
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


class FakeAuthEmailSender:
    def __init__(self, *, fail_delivery: bool = False) -> None:
        self.verification_tokens: list[tuple[str, str]] = []
        self.password_reset_tokens: list[tuple[str, str]] = []
        self.fail_delivery = fail_delivery

    async def send_verification(self, *, recipient: str, token: str) -> None:
        if self.fail_delivery:
            raise EmailDeliveryError("test transport failure")
        self.verification_tokens.append((recipient, token))

    async def send_password_reset(self, *, recipient: str, token: str) -> None:
        if self.fail_delivery:
            raise EmailDeliveryError("test transport failure")
        self.password_reset_tokens.append((recipient, token))


@asynccontextmanager
async def api_client(
    sender: AuthEmailSender,
    email: str,
    settings: Settings | None = None,
) -> AsyncIterator[tuple[AsyncClient, FastAPI]]:
    assert TEST_DATABASE_URL is not None
    app_settings = settings or Settings(
        app_env="test",
        database_url=SecretStr(TEST_DATABASE_URL),
        auth_rate_limit_secret=SecretStr(uuid4().hex),
    )
    app = create_app(
        app_settings,
        auth_email_sender=sender,
    )
    async with app.router.lifespan_context(app):
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                yield client, app
        finally:
            session_factory = app.state.database_session_factory
            if session_factory is not None:
                async with session_factory() as session:
                    await session.execute(delete(User).where(User.email == email))
                    await session.commit()


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_email_auth_verification_sessions_refresh_and_recovery() -> None:
    assert TEST_DATABASE_URL is not None
    email = f"auth-{uuid4().hex}@example.com"
    original_password = "original secure passphrase 2026!"
    new_password = "replacement secure passphrase 2026!"
    mailer = FakeAuthEmailSender()

    async def run(client: AsyncClient, app: FastAPI) -> None:
        register_payload = {
            "email": email,
            "password": original_password,
            "display_name": "Test account",
        }
        registered = await client.post("/api/v1/auth/register", json=register_payload)
        assert registered.status_code == 202
        assert registered.json() == {
            "message": (
                "If the address is eligible, instructions will be sent to verify the account."
            )
        }
        assert len(mailer.verification_tokens) == 1
        first_verify_token = mailer.verification_tokens[-1][1]

        unverified_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": original_password},
        )
        assert unverified_login.status_code == 401

        resent_verification = await client.post(
            "/api/v1/auth/verification/resend",
            json={"email": email},
        )
        assert resent_verification.status_code == 202
        assert resent_verification.json() == registered.json()
        assert len(mailer.verification_tokens) == 2
        verify_token = mailer.verification_tokens[-1][1]
        superseded_verification = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": first_verify_token},
        )
        assert superseded_verification.status_code == 400

        verified = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": verify_token},
        )
        assert verified.status_code == 200
        replayed_verification = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": verify_token},
        )
        assert replayed_verification.status_code == 400
        duplicate_verified_registration = await client.post(
            "/api/v1/auth/register",
            json={
                **register_payload,
                "password": "different account password 2026!",
                "display_name": "Different name",
            },
        )
        assert duplicate_verified_registration.status_code == registered.status_code
        assert duplicate_verified_registration.json() == registered.json()
        assert len(mailer.verification_tokens) == 2

        wrong_password = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "not the account password"},
        )
        assert wrong_password.status_code == 401
        assert wrong_password.json() == {"detail": "Invalid email or password"}

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email.upper(), "password": original_password},
        )
        assert login.status_code == 200
        first_session = login.json()
        assert first_session["token_type"] == "bearer"
        assert first_session["expires_in"] == 900
        assert first_session["access_token"]
        assert first_session["refresh_token"]

        profile = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {first_session['access_token']}"},
        )
        assert profile.status_code == 200
        assert profile.json()["public_id"]
        assert "id" not in profile.json()
        assert profile.json()["email"] == email
        assert profile.json()["display_name"] == "Test account"
        assert "password_hash" not in profile.json()
        session_factory = app.state.database_session_factory
        assert session_factory is not None
        async with session_factory() as database_session:
            account = await database_session.scalar(select(User).where(User.email == email))
            assert account is not None
            assert account.public_id != account.id
            assert profile.json()["public_id"] == str(account.public_id)

        refreshed = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_session["refresh_token"]},
        )
        assert refreshed.status_code == 200
        rotated_session = refreshed.json()
        assert rotated_session["access_token"] != first_session["access_token"]
        assert rotated_session["refresh_token"] != first_session["refresh_token"]
        old_access = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {first_session['access_token']}"},
        )
        assert old_access.status_code == 401

        refresh_replay = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_session["refresh_token"]},
        )
        assert refresh_replay.status_code == 401
        replay_revoked_access = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {rotated_session['access_token']}"},
        )
        assert replay_revoked_access.status_code == 401

        second_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": original_password},
        )
        assert second_login.status_code == 200
        recovery_message = await client.post(
            "/api/v1/auth/password/forgot",
            json={"email": f"missing-{uuid4().hex}@example.com"},
        )
        assert recovery_message.status_code == 202
        assert recovery_message.json() == {
            "message": "If an eligible account exists, password reset instructions will be sent."
        }
        assert not mailer.password_reset_tokens

        recovery = await client.post(
            "/api/v1/auth/password/forgot",
            json={"email": email},
        )
        assert recovery.status_code == 202
        assert recovery.json() == recovery_message.json()
        assert len(mailer.password_reset_tokens) == 1
        reset_token = mailer.password_reset_tokens[-1][1]

        invalid_reset = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": "x" * 43, "new_password": new_password},
        )
        assert invalid_reset.status_code == 400

        reset = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": reset_token, "new_password": new_password},
        )
        assert reset.status_code == 200
        replayed_reset = await client.post(
            "/api/v1/auth/password/reset",
            json={"token": reset_token, "new_password": original_password},
        )
        assert replayed_reset.status_code == 400
        revoked_after_reset = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {second_login.json()['access_token']}"},
        )
        assert revoked_after_reset.status_code == 401

        old_password_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": original_password},
        )
        assert old_password_login.status_code == 401
        new_password_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_password},
        )
        assert new_password_login.status_code == 200

        signed_out = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_password_login.json()['access_token']}"},
        )
        assert signed_out.status_code == 204
        signed_out_profile = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_password_login.json()['access_token']}"},
        )
        assert signed_out_profile.status_code == 401

    async def run_with_client() -> None:
        async with api_client(mailer, email) as (client, app):
            await run(client, app)

    asyncio.run(run_with_client())


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_registration_validation_duplicate_and_delivery_failure() -> None:
    assert TEST_DATABASE_URL is not None
    email = f"validation-{uuid4().hex}@example.com"
    mailer = FakeAuthEmailSender(fail_delivery=True)

    async def run() -> None:
        async with api_client(mailer, email) as (client, _app):
            invalid_email = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "not-an-email",
                    "password": "long enough secure passphrase",
                    "display_name": "Test",
                },
            )
            assert invalid_email.status_code == 422

            too_short_password = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "short",
                    "display_name": "Test",
                },
            )
            assert too_short_password.status_code == 422

            blank_name = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "long enough secure passphrase",
                    "display_name": "   ",
                },
            )
            assert blank_name.status_code == 422

            delivered_unavailable = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "long enough secure passphrase",
                    "display_name": "Test",
                },
            )
            assert delivered_unavailable.status_code == 202
            assert delivered_unavailable.json() == {
                "message": (
                    "If the address is eligible, instructions will be sent to verify the account."
                )
            }

            repeated = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "a different secure passphrase",
                    "display_name": "Different name",
                },
            )
            assert repeated.status_code == delivered_unavailable.status_code
            assert repeated.json() == delivered_unavailable.json()

            unverified_login = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "long enough secure passphrase"},
            )
            assert unverified_login.status_code == 401

    asyncio.run(run())


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_login_rate_limit_is_enforced_and_returns_retry_after() -> None:
    assert TEST_DATABASE_URL is not None
    email = f"rate-limit-{uuid4().hex}@example.com"
    settings = Settings(
        app_env="test",
        database_url=SecretStr(TEST_DATABASE_URL),
        auth_rate_limit_secret=SecretStr(uuid4().hex),
        auth_login_attempt_limit=2,
        auth_rate_limit_window_seconds=1,
    )

    async def run() -> None:
        async with api_client(FakeAuthEmailSender(), email, settings) as (client, _app):
            payload = {"email": email, "password": "incorrect but long password"}
            first = await client.post("/api/v1/auth/login", json=payload)
            second = await client.post("/api/v1/auth/login", json=payload)
            blocked = await client.post("/api/v1/auth/login", json=payload)

            assert first.status_code == 401
            assert second.status_code == 401
            assert blocked.status_code == 429
            assert blocked.headers["retry-after"].isdigit()
            assert blocked.json() == {"detail": "Too many attempts. Try again later."}
            await asyncio.sleep(1.1)
            after_window = await client.post("/api/v1/auth/login", json=payload)
            assert after_window.status_code == 401

    asyncio.run(run())


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_expired_rate_limit_bucket_cleanup_retains_current_window() -> None:
    assert TEST_DATABASE_URL is not None
    email = f"cleanup-{uuid4().hex}@example.com"
    expired_hash = hash_one_time_token(uuid4().hex)
    current_hash = hash_one_time_token(uuid4().hex)
    now = datetime.now(UTC)

    async def run() -> None:
        async with api_client(FakeAuthEmailSender(), email) as (_client, app):
            session_factory = app.state.database_session_factory
            assert session_factory is not None
            async with session_factory() as session:
                session.add_all(
                    [
                        AuthRateLimitBucket(
                            bucket_key_hash=expired_hash,
                            window_started_at=now - timedelta(days=2),
                            attempt_count=3,
                        ),
                        AuthRateLimitBucket(
                            bucket_key_hash=current_hash,
                            window_started_at=now,
                            attempt_count=1,
                        ),
                    ]
                )
                await session.commit()

                removed = await delete_expired_rate_limit_buckets(
                    session,
                    older_than=now - timedelta(days=1),
                )

                assert removed == 1
                assert (
                    await session.scalar(
                        select(AuthRateLimitBucket.bucket_key_hash).where(
                            AuthRateLimitBucket.bucket_key_hash == expired_hash
                        )
                    )
                ) is None
                assert (
                    await session.scalar(
                        select(AuthRateLimitBucket.bucket_key_hash).where(
                            AuthRateLimitBucket.bucket_key_hash == current_hash
                        )
                    )
                ) is not None
                await session.execute(
                    delete(AuthRateLimitBucket).where(
                        AuthRateLimitBucket.bucket_key_hash == current_hash
                    )
                )
                await session.commit()

    asyncio.run(run())


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_private_profile_update_validates_and_persists_display_name_and_interests() -> None:
    assert TEST_DATABASE_URL is not None
    email = f"profile-{uuid4().hex}@example.com"
    password = "Profile-test-passphrase-2026!"
    sender = FakeAuthEmailSender()

    async def run() -> None:
        async with api_client(sender, email) as (client, _app):
            unauthorized = await client.get("/api/v1/profile/me")
            assert unauthorized.status_code == 401

            registered = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "display_name": "Profile User",
                },
            )
            assert registered.status_code == 202
            await client.post(
                "/api/v1/auth/verify-email",
                json={"token": sender.verification_tokens[-1][1]},
            )
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            auth_headers = {
                "Authorization": f"Bearer {login.json()['access_token']}",
            }

            initial = await client.get("/api/v1/profile/me", headers=auth_headers)
            assert initial.status_code == 200
            assert initial.json()["public_id"]
            assert "id" not in initial.json()
            assert initial.json()["display_name"] == "Profile User"
            assert initial.json()["interests"] == []
            assert "email" not in initial.json()
            assert "password_hash" not in initial.json()

            updated = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={
                    "display_name": "  Updated Profile  ",
                    "interests": ["Exam prep", "Technology"],
                },
            )
            assert updated.status_code == 200
            assert updated.json()["display_name"] == "Updated Profile"
            assert updated.json()["interests"] == ["Exam prep", "Technology"]

            added = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"interests": ["Native"]},
            )
            assert added.status_code == 200
            assert added.json()["interests"] == ["Exam prep", "Technology", "Native"]

            duplicate_add = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"interests": ["native"]},
            )
            assert duplicate_add.status_code == 200
            assert duplicate_add.json()["interests"] == ["Exam prep", "Technology", "Native"]

            removed = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"remove_interests": ["exam prep"]},
            )
            assert removed.status_code == 200
            assert removed.json()["interests"] == ["Technology", "Native"]

            invalid_patches = [
                {},
                {"display_name": None},
                {"interests": None},
                {"remove_interests": None},
                {"display_name": "   "},
                {"interests": ["Technology", " technology "]},
                {"interests": [" "]},
                {"interests": ["Native"], "remove_interests": ["native"]},
                {"interests": ["x" * 81]},
                {"interests": [f"Topic {index}" for index in range(21)]},
                {"unexpected_field": "must be rejected"},
            ]
            for payload in invalid_patches:
                invalid = await client.patch(
                    "/api/v1/profile/me",
                    headers=auth_headers,
                    json=payload,
                )
                assert invalid.status_code == 422, payload

            unchanged = await client.get("/api/v1/profile/me", headers=auth_headers)
            assert unchanged.json()["display_name"] == "Updated Profile"
            assert unchanged.json()["interests"] == ["Technology", "Native"]

            over_limit = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"interests": [f"Additional {index}" for index in range(19)]},
            )
            assert over_limit.status_code == 422
            after_over_limit = await client.get("/api/v1/profile/me", headers=auth_headers)
            assert after_over_limit.json()["interests"] == ["Technology", "Native"]

            empty_addition = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"interests": []},
            )
            assert empty_addition.status_code == 200
            assert empty_addition.json()["interests"] == ["Technology", "Native"]

            cleared = await client.patch(
                "/api/v1/profile/me",
                headers=auth_headers,
                json={"remove_interests": ["Technology", "Native"]},
            )
            assert cleared.status_code == 200
            assert cleared.json()["interests"] == []

    asyncio.run(run())


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_expired_verification_recovery_and_session_tokens_are_rejected() -> None:
    assert TEST_DATABASE_URL is not None
    email = f"expired-{uuid4().hex}@example.com"
    password = "Expired-token-test-passphrase!"
    mailer = FakeAuthEmailSender()

    async def run() -> None:
        async with api_client(mailer, email) as (client, app):
            registration = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "display_name": "Expiry test",
                },
            )
            assert registration.status_code == 202
            verification_token = mailer.verification_tokens[-1][1]
            session_factory = app.state.database_session_factory
            assert session_factory is not None

            async with session_factory() as session:
                verification_row = await session.scalar(
                    select(AuthActionToken).where(
                        AuthActionToken.token_hash == hash_one_time_token(verification_token)
                    )
                )
                user = await session.scalar(select(User).where(User.email == email))
                assert verification_row is not None
                assert user is not None
                verification_row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
                # Mark verified independently so the password-reset expiration can be tested too.
                user.email_verified_at = datetime.now(UTC)
                await session.commit()

            expired_verification = await client.post(
                "/api/v1/auth/verify-email",
                json={"token": verification_token},
            )
            assert expired_verification.status_code == 400

            await client.post("/api/v1/auth/password/forgot", json={"email": email})
            reset_token = mailer.password_reset_tokens[-1][1]
            async with session_factory() as session:
                reset_row = await session.scalar(
                    select(AuthActionToken).where(
                        AuthActionToken.token_hash == hash_one_time_token(reset_token)
                    )
                )
                assert reset_row is not None
                reset_row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
                await session.commit()

            expired_reset = await client.post(
                "/api/v1/auth/password/reset",
                json={"token": reset_token, "new_password": "Another-long-passphrase!"},
            )
            assert expired_reset.status_code == 400

            login = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            assert login.status_code == 200
            async with session_factory() as session:
                auth_session = await session.scalar(
                    select(AuthSession).where(
                        AuthSession.access_token_hash
                        == hash_one_time_token(login.json()["access_token"])
                    )
                )
                refresh_row = await session.scalar(
                    select(AuthRefreshToken).where(
                        AuthRefreshToken.token_hash
                        == hash_one_time_token(login.json()["refresh_token"])
                    )
                )
                assert auth_session is not None
                assert refresh_row is not None
                auth_session.access_expires_at = datetime.now(UTC) - timedelta(seconds=1)
                refresh_row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
                await session.commit()

            expired_access = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            )
            expired_refresh = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": login.json()["refresh_token"]},
            )
            assert expired_access.status_code == 401
            assert expired_refresh.status_code == 401

    asyncio.run(run())
