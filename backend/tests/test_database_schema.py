from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import UniqueConstraint

import app.db.models as _models  # noqa: F401
from app.db.base import Base


def test_initial_models_register_user_and_community_tables() -> None:
    assert set(Base.metadata.tables) == {
        "auth_action_tokens",
        "auth_refresh_tokens",
        "auth_sessions",
        "communities",
        "users",
    }

    communities = Base.metadata.tables["communities"]
    assert communities.c.owner_id.foreign_keys
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_communities_slug"
        for constraint in communities.constraints
    )
    assert communities.c.expires_at.nullable is True
    users = Base.metadata.tables["users"]
    assert users.c.email.nullable is True
    assert users.c.password_hash.nullable is True
    assert users.c.email_verified_at.nullable is True
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_users_email"
        for constraint in users.constraints
    )


def test_authentication_migration_is_the_single_head() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert script.get_heads() == ["0002_auth_identity_sessions"]
    assert (
        script.get_revision("0002_auth_identity_sessions").down_revision
        == "0001_initial_users_communities"
    )
