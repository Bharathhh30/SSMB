import hashlib
import hmac
import logging
import math
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.features.auth.models import (
    AuthActionToken,
    AuthRateLimitBucket,
    AuthRefreshToken,
    AuthSession,
)
from app.features.auth.schemas import TokenResponse
from app.features.auth.security import (
    create_one_time_token,
    hash_one_time_token,
    hash_password,
    normalize_email,
    verify_password,
)
from app.features.users.models import User
from app.integrations.auth_email import AuthEmailSender, EmailDeliveryError

logger = logging.getLogger(__name__)

# Keep unknown-email login attempts close to the same password-hashing cost as real users.
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))

REGISTRATION_MESSAGE = (
    "If the address is eligible, instructions will be sent to verify the account."
)
RECOVERY_MESSAGE = "If an eligible account exists, password reset instructions will be sent."


class RateLimitSecretNotConfigured(RuntimeError):
    """Raised when a deployed environment has no rate-limit HMAC key."""


async def consume_rate_limit(
    session: AsyncSession,
    settings: Settings,
    *,
    purpose: str,
    identity: str,
    maximum_attempts: int,
) -> int:
    if settings.auth_rate_limit_secret is None:
        if settings.app_env in {"staging", "production"}:
            raise RateLimitSecretNotConfigured
        secret = b"local-development-only-rate-limit-key"
    else:
        secret = settings.auth_rate_limit_secret.get_secret_value().encode("utf-8")

    bucket_key_hash = hmac.new(
        secret,
        f"{purpose}\0{identity}".encode(),
        hashlib.sha256,
    ).hexdigest()
    now = datetime.now(UTC)
    window = timedelta(seconds=settings.auth_rate_limit_window_seconds)
    bucket_table = AuthRateLimitBucket.__table__
    window_expired = bucket_table.c.window_started_at <= now - window

    statement = (
        pg_insert(AuthRateLimitBucket)
        .values(
            bucket_key_hash=bucket_key_hash,
            window_started_at=now,
            attempt_count=1,
        )
        .on_conflict_do_update(
            index_elements=[bucket_table.c.bucket_key_hash],
            set_={
                "window_started_at": case(
                    (window_expired, now),
                    else_=bucket_table.c.window_started_at,
                ),
                "attempt_count": case(
                    (window_expired, 1),
                    else_=bucket_table.c.attempt_count + 1,
                ),
            },
        )
        .returning(
            bucket_table.c.window_started_at,
            bucket_table.c.attempt_count,
        )
    )
    window_started_at, attempt_count = (await session.execute(statement)).one()
    await session.commit()

    if attempt_count <= maximum_attempts:
        return 0
    retry_at = window_started_at + window
    return max(1, math.ceil((retry_at - now).total_seconds()))


async def register(
    session: AsyncSession,
    sender: AuthEmailSender,
    settings: Settings,
    *,
    email: str,
    password: str,
    display_name: str,
) -> None:
    normalized_email = normalize_email(email)
    password_hash = hash_password(password)
    user = await session.scalar(select(User).where(User.email == normalized_email))

    if user is not None and user.email_verified_at is not None:
        await session.rollback()
        return

    token: str | None = None
    try:
        if user is None:
            user = User(
                email=normalized_email,
                password_hash=password_hash,
                display_name=display_name.strip(),
            )
            session.add(user)
            await session.flush()

        token = await _create_action_token(
            session,
            user_id=user.id,
            purpose="email_verification",
            expires_at=datetime.now(UTC) + timedelta(hours=settings.auth_verification_token_hours),
        )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        # A concurrent registration may have won the normalized-email unique constraint.
        return

    if token is not None:
        await _deliver_verification(sender, normalized_email, token)


async def resend_verification(
    session: AsyncSession,
    sender: AuthEmailSender,
    settings: Settings,
    *,
    email: str,
) -> None:
    normalized_email = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized_email))
    if user is None or user.email_verified_at is not None:
        await session.rollback()
        return

    token = await _create_action_token(
        session,
        user_id=user.id,
        purpose="email_verification",
        expires_at=datetime.now(UTC) + timedelta(hours=settings.auth_verification_token_hours),
    )
    await session.commit()
    await _deliver_verification(sender, normalized_email, token)


async def verify_email(session: AsyncSession, *, token: str) -> bool:
    now = datetime.now(UTC)
    action = await _find_action_token(
        session,
        token=token,
        purpose="email_verification",
        now=now,
    )
    if action is None:
        await session.rollback()
        return False

    user = await session.scalar(select(User).where(User.id == action.user_id).with_for_update())
    if user is None or user.email_verified_at is not None:
        await session.rollback()
        return False

    action.consumed_at = now
    user.email_verified_at = now
    await session.commit()
    return True


async def login(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
) -> TokenResponse | None:
    normalized_email = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized_email))
    stored_hash = (
        user.password_hash
        if user is not None and user.password_hash is not None
        else _DUMMY_PASSWORD_HASH
    )
    password_matches = verify_password(password, stored_hash)

    if (
        user is None
        or user.password_hash is None
        or not password_matches
        or user.email_verified_at is None
    ):
        await session.rollback()
        return None

    response, auth_session, refresh_token = _new_session(user.id, settings)
    session.add(auth_session)
    await session.flush()
    refresh_record = _new_refresh_token(auth_session.id, refresh_token, settings)
    session.add(refresh_record)
    await session.commit()
    return response


