import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.db.engine import create_database_engine
from app.features.auth.maintenance import delete_expired_rate_limit_buckets


async def main() -> None:
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    if engine is None:
        raise RuntimeError("DATABASE_URL must be configured")

    retention_seconds = max(
        86_400,
        settings.auth_rate_limit_window_seconds * 2,
    )
    cutoff = datetime.now(UTC) - timedelta(seconds=retention_seconds)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            removed = await delete_expired_rate_limit_buckets(session, older_than=cutoff)
    finally:
        await engine.dispose()

    print(f"Removed {removed} expired authentication rate-limit buckets.")


if __name__ == "__main__":
    asyncio.run(main())
