from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_PROFILE_INTERESTS = 20
MAX_INTEREST_LENGTH = 80


class ProfileRead(BaseModel):
    public_id: UUID
    display_name: str
    interests: list[str]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(
        default=None,
        max_length=80,
        description="Replace the current display name.",
    )
    interests: list[str] | None = Field(
        default=None,
        max_length=MAX_PROFILE_INTERESTS,
        description="Interests to add. Existing interests are preserved.",
    )
    remove_interests: list[str] | None = Field(
        default=None,
        max_length=MAX_PROFILE_INTERESTS,
        description="Interests to remove. Missing interests are ignored.",
    )

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name cannot be blank")
        return normalized

    @field_validator("interests", "remove_interests")
    @classmethod
    def validate_interests(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return values
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Interests cannot be blank")
        if any(len(value) > MAX_INTEREST_LENGTH for value in normalized):
            raise ValueError(f"Each interest must be at most {MAX_INTEREST_LENGTH} characters")
        folded = [value.casefold() for value in normalized]
        if len(folded) != len(set(folded)):
            raise ValueError("Interests must be unique, ignoring case")
        return normalized

    @model_validator(mode="after")
    def validate_patch_fields(self) -> "ProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one profile field must be provided")
        if "display_name" in self.model_fields_set and self.display_name is None:
            raise ValueError("Display name cannot be null")
        if "interests" in self.model_fields_set and self.interests is None:
            raise ValueError("Interests cannot be null; use an empty list for no additions")
        if "remove_interests" in self.model_fields_set and self.remove_interests is None:
            raise ValueError("remove_interests cannot be null; use an empty list for no removals")

        additions = {value.casefold() for value in self.interests or []}
        removals = {value.casefold() for value in self.remove_interests or []}
        if additions.intersection(removals):
            raise ValueError("An interest cannot be added and removed in the same request")
        return self
