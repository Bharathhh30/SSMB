from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.communities.models import Community, CommunityInvite, CommunityMembership

PUBLIC_TOPIC_LIMIT = 50


async def list_communities(
    session: AsyncSession,
    *,
    query: str | None,
    topic: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Community], int]:
    now = datetime.now(UTC)
    filters = [
        Community.access_type == "open",
        or_(Community.expires_at.is_(None), Community.expires_at > now),
    ]

    if query:
        escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped_query}%"
        filters.append(
            or_(
                Community.name.ilike(pattern, escape="\\"),
                Community.topic.ilike(pattern, escape="\\"),
                Community.description.ilike(pattern, escape="\\"),
            )
        )
    if topic:
        filters.append(func.trim(Community.topic) == topic)

    total = await session.scalar(select(func.count()).select_from(Community).where(*filters))
    statement = (
        select(Community)
        .where(*filters)
        .order_by(Community.name.asc(), Community.id.asc())
        .limit(limit)
        .offset(offset)
    )
    communities = await session.scalars(statement)
    return list(communities.all()), total or 0


async def list_owned_communities(
    session: AsyncSession,
    *,
    owner_id: UUID,
    limit: int,
    offset: int,
) -> tuple[list[Community], int]:
    filters = [Community.owner_id == owner_id]
    total = await session.scalar(select(func.count()).select_from(Community).where(*filters))
    statement = (
        select(Community)
        .where(*filters)
        .order_by(Community.created_at.desc(), Community.id.asc())
        .limit(limit)
        .offset(offset)
    )
    communities = await session.scalars(statement)
    return list(communities.all()), total or 0


async def list_public_topics(session: AsyncSession) -> list[str]:
    now = datetime.now(UTC)
    topic = func.trim(Community.topic).label("topic")
    statement = (
        select(topic)
        .where(
            Community.access_type == "open",
            or_(Community.expires_at.is_(None), Community.expires_at > now),
        )
        .distinct()
        .order_by(topic.asc())
        .limit(PUBLIC_TOPIC_LIMIT)
    )
    topics = await session.scalars(statement)
    return list(topics.all())


async def get_public_community(session: AsyncSession, *, slug: str) -> Community | None:
    now = datetime.now(UTC)
    statement = select(Community).where(
        Community.slug == slug,
        Community.access_type == "open",
        or_(Community.expires_at.is_(None), Community.expires_at > now),
    )
    return await session.scalar(statement)


async def get_public_community_with_member_count(
    session: AsyncSession,
    *,
    slug: str,
) -> tuple[Community, int] | None:
    now = datetime.now(UTC)
    member_count = (
        select(func.count(CommunityMembership.id))
        .where(CommunityMembership.community_id == Community.id)
        .scalar_subquery()
    )
    statement = select(Community, member_count.label("member_count")).where(
        Community.slug == slug,
        Community.access_type == "open",
        or_(Community.expires_at.is_(None), Community.expires_at > now),
    )
    row = (await session.execute(statement)).one_or_none()
    return (row[0], row[1]) if row is not None else None


async def community_name_exists(session: AsyncSession, *, name: str) -> bool:
    normalized_name = func.lower(func.btrim(name))
    statement = select(Community.id).where(
        func.lower(func.btrim(Community.name)) == normalized_name
    )
    return bool(await session.scalar(statement))


async def create_community(
    session: AsyncSession,
    *,
    community_id: UUID,
    public_id: UUID,
    owner_id: UUID,
    name: str,
    slug: str,
    topic: str,
    description: str,
    access_type: str,
    expires_at: datetime | None,
) -> Community:
    community = Community(
        id=community_id,
        public_id=public_id,
        owner_id=owner_id,
        name=name,
        slug=slug,
        topic=topic,
        description=description,
        access_type=access_type,
        expires_at=expires_at,
    )
    founder_membership = CommunityMembership(
        id=uuid4(),
        community_id=community.id,
        user_id=owner_id,
        role="owner",
        joined_at=datetime.now(UTC),
    )
    session.add_all([community, founder_membership])
    await session.flush()
    return community


async def get_joinable_community(
    session: AsyncSession,
    *,
    slug: str,
    now: datetime,
) -> Community | None:
    statement = (
        select(Community)
        .where(
            Community.slug == slug,
            Community.access_type == "open",
            or_(Community.expires_at.is_(None), Community.expires_at > now),
        )
        .with_for_update()
    )
    return await session.scalar(statement)


