from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.features.communities import service
from app.features.communities.schemas import CommunityTopicList

router = APIRouter(prefix="/topics", tags=["topics"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


@router.get(
    "",
    response_model=CommunityTopicList,
    summary="List topics with public communities",
)
async def get_community_topics(session: DatabaseSession) -> CommunityTopicList:
    return CommunityTopicList(items=await service.discoverable_topics(session))
