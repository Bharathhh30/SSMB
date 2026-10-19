from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import get_database_session
from app.features.auth.models import AuthSession
from app.features.auth.security import hash_one_time_token
from app.features.users.models import User
from app.integrations.auth_email import AuthEmailSender

bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    user: User
    session: AuthSession


async def get_auth_email_sender(request: Request) -> AuthEmailSender:
    sender: AuthEmailSender | None = request.app.state.auth_email_sender
    if sender is None or not getattr(sender, "is_configured", True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication email delivery is not configured",
        )
    return sender


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


EmailSenderDependency = Annotated[AuthEmailSender, Depends(get_auth_email_sender)]
SettingsDependency = Annotated[Settings, Depends(get_app_settings)]


async def require_authenticated_principal(
    session: DatabaseSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    if len(credentials.credentials) > 128:
        raise _unauthorized()

    token_hash = hash_one_time_token(credentials.credentials)
    statement = (
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.access_token_hash == token_hash,
            AuthSession.revoked_at.is_(None),
            AuthSession.access_expires_at > datetime.now(UTC),
            User.email_verified_at.is_not(None),
        )
    )
    result = await session.execute(statement)
    row = result.one_or_none()
    if row is None:
        raise _unauthorized()
    auth_session, user = row
    return AuthenticatedPrincipal(user=user, session=auth_session)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


AuthenticatedDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(require_authenticated_principal),
]
