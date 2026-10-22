import asyncio
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.db.engine import create_database_engine
from app.features.communities.models import Community
from app.features.users.models import User

DEMO_OWNER_ID = uuid5(NAMESPACE_URL, "community-platform:development-demo-owner")
DEMO_COMMUNITIES = (
    {
        "slug": "gate-quant-lab",
        "name": "GATE Quant Lab",
        "topic": "Exam prep",
        "description": "Focused problem-solving, one small win at a time.",
        "access_type": "open",
    },
    {
        "slug": "jee-study-hall",
        "name": "JEE Study Hall",
        "topic": "Exam prep",
        "description": "A calm, consistent space for JEE preparation.",
        "access_type": "open",
    },
    {
        "slug": "react-native-makers",
        "name": "React Native Makers",
        "topic": "Technology",
        "description": "Build, share, and learn from each other.",
        "access_type": "open",
    },
    {
        "slug": "design-product-notes",
        "name": "Design + Product Notes",
        "topic": "Creative",
        "description": "Thoughtful critique for people who make things.",
        "access_type": "invite_only",
    },
    {
        "slug": "language-exchange",
        "name": "Language Exchange",
        "topic": "Languages",
        "description": "Practice a new language with friendly people.",
        "access_type": "open",
    },
)


async def seed_development_data() -> int:
    settings = get_settings()
    if settings.app_env != "development":
        raise RuntimeError("Development seed data can only be inserted when APP_ENV=development")

    engine = create_database_engine(settings.database_url)
    if engine is None:
        raise RuntimeError("DATABASE_URL must be configured before seeding")

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory.begin() as session:
            await session.execute(
                postgres_insert(User)
                .values(id=DEMO_OWNER_ID, display_name="Community Demo Owner")
                .on_conflict_do_nothing(index_elements=[User.id])
            )

            for community in DEMO_COMMUNITIES:
                statement = postgres_insert(Community).values(
                    id=uuid5(NAMESPACE_URL, f"community-platform:development:{community['slug']}"),
                    owner_id=DEMO_OWNER_ID,
                    **community,
                )
                await session.execute(
                    statement.on_conflict_do_update(
                        index_elements=[Community.id],
                        set_={
                            "name": statement.excluded.name,
                            "topic": statement.excluded.topic,
                            "description": statement.excluded.description,
                            "access_type": statement.excluded.access_type,
                        },
                    )
                )
    finally:
        await engine.dispose()

    return len(DEMO_COMMUNITIES)


if __name__ == "__main__":
    seeded = asyncio.run(seed_development_data())
    print(f"Seeded {seeded} development communities.")
