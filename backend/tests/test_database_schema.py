from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import UniqueConstraint

import app.db.models as _models  # noqa: F401
from app.db.base import Base


def test_initial_models_register_user_and_community_tables() -> None:
    assert set(Base.metadata.tables) == {"users", "communities"}

    communities = Base.metadata.tables["communities"]
    assert communities.c.owner_id.foreign_keys
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_communities_slug"
        for constraint in communities.constraints
    )
    assert communities.c.expires_at.nullable is True


def test_initial_alembic_revision_is_the_single_head() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert script.get_heads() == ["0001_initial_users_communities"]
    assert script.get_revision("0001_initial_users_communities").down_revision is None
