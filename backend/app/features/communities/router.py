from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.auth.dependencies import AuthenticatedDependency
from app.features.communities import service
from app.features.communities.schemas import CommunityCreate, CommunityPage, CommunityRead
from app.features.communities.service import CommunitySlugConflict

router = APIRouter(prefix="/communities", tags=["communities"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


@router.post(
    "",
    response_model=CommunityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a community",
)
async def create_community(
    data: CommunityCreate,
    principal: AuthenticatedDependency,
    session: DatabaseSession,
) -> CommunityRead:
    try:
        community = await service.create_community(
            session,
            owner_id=principal.user.id,
            data=data,
        )
    except CommunitySlugConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A community URL conflict occurred. Please retry.",
        ) from None
    return CommunityRead.model_validate(community)


@router.get(
    "",
    response_model=CommunityPage,
    summary="Discover communities",
)
async def get_communities(
    session: DatabaseSession,
    q: Annotated[
        str | None,
        Query(
            max_length=120,
            description=(
                "Case-insensitive partial match. Empty or whitespace-only values are ignored."
            ),
        ),
    ] = None,
    topic: Annotated[
        str | None,
        Query(
            max_length=80,
            description=(
                "Exact topic match after trimming. Empty or whitespace-only values are ignored."
            ),
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CommunityPage:
    communities, total = await service.discover_communities(
        session,
        query=q,
        topic=topic,
        limit=limit,
        offset=offset,
    )
    return CommunityPage(items=communities, total=total, limit=limit, offset=offset)


@router.get(
    "/{slug}",
    response_model=CommunityRead,
    summary="Read a public community preview",
)
async def get_community(
    session: DatabaseSession,
    slug: Annotated[str, Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")],
) -> CommunityRead:
    community = await service.get_public_community(session, slug=slug)
    if community is None:
        raise HTTPException(status_code=404, detail="Community not found")
    return CommunityRead.model_validate(community)
