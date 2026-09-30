from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_database_engine(database_url: SecretStr | None) -> AsyncEngine | None:
    if database_url is None:
        return None
    return create_async_engine(
        database_url.get_secret_value(),
        pool_pre_ping=True,
    )
