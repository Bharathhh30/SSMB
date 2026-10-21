from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.auth.dependencies import AuthenticatedDependency
from app.features.communities import service
from app.features.communities.schemas import (
    CommunityCreate,
    CommunityDetailRead,
    CommunityMembershipRead,
    CommunityPage,
    CommunityRead,
    CommunityUpdate,
)
from app.features.communities.service import (
    CommunityForbidden,
    CommunityNotFound,
    CommunityNotJoinable,
    CommunityOwnerCannotLeave,
    CommunitySlugConflict,
)

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


@router.post(
    "/{slug}/join",
    response_model=CommunityMembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Join an open community",
)
async def join_community(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    response: Response,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
) -> CommunityMembershipRead:
    try:
        membership, created = await service.join_community(
            session,
            slug=slug,
            user_id=principal.user.id,
        )
    except CommunityNotJoinable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        ) from None
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return CommunityMembershipRead.model_validate(membership)


@router.delete(
    "/{slug}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave a community",
)
async def leave_community(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
) -> Response:
    try:
        await service.leave_community(
            session,
            slug=slug,
            user_id=principal.user.id,
        )
    except CommunityNotJoinable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        ) from None
    except CommunityOwnerCannotLeave:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transfer community ownership before leaving",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{slug}/manage",
    response_model=CommunityRead,
    summary="Read a community owned by the current user",
    responses={
        403: {"description": "The authenticated user is not the community owner."},
        404: {"description": "No community exists with this slug."},
    },
)
async def get_owned_community(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
) -> CommunityRead:
    try:
        community = await service.get_owned_community(
            session,
            slug=slug,
            owner_id=principal.user.id,
        )
    except CommunityNotFound:
        raise HTTPException(status_code=404, detail="Community not found") from None
    except CommunityForbidden:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage this community.",
        ) from None
    return CommunityRead.model_validate(community)


@router.patch(
    "/{slug}",
    response_model=CommunityRead,
    summary="Update a community owned by the current user",
    responses={
        403: {"description": "The authenticated user is not the community owner."},
        404: {"description": "No community exists with this slug."},
    },
)
async def update_owned_community(
    data: CommunityUpdate,
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
) -> CommunityRead:
    try:
        community = await service.update_owned_community(
            session,
            slug=slug,
            owner_id=principal.user.id,
            data=data,
        )
    except CommunityNotFound:
        raise HTTPException(status_code=404, detail="Community not found") from None
    except CommunityForbidden:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage this community.",
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
    response_model=CommunityDetailRead,
    summary="Read a public community preview",
    responses={404: {"description": "Community is unknown, private, or expired."}},
)
async def get_community(
    session: DatabaseSession,
    slug: Annotated[str, Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")],
) -> CommunityDetailRead:
    community_details = await service.get_public_community_with_member_count(
        session,
        slug=slug,
    )
    if community_details is None:
        raise HTTPException(status_code=404, detail="Community not found")
    community, member_count = community_details
    public_fields = CommunityRead.model_validate(community).model_dump()
    return CommunityDetailRead(**public_fields, member_count=member_count)
