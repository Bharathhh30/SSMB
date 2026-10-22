from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

import app.db.models as _models  # noqa: F401
from app.db.base import Base


def test_initial_models_register_user_and_community_tables() -> None:
    assert set(Base.metadata.tables) == {
        "auth_action_tokens",
        "auth_rate_limit_buckets",
        "auth_refresh_tokens",
        "auth_sessions",
        "communities",
        "community_invites",
        "community_memberships",
        "users",
        "user_interests",
    }

    communities = Base.metadata.tables["communities"]
    assert communities.c.owner_id.foreign_keys
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_communities_slug"
        for constraint in communities.constraints
    )
    assert any(
        isinstance(index, Index) and index.name == "uq_communities_normalized_name" and index.unique
        for index in communities.indexes
    )
    assert communities.c.expires_at.nullable is True
    memberships = Base.metadata.tables["community_memberships"]
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_community_memberships_community_user"
        for constraint in memberships.constraints
    )
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_community_memberships_role"
        for constraint in memberships.constraints
    )
    invites = Base.metadata.tables["community_invites"]
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_community_invites_token_hash"
        for constraint in invites.constraints
    )
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_community_invites_not_consumed_and_revoked"
        for constraint in invites.constraints
    )
    users = Base.metadata.tables["users"]
    assert users.c.email.nullable is True
    assert users.c.password_hash.nullable is True
    assert users.c.email_verified_at.nullable is True
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_users_email"
        for constraint in users.constraints
    )


def test_unique_community_name_migration_is_the_single_head() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert script.get_heads() == ["0007_unique_community_names"]
    assert (
        script.get_revision("0004_private_user_interests").down_revision == "0003_auth_rate_limits"
    )
    assert (
        script.get_revision("0005_community_memberships").down_revision
        == "0004_private_user_interests"
    )
    assert (
        script.get_revision("0006_community_invites").down_revision == "0005_community_memberships"
    )
    assert (
        script.get_revision("0007_unique_community_names").down_revision == "0006_community_invites"
    )
