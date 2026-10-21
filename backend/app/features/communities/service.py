import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.communities import repository
from app.features.communities.models import Community, CommunityMembership
from app.features.communities.schemas import CommunityCreate, CommunityUpdate


class CommunitySlugConflict(Exception):
    """The generated public slug collided with another community."""


class CommunityNotJoinable(Exception):
    """The community does not exist or cannot be joined by this caller."""


class CommunityOwnerCannotLeave(Exception):
    """The owner must transfer ownership before leaving their community."""


class CommunityNotFound(Exception):
    """No community exists for the requested slug."""


class CommunityForbidden(Exception):
    """The authenticated caller is not allowed to manage the community."""


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
        if _is_slug_unique_conflict(error):
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


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug[:140].rstrip("-") or "community"


def _with_unique_suffix(base_slug: str) -> str:
    suffix = uuid4().hex[:8]
    return f"{base_slug[: 140 - len(suffix) - 1].rstrip('-')}-{suffix}"


def _is_slug_unique_conflict(error: Exception) -> bool:
    current: object | None = error
    while current is not None:
        if (
            getattr(current, "sqlstate", None) == "23505"
            and getattr(current, "constraint_name", None) == "uq_communities_slug"
        ):
            return True
        current = getattr(current, "orig", None) or getattr(current, "__cause__", None)
    return False
