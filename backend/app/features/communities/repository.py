from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.communities.models import Community, CommunityMembership

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


async def community_slug_exists(session: AsyncSession, *, slug: str) -> bool:
    return bool(await session.scalar(select(Community.id).where(Community.slug == slug)))


async def create_community(
    session: AsyncSession,
    *,
    owner_id: UUID,
    name: str,
    slug: str,
    topic: str,
    description: str,
    access_type: str,
    expires_at: datetime | None,
) -> Community:
    community = Community(
        id=uuid4(),
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
    )
    session.add_all([community, founder_membership])
    await session.flush()
    return community
