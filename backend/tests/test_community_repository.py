import asyncio
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.communities.repository import list_communities


def test_discovery_query_uses_public_filters_and_bound_pagination() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = 0
    rows = MagicMock()
    rows.all.return_value = []
    session.scalars.return_value = rows

    async def execute() -> None:
        await list_communities(
            session,
            query=r"gate%_",
            topic="Exam prep",
            limit=5,
            offset=10,
        )

    asyncio.run(execute())
    statement = session.scalars.await_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    parameters = list(compiled.params.values())

    assert "communities.access_type =" in compiled.string
    assert "communities.expires_at IS NULL" in compiled.string
    assert " LIMIT " in compiled.string
    assert " OFFSET " in compiled.string
    assert "open" in parameters
    assert "Exam prep" in parameters
    assert 5 in parameters
    assert 10 in parameters
    assert any(
        isinstance(value, str) and value.startswith("%gate") and r"\%" in value and r"\_" in value
        for value in parameters
    )
