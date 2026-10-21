from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.auth.dependencies import AuthenticatedDependency
from app.features.profiles import service
from app.features.profiles.schemas import ProfileRead, ProfileUpdate
from app.features.profiles.service import ProfilePolicyError

router = APIRouter(prefix="/profile", tags=["profiles"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


@router.get(
    "/me",
    response_model=ProfileRead,
    summary="Read the authenticated user's private profile",
)
async def get_my_profile(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
) -> ProfileRead:
    return await service.get_own_profile(session, principal)


@router.patch(
    "/me",
    response_model=ProfileRead,
    summary="Update the authenticated user's private profile",
)
async def update_my_profile(
    update: ProfileUpdate,
    principal: AuthenticatedDependency,
    session: DatabaseSession,
) -> ProfileRead:
    try:
        return await service.update_own_profile(session, principal, update)
    except ProfilePolicyError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None
