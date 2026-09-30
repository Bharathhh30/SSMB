from sqlalchemy.ext.asyncio import AsyncSession

from app.features.communities import repository
from app.features.communities.models import Community


async def get_public_community(session: AsyncSession, *, slug: str) -> Community | None:
    return await repository.get_public_community(session, slug=slug)


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