async def get_community_by_slug_for_leave(
    session: AsyncSession,
    *,
    slug: str,
) -> Community | None:
    statement = select(Community).where(Community.slug == slug).with_for_update()
    return await session.scalar(statement)


async def get_owned_community(
    session: AsyncSession,
    *,
    slug: str,
    for_update: bool = False,
) -> Community | None:
    statement = select(Community).where(Community.slug == slug)
    if for_update:
        statement = statement.with_for_update()
    return await session.scalar(statement)


async def get_membership(
    session: AsyncSession,
    *,
    community_id: UUID,
    user_id: UUID,
) -> CommunityMembership | None:
    return await session.scalar(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == user_id,
        )
    )


async def list_user_memberships(
    session: AsyncSession,
    *,
    user_id: UUID,
    limit: int,
    offset: int,
) -> tuple[list[tuple[CommunityMembership, Community]], int]:
    filters = [CommunityMembership.user_id == user_id]
    total = await session.scalar(
        select(func.count()).select_from(CommunityMembership).where(*filters)
    )
    statement = (
        select(CommunityMembership, Community)
        .join(Community, Community.id == CommunityMembership.community_id)
        .where(*filters)
        .order_by(
            CommunityMembership.joined_at.desc(),
            CommunityMembership.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(statement)
    return [(row[0], row[1]) for row in result.all()], total or 0


async def add_member(
    session: AsyncSession,
    *,
    community_id: UUID,
    user_id: UUID,
) -> CommunityMembership:
    membership = CommunityMembership(
        id=uuid4(),
        community_id=community_id,
        user_id=user_id,
        role="member",
        joined_at=datetime.now(UTC),
    )
    session.add(membership)
    await session.flush()
    return membership


async def delete_membership(session: AsyncSession, membership: CommunityMembership) -> None:
    await session.delete(membership)
    await session.flush()


async def create_invite(
    session: AsyncSession,
    *,
    community_id: UUID,
    created_by_user_id: UUID,
    token_hash: str,
    created_at: datetime,
    expires_at: datetime,
) -> CommunityInvite:
    invite = CommunityInvite(
        id=uuid4(),
        public_id=uuid4(),
        community_id=community_id,
        created_by_user_id=created_by_user_id,
        token_hash=token_hash,
        created_at=created_at,
        expires_at=expires_at,
    )
    session.add(invite)
    await session.flush()
    return invite


async def list_community_invites(
    session: AsyncSession,
    *,
    community_id: UUID,
    limit: int,
    offset: int,
) -> tuple[list[CommunityInvite], int]:
    total = await session.scalar(
        select(func.count())
        .select_from(CommunityInvite)
        .where(CommunityInvite.community_id == community_id)
    )
    statement = (
        select(CommunityInvite)
        .where(CommunityInvite.community_id == community_id)
        .order_by(CommunityInvite.created_at.desc(), CommunityInvite.id.asc())
        .limit(limit)
        .offset(offset)
    )
    invites = await session.scalars(statement)
    return list(invites.all()), total or 0


async def get_invite_community_id_by_token_hash(
    session: AsyncSession,
    *,
    token_hash: str,
) -> UUID | None:
    return await session.scalar(
        select(CommunityInvite.community_id).where(CommunityInvite.token_hash == token_hash)
    )


async def get_community_by_id_for_update(
    session: AsyncSession,
    *,
    community_id: UUID,
) -> Community | None:
    return await session.scalar(
        select(Community).where(Community.id == community_id).with_for_update()
    )


async def get_invite_by_token_hash(
    session: AsyncSession,
    *,
    token_hash: str,
    for_update: bool = False,
) -> CommunityInvite | None:
    statement = select(CommunityInvite).where(CommunityInvite.token_hash == token_hash)
    if for_update:
        statement = statement.with_for_update()
    return await session.scalar(statement)


async def get_community_invite(
    session: AsyncSession,
    *,
    community_id: UUID,
    invite_public_id: UUID,
    for_update: bool = False,
) -> CommunityInvite | None:
    statement = select(CommunityInvite).where(
        CommunityInvite.public_id == invite_public_id,
        CommunityInvite.community_id == community_id,
    )
    if for_update:
        statement = statement.with_for_update()
    return await session.scalar(statement)
