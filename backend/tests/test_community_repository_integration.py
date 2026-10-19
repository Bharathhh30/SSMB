import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.features.communities.models import Community
from app.features.communities.repository import (
    get_public_community,
    list_communities,
    list_public_topics,
)
from app.features.users.models import User

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None and os.environ.get("CI", "").lower() != "true",
    reason="Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
def test_discovery_filters_private_and_expired_rows_and_paginates() -> None:
    assert TEST_DATABASE_URL is not None

    async def run() -> None:
        engine = create_async_engine(TEST_DATABASE_URL)
        owner_id = uuid4()
        active_ids = [uuid4(), uuid4(), uuid4()]
        expired_id = uuid4()
        private_id = uuid4()
        wildcard_id = uuid4()
        stable_ids = sorted([uuid4(), uuid4()])
        suffix = uuid4().hex
        now = datetime.now(UTC)

        try:
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                session.add(
                    User(
                        id=owner_id,
                        display_name="Repository integration test",
                    )
                )
                await session.flush()
                session.add_all(
                    [
                        Community(
                            id=active_ids[0],
                            owner_id=owner_id,
                            name=f"Community {suffix} Alpha",
                            slug=f"community-{suffix}-alpha",
                            topic="Integration",
                            description="A visible integration-test result.",
                            access_type="open",
                        ),
                        Community(
                            id=active_ids[1],
                            owner_id=owner_id,
                            name=f"Community {suffix} Beta",
                            slug=f"community-{suffix}-beta",
                            topic="Integration",
                            description="Another visible integration-test result.",
                            access_type="open",
                        ),
                        Community(
                            id=active_ids[2],
                            owner_id=owner_id,
                            name=f"Community {suffix} Gamma",
                            slug=f"community-{suffix}-gamma",
                            topic=" Integration ",
                            description="A visible result with whitespace around its topic.",
                            access_type="open",
                        ),
                        Community(
                            id=expired_id,
                            owner_id=owner_id,
                            name=f"Community {suffix} Expired",
                            slug=f"community-{suffix}-expired",
                            topic="Expired only",
                            description="This expired result must not be discoverable.",
                            access_type="open",
                            expires_at=now - timedelta(days=1),
                        ),
                        Community(
                            id=private_id,
                            owner_id=owner_id,
                            name=f"Community {suffix} Private",
                            slug=f"community-{suffix}-private",
                            topic="Invite only",
                            description="This invite-only result must not be public.",
                            access_type="invite_only",
                        ),
                        Community(
                            id=wildcard_id,
                            owner_id=owner_id,
                            name=f"Pattern 100%_ match {suffix}",
                            slug=f"pattern-{suffix}-wildcard",
                            topic="Pattern tests",
                            description="Literal wildcard characters in a searchable name.",
                            access_type="open",
                        ),
                        *[
                            Community(
                                id=community_id,
                                owner_id=owner_id,
                                name=f"Stable {suffix}",
                                slug=f"stable-{suffix}-{index}",
                                topic="Stable ordering",
                                description="Equal names must still paginate deterministically.",
                                access_type="open",
                            )
                            for index, community_id in enumerate(reversed(stable_ids))
                        ],
                    ]
                )
                await session.commit()

                try:
                    public_detail = await get_public_community(
                        session,
                        slug=f"community-{suffix}-alpha",
                    )
                    private_detail = await get_public_community(
                        session,
                        slug=f"community-{suffix}-private",
                    )
                    expired_detail = await get_public_community(
                        session,
                        slug=f"community-{suffix}-expired",
                    )
                    first_page, total = await list_communities(
                        session,
                        query=f"community {suffix}",
                        topic="Integration",
                        limit=2,
                        offset=0,
                    )
                    second_page, second_total = await list_communities(
                        session,
                        query=f"community {suffix}",
                        topic="Integration",
                        limit=1,
                        offset=2,
                    )
                    beyond_end, beyond_end_total = await list_communities(
                        session,
                        query=f"community {suffix}",
                        topic="Integration",
                        limit=1,
                        offset=99,
                    )
                    description_matches, description_total = await list_communities(
                        session,
                        query="integration-test result",
                        topic=None,
                        limit=10,
                        offset=0,
                    )
                    wildcard_matches, wildcard_total = await list_communities(
                        session,
                        query=f"100%_ match {suffix}",
                        topic="Pattern tests",
                        limit=10,
                        offset=0,
                    )
                    stable_order, stable_total = await list_communities(
                        session,
                        query=f"Stable {suffix}",
                        topic="Stable ordering",
                        limit=10,
                        offset=0,
                    )
                    topics = await list_public_topics(session)

                    assert public_detail is not None
                    assert public_detail.id == active_ids[0]
                    assert private_detail is None
                    assert expired_detail is None
                    assert total == second_total == 3
                    assert [community.id for community in first_page] == active_ids[:2]
                    assert [community.id for community in second_page] == [active_ids[2]]
                    assert beyond_end == []
                    assert beyond_end_total == 3
                    assert description_total == 2
                    assert [community.id for community in description_matches] == active_ids[:2]
                    assert wildcard_total == 1
                    assert [community.id for community in wildcard_matches] == [wildcard_id]
                    assert stable_total == 2
                    assert [community.id for community in stable_order] == stable_ids
                    assert topics == ["Integration", "Pattern tests", "Stable ordering"]
                finally:
                    await session.execute(
                        delete(Community).where(
                            Community.id.in_(
                                [
                                    *active_ids,
                                    expired_id,
                                    private_id,
                                    wildcard_id,
                                    *stable_ids,
                                ]
                            )
                        )
                    )
                    await session.execute(delete(User).where(User.id == owner_id))
                    await session.commit()
        finally:
            await engine.dispose()

    asyncio.run(run())
