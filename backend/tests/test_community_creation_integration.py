import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.features.auth.dependencies import require_authenticated_principal
from app.features.communities.models import Community, CommunityMembership
from app.features.users.models import User
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_creator_is_persisted_as_owner_and_duplicate_names_get_unique_slugs() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        owner_id = uuid4()
        created_ids = []
        engine = create_async_engine(TEST_DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                session.add(User(id=owner_id, display_name="Community creator"))
                await session.commit()

            settings = Settings(
                app_env="test",
                database_url=SecretStr(TEST_DATABASE_URL),
            )
            app = create_app(settings)
            app.dependency_overrides[require_authenticated_principal] = lambda: SimpleNamespace(
                user=SimpleNamespace(id=owner_id)
            )

            async with app.router.lifespan_context(app):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    first = await client.post(
                        "/api/v1/communities",
                        json={
                            "name": "Study Circle",
                            "topic": "Biology",
                            "access_type": "open",
                        },
                    )
                    second = await client.post(
                        "/api/v1/communities",
                        json={
                            "name": "Study Circle",
                            "topic": "Biology",
                            "access_type": "invite_only",
                        },
                    )

            assert first.status_code == 201
            assert second.status_code == 201
            first_data = first.json()
            second_data = second.json()
            created_ids.extend([first_data["id"], second_data["id"]])
            assert first_data["slug"] == "study-circle"
            assert second_data["slug"].startswith("study-circle-")
            assert first_data["slug"] != second_data["slug"]
            assert second_data["access_type"] == "invite_only"
            assert "owner_id" not in first_data

            async with session_factory() as session:
                memberships = await session.scalars(
                    select(CommunityMembership).where(
                        CommunityMembership.community_id.in_(created_ids)
                    )
                )
                rows = list(memberships.all())
                assert len(rows) == 2
                assert all(row.user_id == owner_id for row in rows)
                assert all(row.role == "owner" for row in rows)

            with pytest.raises(IntegrityError):
                async with session_factory() as session:
                    session.add(
                        CommunityMembership(
                            community_id=created_ids[0],
                            user_id=owner_id,
                            role="member",
                        )
                    )
                    await session.flush()
        finally:
            async with session_factory() as session:
                if created_ids:
                    await session.execute(delete(Community).where(Community.id.in_(created_ids)))
                await session.execute(delete(User).where(User.id == owner_id))
                await session.commit()
            await engine.dispose()

    asyncio.run(run())
