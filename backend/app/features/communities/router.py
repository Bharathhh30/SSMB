from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.communities import service
from app.features.communities.schemas import CommunityPage

router = APIRouter(prefix="/communities", tags=["communities"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


@router.get(
    "",
    response_model=CommunityPage,
    summary="Discover communities",
)
async def get_communities(
    session: DatabaseSession,
    q: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    topic: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
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
