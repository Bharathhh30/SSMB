from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class CommunityTopicList(BaseModel):
    items: list[str]


class CommunityMembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    community_id: UUID
    role: Literal["owner", "moderator", "member"]
    joined_at: datetime


class CommunityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    topic: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=5000)
    access_type: Literal["open", "invite_only"]
    expires_at: datetime | None = None

    @field_validator("name", "topic")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank")
        return normalized

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("expires_at")
    @classmethod
    def validate_expiry(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Expiry timestamp must include a timezone")
        if value <= datetime.now(UTC):
            raise ValueError("Expiry timestamp must be in the future")
        return value
