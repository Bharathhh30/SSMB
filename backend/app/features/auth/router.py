from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import get_database_session
from app.features.auth import service
from app.features.auth.dependencies import (
    AuthenticatedDependency,
    EmailSenderDependency,
    SettingsDependency,
)
from app.features.auth.schemas import (
    AuthenticatedUserRead,
    AuthMessage,
    EmailRequest,
    LoginRequest,
    OneTimeTokenRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.features.auth.security import PasswordPolicyError, normalize_email

router = APIRouter(prefix="/auth", tags=["authentication"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]
REGISTRATION_MESSAGE = (
    "If the address is eligible, instructions will be sent to verify the account."
)
RECOVERY_MESSAGE = "If an eligible account exists, password reset instructions will be sent."
INVALID_ACTION_TOKEN = "Invalid or expired token"
INVALID_CREDENTIALS = "Invalid email or password"


@router.post(
    "/register",
    response_model=AuthMessage,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Register an account and request email verification",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    session: DatabaseSession,
    sender: EmailSenderDependency,
    settings: SettingsDependency,
) -> AuthMessage:
    client_ip = _client_ip(request)
    await _enforce_rate_limit(
        session,
        settings,
        purpose="email_action_ip",
        identity=client_ip,
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    await _enforce_rate_limit(
        session,
        settings,
        purpose="email_action_account",
        identity=f"{client_ip}:{normalize_email(str(payload.email))}",
        maximum_attempts=settings.auth_email_action_attempt_limit,
    )
    try:
        await service.register(
            session,
            sender,
            settings,
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
        )
    except PasswordPolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None
    return AuthMessage(message=REGISTRATION_MESSAGE)


@router.post(
    "/verification/resend",
    response_model=AuthMessage,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Resend account verification instructions",
)
async def resend_verification(
    payload: EmailRequest,
    request: Request,
    session: DatabaseSession,
    sender: EmailSenderDependency,
    settings: SettingsDependency,
) -> AuthMessage:
    client_ip = _client_ip(request)
    await _enforce_rate_limit(
        session,
        settings,
        purpose="email_action_ip",
        identity=client_ip,
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    await _enforce_rate_limit(
        session,
        settings,
        purpose="email_action_account",
        identity=f"{client_ip}:{normalize_email(str(payload.email))}",
        maximum_attempts=settings.auth_email_action_attempt_limit,
    )
    await service.resend_verification(
        session,
        sender,
        settings,
        email=str(payload.email),
    )
    return AuthMessage(message=REGISTRATION_MESSAGE)


@router.post(
    "/verify-email",
    response_model=AuthMessage,
    summary="Verify an email address with a one-time token",
)
async def verify_email(
    payload: OneTimeTokenRequest,
    request: Request,
    session: DatabaseSession,
    settings: SettingsDependency,
) -> AuthMessage:
    await _enforce_rate_limit(
        session,
        settings,
        purpose="token_action_ip",
        identity=_client_ip(request),
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    if not await service.verify_email(session, token=payload.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_ACTION_TOKEN,
        )
    return AuthMessage(message="Email verified. You can now sign in.")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in with a verified email and password",
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: DatabaseSession,
    settings: SettingsDependency,
) -> TokenResponse:
    client_ip = _client_ip(request)
    await _enforce_rate_limit(
        session,
        settings,
        purpose="login_ip",
        identity=client_ip,
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    await _enforce_rate_limit(
        session,
        settings,
        purpose="login_account",
        identity=f"{client_ip}:{normalize_email(str(payload.email))}",
        maximum_attempts=settings.auth_login_attempt_limit,
    )
    tokens = await service.login(
        session,
        settings,
        email=str(payload.email),
        password=payload.password,
    )
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate a refresh token and issue a new access token",
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    session: DatabaseSession,
    settings: SettingsDependency,
) -> TokenResponse:
    await _enforce_rate_limit(
        session,
        settings,
        purpose="token_action_ip",
        identity=_client_ip(request),
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    tokens = await service.refresh(
        session,
        settings,
        refresh_token=payload.refresh_token,
    )
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current session",
)
async def logout(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
) -> Response:
    await service.revoke_session(session, principal.session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=AuthenticatedUserRead,
    summary="Read the authenticated account",
)
async def get_me(principal: AuthenticatedDependency) -> AuthenticatedUserRead:
    user = principal.user
    if user.email is None or user.display_name is None or user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthenticatedUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified_at=user.email_verified_at,
    )


@router.post(
    "/password/forgot",
    response_model=AuthMessage,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password recovery instructions",
)
async def request_password_reset(
    payload: EmailRequest,
    request: Request,
    session: DatabaseSession,
    sender: EmailSenderDependency,
    settings: SettingsDependency,
) -> AuthMessage:
    client_ip = _client_ip(request)
    await _enforce_rate_limit(
        session,
        settings,
        purpose="email_action_ip",
        identity=client_ip,
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    await _enforce_rate_limit(
        session,
        settings,
        purpose="email_action_account",
        identity=f"{client_ip}:{normalize_email(str(payload.email))}",
        maximum_attempts=settings.auth_email_action_attempt_limit,
    )
    await service.request_password_reset(
        session,
        sender,
        settings,
        email=str(payload.email),
    )
    return AuthMessage(message=RECOVERY_MESSAGE)


@router.post(
    "/password/reset",
    response_model=AuthMessage,
    summary="Reset a password with a one-time token",
)
async def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    session: DatabaseSession,
    settings: SettingsDependency,
) -> AuthMessage:
    await _enforce_rate_limit(
        session,
        settings,
        purpose="token_action_ip",
        identity=_client_ip(request),
        maximum_attempts=settings.auth_ip_attempt_limit,
    )
    try:
        reset = await service.reset_password(
            session,
            token=payload.token,
            new_password=payload.new_password,
        )
    except PasswordPolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None

    if not reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_ACTION_TOKEN,
        )
    return AuthMessage(message="Password updated. Sign in with your new password.")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


async def _enforce_rate_limit(
    session: AsyncSession,
    settings: Settings,
    *,
    purpose: str,
    identity: str,
    maximum_attempts: int,
) -> None:
    try:
        retry_after = await service.consume_rate_limit(
            session,
            settings,
            purpose=purpose,
            identity=identity,
            maximum_attempts=maximum_attempts,
        )
    except service.RateLimitSecretNotConfigured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication rate limiting is not configured",
        ) from None

    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
