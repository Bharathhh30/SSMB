import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_database_url_is_kept_as_a_secret() -> None:
    database_url = "postgresql+asyncpg://user:password@localhost/community"
    settings = Settings(app_env="test", database_url=database_url)

    assert isinstance(settings.database_url, SecretStr)
    assert database_url not in repr(settings)


def test_database_url_requires_the_async_postgres_driver() -> None:
    with pytest.raises(ValidationError, match="postgresql\\+asyncpg"):
        Settings(app_env="test", database_url="postgresql://user:password@localhost/community")
