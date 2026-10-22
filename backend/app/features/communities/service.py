import re
import unicodedata
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.security import create_one_time_token, hash_one_time_token
from app.features.communities import repository
from app.features.communities.models import Community, CommunityInvite, CommunityMembership
from app.features.communities.schemas import (
    CommunityCreate,
    CommunityInviteRead,
    CommunityUpdate,
)

COMMUNITY_INVITE_LIFETIME = timedelta(days=7)
COMMUNITY_INVITE_CREATE_LIMIT = 10
COMMUNITY_INVITE_ACCEPT_LIMIT = 20


class CommunitySlugConflict(Exception):
    """The generated public slug collided with another community."""


class CommunityNameConflict(Exception):
    """A community already uses the normalized display name."""


class CommunityNotJoinable(Exception):
    """The community does not exist or cannot be joined by this caller."""


class CommunityOwnerCannotLeave(Exception):
    """The owner must transfer ownership before leaving their community."""


class CommunityNotFound(Exception):
    """No community exists for the requested slug."""


class CommunityForbidden(Exception):
    """The authenticated caller is not allowed to manage the community."""


class CommunityInviteConflict(Exception):
    """The requested invite action conflicts with the invite or community state."""


class CommunityInviteUnavailable(Exception):
    """The invite is invalid, expired, revoked, or belongs to an unavailable community."""


class CommunityInviteAlreadyUsed(Exception):
    """The invite has already been accepted by another account."""


async def get_public_community_with_member_count(
    session: AsyncSession,
    *,
    slug: str,
) -> tuple[Community, int] | None:
    return await repository.get_public_community_with_member_count(session, slug=slug)


async def discover_communities(
    session: AsyncSession,
    *,
    query: str | None,
    topic: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Community], int]:
    normalized_query = query.strip() if query and query.strip() else None
    normalized_topic = topic.strip() if topic and topic.strip() else None
    return await repository.list_communities(
        session,
        query=normalized_query,
        topic=normalized_topic,
        limit=limit,
        offset=offset,
    )


async def discoverable_topics(session: AsyncSession) -> list[str]:
    return await repository.list_public_topics(session)


async def create_community(
    session: AsyncSession,
    *,
    owner_id: UUID,
    data: CommunityCreate,
) -> Community:
    if await repository.community_name_exists(session, name=data.name):
        await session.rollback()
        raise CommunityNameConflict

    base_slug = _slugify(data.name)
    slug = base_slug
    if await repository.community_slug_exists(session, slug=slug):
        slug = _with_unique_suffix(base_slug)

    try:
        community = await repository.create_community(
            session,
            owner_id=owner_id,
            name=data.name,
            slug=slug,
            topic=data.topic,
            description=data.description,
            access_type=data.access_type,
            expires_at=data.expires_at,
        )
        await session.commit()
        return community
    except IntegrityError as error:
        await session.rollback()
        if _is_unique_violation(error, "uq_communities_normalized_name"):
            raise CommunityNameConflict from error
        if _is_slug_unique_conflict(error):
            if await repository.community_name_exists(session, name=data.name):
                raise CommunityNameConflict from error
            raise CommunitySlugConflict from error
        raise


async def join_community(
    session: AsyncSession,
    *,
    slug: str,
    user_id: UUID,
) -> tuple[CommunityMembership, bool]:
    now = datetime.now(UTC)
    community = await repository.get_joinable_community(session, slug=slug, now=now)
    if community is None:
        await session.rollback()
        raise CommunityNotJoinable

    membership = await repository.get_membership(
        session,
        community_id=community.id,
        user_id=user_id,
    )
    if membership is not None:
        await session.commit()
        return membership, False

    membership = await repository.add_member(
        session,
        community_id=community.id,
        user_id=user_id,
    )
    await session.commit()
    return membership, True


async def leave_community(
    session: AsyncSession,
    *,
    slug: str,
    user_id: UUID,
) -> None:
    community = await repository.get_community_by_slug_for_leave(session, slug=slug)
    if community is None:
        await session.rollback()
        raise CommunityNotJoinable

    membership = await repository.get_membership(
        session,
        community_id=community.id,
        user_id=user_id,
    )
    now = datetime.now(UTC)
    if membership is None:
        is_public_and_active = community.access_type == "open" and (
            community.expires_at is None or community.expires_at > now
        )
        if is_public_and_active:
            await session.commit()
            return
        await session.rollback()
        raise CommunityNotJoinable

    if membership.role == "owner" or community.owner_id == user_id:
        await session.rollback()
        raise CommunityOwnerCannotLeave

    await repository.delete_membership(session, membership)
    await session.commit()


async def get_owned_community(
    session: AsyncSession,
    *,
    slug: str,
    owner_id: UUID,
) -> Community:
    community = await repository.get_owned_community(session, slug=slug)
    if community is None:
        raise CommunityNotFound
    if community.owner_id != owner_id:
        raise CommunityForbidden
    return community


async def update_owned_community(
    session: AsyncSession,
    *,
    slug: str,
    owner_id: UUID,
    data: CommunityUpdate,
) -> Community:
    community = await repository.get_owned_community(
        session,
        slug=slug,
        for_update=True,
    )
    if community is None:
        await session.rollback()
        raise CommunityNotFound
    if community.owner_id != owner_id:
        await session.rollback()
        raise CommunityForbidden

    for field in data.model_fields_set:
        setattr(community, field, getattr(data, field))
    await session.commit()
    return community


