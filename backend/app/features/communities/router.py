from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import get_database_session
from app.features.auth import service as auth_service
from app.features.auth.dependencies import AuthenticatedDependency, SettingsDependency
from app.features.communities import service
from app.features.communities.schemas import (
    CommunityCreate,
    CommunityDetailRead,
    CommunityInviteAccept,
    CommunityInviteCreated,
    CommunityInvitePage,
    CommunityMembershipRead,
    CommunityPage,
    CommunityRead,
    CommunityRosterPage,
    CommunityUpdate,
    MyCommunityMembershipPage,
)
from app.features.communities.service import (
    CommunityForbidden,
    CommunityInviteAlreadyUsed,
    CommunityInviteConflict,
    CommunityInviteUnavailable,
    CommunityNameConflict,
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
    responses={
        409: {"description": "A community already uses this name or its generated URL collided."}
    },
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
    except CommunityNameConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A community with this name already exists. Choose a different name.",
        ) from None
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
        membership, created, community_slug = await service.join_community(
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
    return CommunityMembershipRead(
        community_slug=community_slug,
        role=membership.role,
        joined_at=membership.joined_at,
    )


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


@router.post(
    "/{slug}/invites",
    response_model=CommunityInviteCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single-use invite for an invite-only community",
    responses={
        403: {"description": "The authenticated user is not the community owner."},
        404: {"description": "No community exists with this slug."},
        409: {"description": "Invites are unavailable for this community state."},
        429: {"description": "The invite creation rate limit was exceeded."},
    },
)
async def create_community_invite(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    settings: SettingsDependency,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
) -> CommunityInviteCreated:
    await _enforce_community_invite_rate_limit(
        session,
        settings,
        purpose="community_invite_create",
        identity=str(principal.user.id),
        maximum_attempts=service.COMMUNITY_INVITE_CREATE_LIMIT,
    )
    try:
        invite, raw_token = await service.create_community_invite(
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
    except CommunityInviteConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    return CommunityInviteCreated(
        invite_public_id=invite.public_id,
        invite_token=raw_token,
        expires_at=invite.expires_at,
    )


@router.get(
    "/{slug}/invites",
    response_model=CommunityInvitePage,
    summary="List invite metadata for an owned community",
    responses={
        403: {"description": "The authenticated user is not the community owner."},
        404: {"description": "No community exists with this slug."},
    },
)
async def get_community_invites(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CommunityInvitePage:
    try:
        invites, total = await service.list_community_invites(
            session,
            slug=slug,
            owner_id=principal.user.id,
            limit=limit,
            offset=offset,
        )
    except CommunityNotFound:
        raise HTTPException(status_code=404, detail="Community not found") from None
    except CommunityForbidden:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage this community.",
        ) from None
    return CommunityInvitePage(items=invites, total=total, limit=limit, offset=offset)


@router.delete(
    "/{slug}/invites/{invite_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an unused community invite",
    responses={
        403: {"description": "The authenticated user is not the community owner."},
        404: {"description": "The community or invite does not exist."},
        409: {"description": "The invite has already been accepted."},
    },
)
async def revoke_community_invite(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
    invite_public_id: UUID,
) -> Response:
    try:
        await service.revoke_community_invite(
            session,
            slug=slug,
            invite_public_id=invite_public_id,
            owner_id=principal.user.id,
        )
    except CommunityNotFound:
        raise HTTPException(status_code=404, detail="Community not found") from None
    except CommunityForbidden:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage this community.",
        ) from None
    except CommunityInviteUnavailable:
        raise HTTPException(status_code=404, detail="Invite not found") from None
    except CommunityInviteAlreadyUsed:
        raise HTTPException(
            status_code=409,
            detail="This invite has already been accepted and cannot be revoked.",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/invites/accept",
    response_model=CommunityMembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Accept a community invite",
    responses={
        404: {"description": "The invite is invalid, expired, revoked, or unavailable."},
        409: {"description": "The invite has already been accepted by another account."},
        429: {"description": "The invite acceptance rate limit was exceeded."},
    },
)
async def accept_community_invite(
    data: CommunityInviteAccept,
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    settings: SettingsDependency,
    response: Response,
) -> CommunityMembershipRead:
    await _enforce_community_invite_rate_limit(
        session,
        settings,
        purpose="community_invite_accept",
        identity=str(principal.user.id),
        maximum_attempts=service.COMMUNITY_INVITE_ACCEPT_LIMIT,
    )
    try:
        membership, created, community_slug = await service.accept_community_invite(
            session,
            invite_token=data.invite_token,
            user_id=principal.user.id,
        )
    except CommunityInviteUnavailable:
        raise HTTPException(
            status_code=404,
            detail="Invite is invalid or no longer available.",
        ) from None
    except CommunityInviteAlreadyUsed:
        raise HTTPException(
            status_code=409,
            detail="This invite has already been used by another account.",
        ) from None
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return CommunityMembershipRead(
        community_slug=community_slug,
        role=membership.role,
        joined_at=membership.joined_at,
    )


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
    "/memberships/me",
    response_model=MyCommunityMembershipPage,
    summary="List communities the authenticated user belongs to",
    description=(
        "Returns the current account's memberships, including communities it owns. "
        "This endpoint cannot be used to inspect another user's memberships."
    ),
)
async def get_my_community_memberships(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MyCommunityMembershipPage:
    items, total = await service.list_own_memberships(
        session,
        user_id=principal.user.id,
        limit=limit,
        offset=offset,
    )
    return MyCommunityMembershipPage(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/mine",
    response_model=CommunityPage,
    summary="List communities owned by the authenticated user",
)
async def get_my_communities(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CommunityPage:
    communities, total = await service.list_owned_communities(
        session,
        owner_id=principal.user.id,
        limit=limit,
        offset=offset,
    )
    return CommunityPage(items=communities, total=total, limit=limit, offset=offset)


@router.get(
    "/{slug}/members",
    response_model=CommunityRosterPage,
    summary="List a community roster for its owner or moderators",
    description=(
        "Only the community owner and its moderators can view member identities. "
        "This endpoint does not expose a user's memberships across communities."
    ),
    responses={
        403: {"description": "The authenticated user is not this community's owner or moderator."},
        404: {"description": "No community exists with this slug."},
    },
)
async def get_community_roster(
    principal: AuthenticatedDependency,
    session: DatabaseSession,
    slug: Annotated[
        str,
        Path(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CommunityRosterPage:
    try:
        items, total = await service.list_community_roster(
            session,
            slug=slug,
            requester_id=principal.user.id,
            limit=limit,
            offset=offset,
        )
    except CommunityNotFound:
        raise HTTPException(status_code=404, detail="Community not found") from None
    except CommunityForbidden:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this community's member roster.",
        ) from None
    return CommunityRosterPage(items=items, total=total, limit=limit, offset=offset)


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


async def _enforce_community_invite_rate_limit(
    session: AsyncSession,
    settings: Settings,
    *,
    purpose: str,
    identity: str,
    maximum_attempts: int,
) -> None:
    try:
        retry_after = await auth_service.consume_rate_limit(
            session,
            settings,
            purpose=purpose,
            identity=identity,
            maximum_attempts=maximum_attempts,
        )
    except auth_service.RateLimitSecretNotConfigured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Invite rate limiting is not configured",
        ) from None
    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invite actions. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