async def refresh(
    session: AsyncSession,
    settings: Settings,
    *,
    refresh_token: str,
) -> TokenResponse | None:
    now = datetime.now(UTC)
    token_hash = hash_one_time_token(refresh_token)
    refresh_record = await session.scalar(
        select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash).with_for_update()
    )
    if refresh_record is None:
        await session.rollback()
        return None

    auth_session = await session.scalar(
        select(AuthSession).where(AuthSession.id == refresh_record.session_id).with_for_update()
    )
    if auth_session is None:
        await session.rollback()
        return None

    if refresh_record.consumed_at is not None:
        auth_session.revoked_at = auth_session.revoked_at or now
        await session.execute(
            update(AuthRefreshToken)
            .where(
                AuthRefreshToken.session_id == auth_session.id,
                AuthRefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await session.commit()
        return None

    if (
        refresh_record.revoked_at is not None
        or refresh_record.expires_at <= now
        or auth_session.revoked_at is not None
    ):
        await session.rollback()
        return None

    response, next_access_token, next_refresh_token = _new_rotated_tokens(settings)
    refresh_record.consumed_at = now
    new_refresh_record = _new_refresh_token(
        auth_session.id,
        next_refresh_token,
        settings,
    )
    session.add(new_refresh_record)
    await session.flush()
    refresh_record.replaced_by_id = new_refresh_record.id
    auth_session.access_token_hash = hash_one_time_token(next_access_token)
    auth_session.access_expires_at = now + timedelta(minutes=settings.auth_access_token_minutes)
    await session.commit()
    return response


async def revoke_session(session: AsyncSession, auth_session: AuthSession) -> None:
    now = datetime.now(UTC)
    auth_session.revoked_at = auth_session.revoked_at or now
    await session.execute(
        update(AuthRefreshToken)
        .where(
            AuthRefreshToken.session_id == auth_session.id,
            AuthRefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await session.commit()


async def request_password_reset(
    session: AsyncSession,
    sender: AuthEmailSender,
    settings: Settings,
    *,
    email: str,
) -> None:
    normalized_email = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized_email))
    if user is None or user.email_verified_at is None:
        await session.rollback()
        return

    token = await _create_action_token(
        session,
        user_id=user.id,
        purpose="password_reset",
        expires_at=datetime.now(UTC)
        + timedelta(minutes=settings.auth_password_reset_token_minutes),
    )
    await session.commit()
    try:
        await sender.send_password_reset(recipient=normalized_email, token=token)
    except EmailDeliveryError:
        logger.warning("auth.email_delivery_failed")


async def reset_password(
    session: AsyncSession,
    *,
    token: str,
    new_password: str,
) -> bool:
    password_hash = hash_password(new_password)
    now = datetime.now(UTC)
    action = await _find_action_token(
        session,
        token=token,
        purpose="password_reset",
        now=now,
    )
    if action is None:
        await session.rollback()
        return False

    user = await session.scalar(select(User).where(User.id == action.user_id).with_for_update())
    if user is None or user.email_verified_at is None:
        await session.rollback()
        return False

    user.password_hash = password_hash
    action.consumed_at = now
    await session.execute(
        update(AuthActionToken)
        .where(
            AuthActionToken.user_id == user.id,
            AuthActionToken.purpose == "password_reset",
            AuthActionToken.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    await session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await session.execute(
        update(AuthRefreshToken)
        .where(
            AuthRefreshToken.session_id.in_(
                select(AuthSession.id).where(AuthSession.user_id == user.id)
            ),
            AuthRefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await session.commit()
    return True


async def _create_action_token(
    session: AsyncSession,
    *,
    user_id: UUID,
    purpose: str,
    expires_at: datetime,
) -> str:
    now = datetime.now(UTC)
    await session.execute(
        update(AuthActionToken)
        .where(
            AuthActionToken.user_id == user_id,
            AuthActionToken.purpose == purpose,
            AuthActionToken.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    raw_token, token_hash = create_one_time_token()
    session.add(
        AuthActionToken(
            user_id=user_id,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
        )
    )
    await session.flush()
    return raw_token


async def _find_action_token(
    session: AsyncSession,
    *,
    token: str,
    purpose: str,
    now: datetime,
) -> AuthActionToken | None:
    return await session.scalar(
        select(AuthActionToken)
        .where(
            AuthActionToken.token_hash == hash_one_time_token(token),
            AuthActionToken.purpose == purpose,
            AuthActionToken.consumed_at.is_(None),
            AuthActionToken.expires_at > now,
        )
        .with_for_update()
    )


async def _deliver_verification(sender: AuthEmailSender, email: str, token: str) -> None:
    try:
        await sender.send_verification(recipient=email, token=token)
    except EmailDeliveryError:
        logger.warning("auth.email_delivery_failed")


def _new_session(
    user_id: UUID,
    settings: Settings,
) -> tuple[TokenResponse, AuthSession, str]:
    now = datetime.now(UTC)
    response, access_token, refresh_token = _new_rotated_tokens(settings)
    auth_session = AuthSession(
        user_id=user_id,
        access_token_hash=hash_one_time_token(access_token),
        access_expires_at=now + timedelta(minutes=settings.auth_access_token_minutes),
    )
    return response, auth_session, refresh_token


def _new_rotated_tokens(
    settings: Settings,
) -> tuple[TokenResponse, str, str]:
    access_token, _ = create_one_time_token()
    refresh_token, _ = create_one_time_token()
    return (
        TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.auth_access_token_minutes * 60,
        ),
        access_token,
        refresh_token,
    )


def _new_refresh_token(
    session_id: UUID,
    raw_token: str,
    settings: Settings,
) -> AuthRefreshToken:
    return AuthRefreshToken(
        session_id=session_id,
        token_hash=hash_one_time_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.auth_refresh_token_days),
    )
