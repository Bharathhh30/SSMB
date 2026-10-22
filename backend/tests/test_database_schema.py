from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint

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
        "community_lifecycle_events",
        "community_memberships",
        "community_ownership_changes",
        "community_role_changes",
        "users",
        "user_interests",
    }

    communities = Base.metadata.tables["communities"]
    assert communities.c.owner_id.foreign_keys
    assert communities.c.public_id.nullable is False
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_communities_public_id"
        for constraint in communities.constraints
    )
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_communities_slug"
        for constraint in communities.constraints
    )
    assert any(
        isinstance(index, Index) and index.name == "uq_communities_normalized_name" and index.unique
        for index in communities.indexes
    )
    assert communities.c.expires_at.nullable is True
    assert communities.c.archived_at.nullable is True
    assert any(index.name == "ix_communities_archived_at" for index in communities.indexes)
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
    assert invites.c.public_id.nullable is False
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_community_invites_public_id"
        for constraint in invites.constraints
    )
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
    role_changes = Base.metadata.tables["community_role_changes"]
    assert role_changes.c.community_public_id.nullable is False
    assert role_changes.c.actor_public_id.nullable is False
    assert role_changes.c.target_public_id.nullable is False
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_community_role_changes_role_changed"
        for constraint in role_changes.constraints
    )
    role_change_foreign_keys = [
        constraint
        for constraint in role_changes.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(role_change_foreign_keys) == 3
    assert all(
        {foreign_key.ondelete for foreign_key in constraint.elements} == {"SET NULL"}
        for constraint in role_change_foreign_keys
    )
    ownership_changes = Base.metadata.tables["community_ownership_changes"]
    assert ownership_changes.c.community_public_id.nullable is False
    assert ownership_changes.c.previous_owner_public_id.nullable is False
    assert ownership_changes.c.new_owner_public_id.nullable is False
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_community_ownership_changes_distinct_owners"
        for constraint in ownership_changes.constraints
    )
    owner_membership_index = next(
        index
        for index in memberships.indexes
        if index.name == "uq_community_memberships_single_owner"
    )
    assert owner_membership_index.unique is True
    assert str(owner_membership_index.dialect_options["postgresql"]["where"]) == "role = 'owner'"
    lifecycle_events = Base.metadata.tables["community_lifecycle_events"]
    assert lifecycle_events.c.community_public_id.nullable is False
    assert lifecycle_events.c.actor_public_id.nullable is False
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_community_lifecycle_events_event_type"
        for constraint in lifecycle_events.constraints
    )
    users = Base.metadata.tables["users"]
    assert users.c.public_id.nullable is False
    assert users.c.email.nullable is True
    assert users.c.password_hash.nullable is True
    assert users.c.email_verified_at.nullable is True
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_users_public_id"
        for constraint in users.constraints
    )
    assert any(
        isinstance(constraint, UniqueConstraint) and constraint.name == "uq_users_email"
        for constraint in users.constraints
    )


def test_community_archive_migration_is_the_single_head() -> None:
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert script.get_heads() == ["0011_community_archive"]
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
    assert (
        script.get_revision("0008_public_resource_ids").down_revision
        == "0007_unique_community_names"
    )
    assert (
        script.get_revision("0009_community_role_audit").down_revision == "0008_public_resource_ids"
    )
    assert (
        script.get_revision("0010_ownership_transfer").down_revision == "0009_community_role_audit"
    )
    assert script.get_revision("0011_community_archive").down_revision == "0010_ownership_transfer"
