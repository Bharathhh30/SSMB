from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    topic: str
    description: str
    access_type: Literal["open", "invite_only"]
    expires_at: datetime | None
    created_at: datetime


class CommunityPage(BaseModel):
    items: list[CommunityRead]
    total: int
    limit: int
    offset: int
