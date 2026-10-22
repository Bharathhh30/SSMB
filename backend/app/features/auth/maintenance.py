from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import AuthRateLimitBucket


async def delete_expired_rate_limit_buckets(
    session: AsyncSession,
    *,
    older_than: datetime,
) -> int:
    result = await session.execute(
        delete(AuthRateLimitBucket).where(AuthRateLimitBucket.window_started_at < older_than)
    )
    await session.commit()
    return result.rowcount or 0
