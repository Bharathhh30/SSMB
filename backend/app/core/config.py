from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Community API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: SecretStr | None = None
    auth_email_smtp_host: str | None = None
    auth_email_smtp_port: int = Field(default=1025, ge=1, le=65535)
    auth_email_smtp_username: str | None = None
    auth_email_smtp_password: SecretStr | None = None
    auth_email_smtp_starttls: bool = False
    auth_email_smtp_ssl: bool = False
    auth_email_from_address: str = "Community <noreply@example.test>"
    auth_email_timeout_seconds: int = Field(default=10, ge=1, le=60)
    auth_access_token_minutes: int = Field(default=15, ge=1, le=60)
    auth_refresh_token_days: int = Field(default=30, ge=1, le=90)
    auth_verification_token_hours: int = Field(default=24, ge=1, le=168)
    auth_password_reset_token_minutes: int = Field(default=60, ge=5, le=1440)
    auth_rate_limit_secret: SecretStr | None = None
    auth_rate_limit_window_seconds: int = Field(default=900, ge=1, le=86400)
    auth_login_attempt_limit: int = Field(default=10, ge=1, le=100)
    auth_email_action_attempt_limit: int = Field(default=5, ge=1, le=100)
    auth_ip_attempt_limit: int = Field(default=30, ge=1, le=500)

    @field_validator("database_url")
    @classmethod
    def require_async_postgres_driver(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use the postgresql+asyncpg driver")
        return value

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
