from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Community API"
    app_env: Literal["development", "test", "staging", "production"] = "development"

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