async def create_community_invite(
    session: AsyncSession,
    *,
    slug: str,
    owner_id: UUID,
) -> tuple[CommunityInvite, str]:
    community = await _get_locked_owned_community(
        session,
        slug=slug,
        owner_id=owner_id,
    )
    now = datetime.now(UTC)
    if community.access_type != "invite_only":
        await session.rollback()
        raise CommunityInviteConflict("Invites can only be created for invite-only communities")
    if community.expires_at is not None and community.expires_at <= now:
        await session.rollback()
        raise CommunityInviteConflict("Expired communities cannot issue invites")

    invite_expires_at = now + COMMUNITY_INVITE_LIFETIME
    if community.expires_at is not None:
        invite_expires_at = min(invite_expires_at, community.expires_at)
    raw_token, token_hash = create_one_time_token()
    invite = await repository.create_invite(
        session,
        community_id=community.id,
        created_by_user_id=owner_id,
        token_hash=token_hash,
        created_at=now,
        expires_at=invite_expires_at,
    )
    await session.commit()
    return invite, raw_token


async def list_community_invites(
    session: AsyncSession,
    *,
    slug: str,
    owner_id: UUID,
    limit: int,
    offset: int,
) -> tuple[list[CommunityInviteRead], int]:
    community = await repository.get_owned_community(session, slug=slug)
    if community is None:
        raise CommunityNotFound
    if community.owner_id != owner_id:
        raise CommunityForbidden

    invites, total = await repository.list_community_invites(
        session,
        community_id=community.id,
        limit=limit,
        offset=offset,
    )
    now = datetime.now(UTC)
    result = []
    for invite in invites:
        if invite.revoked_at is not None:
            invite_status = "revoked"
        elif invite.consumed_at is not None:
            invite_status = "accepted"
        elif invite.expires_at <= now or (
            community.expires_at is not None and community.expires_at <= now
        ):
            invite_status = "expired"
        else:
            invite_status = "active"
        result.append(
            CommunityInviteRead(
                invite_id=invite.id,
                created_at=invite.created_at,
                expires_at=invite.expires_at,
                status=invite_status,
            )
        )
    return result, total


async def revoke_community_invite(
    session: AsyncSession,
    *,
    slug: str,
    invite_id: UUID,
    owner_id: UUID,
) -> None:
    community = await _get_locked_owned_community(
        session,
        slug=slug,
        owner_id=owner_id,
    )
    invite = await repository.get_community_invite(
        session,
        community_id=community.id,
        invite_id=invite_id,
        for_update=True,
    )
    if invite is None:
        await session.rollback()
        raise CommunityInviteUnavailable
    if invite.consumed_at is not None:
        await session.rollback()
        raise CommunityInviteAlreadyUsed
    if invite.revoked_at is not None:
        await session.commit()
        return

    invite.revoked_at = datetime.now(UTC)
    await session.commit()


async def accept_community_invite(
    session: AsyncSession,
    *,
    invite_token: str,
    user_id: UUID,
) -> tuple[CommunityMembership, bool]:
    token_hash = hash_one_time_token(invite_token)
    community_id = await repository.get_invite_community_id_by_token_hash(
        session,
        token_hash=token_hash,
    )
    if community_id is None:
        await session.rollback()
        raise CommunityInviteUnavailable

    community = await repository.get_community_by_id_for_update(
        session,
        community_id=community_id,
    )
    invite = await repository.get_invite_by_token_hash(
        session,
        token_hash=token_hash,
        for_update=True,
    )
    if community is None or invite is None:
        await session.rollback()
        raise CommunityInviteUnavailable

    now = datetime.now(UTC)
    if invite.revoked_at is not None or invite.expires_at <= now:
        await session.rollback()
        raise CommunityInviteUnavailable
    if community.expires_at is not None and community.expires_at <= now:
        await session.rollback()
        raise CommunityInviteUnavailable

    if invite.consumed_at is not None:
        if invite.accepted_by_user_id != user_id:
            await session.rollback()
            raise CommunityInviteAlreadyUsed
        existing_membership = await repository.get_membership(
            session,
            community_id=community.id,
            user_id=user_id,
        )
        if existing_membership is None:
            await session.rollback()
            raise CommunityInviteAlreadyUsed
        await session.commit()
        return existing_membership, False

    membership = await repository.get_membership(
        session,
        community_id=community.id,
        user_id=user_id,
    )
    created = membership is None
    if membership is None:
        membership = await repository.add_member(
            session,
            community_id=community.id,
            user_id=user_id,
        )
    invite.consumed_at = now
    invite.accepted_by_user_id = user_id
    await session.commit()
    return membership, created


async def _get_locked_owned_community(
    session: AsyncSession,
    *,
    slug: str,
    owner_id: UUID,
) -> Community:
    community = await repository.get_owned_community(
        session,
        slug=slug,
        for_update=True,
    )
    if community is None:
        await session.rollback()
        raise CommunityNotFound
    if community.owner_id != owner_id:
        await session.rollback()
        raise CommunityForbidden
    return community


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug[:140].rstrip("-") or "community"


def _with_unique_suffix(base_slug: str) -> str:
    suffix = uuid4().hex[:8]
    return f"{base_slug[: 140 - len(suffix) - 1].rstrip('-')}-{suffix}"


def _is_slug_unique_conflict(error: Exception) -> bool:
    return _is_unique_violation(error, "uq_communities_slug")


def _is_unique_violation(error: Exception, constraint_name: str) -> bool:
    current: object | None = error
    while current is not None:
        if (
            getattr(current, "sqlstate", None) == "23505"
            and getattr(current, "constraint_name", None) == constraint_name
        ):
            return True
        current = getattr(current, "orig", None) or getattr(current, "__cause__", None)
    return False
