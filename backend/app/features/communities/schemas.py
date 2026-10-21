from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class CommunityDetailRead(CommunityRead):
    member_count: int = Field(
        ge=0,
        description="Current memberships, including the owner and moderators.",
    )


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


class CommunityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    topic: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=5000)
    access_type: Literal["open", "invite_only"] | None = None
    expires_at: datetime | None = None

    @field_validator("name", "topic")
    @classmethod
    def trim_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank")
        return normalized

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

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

    @model_validator(mode="after")
    def validate_patch_fields(self) -> "CommunityUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one community field must be provided")
        for field in {"name", "topic", "description", "access_type"}:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
