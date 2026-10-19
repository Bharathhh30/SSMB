from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.auth.dependencies import AuthenticatedDependency
from app.features.profiles import service
from app.features.profiles.schemas import ProfileRead, ProfileUpdate

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
    return await service.update_own_profile(session, principal, update)
