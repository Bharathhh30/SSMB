from collections.abc import AsyncIterator

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] | None = (
        request.app.state.database_session_factory
    )
    if session_factory is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    async with session_factory() as session:
        yield session
