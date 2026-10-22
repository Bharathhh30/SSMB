"""Record community moderator role changes.

Revision ID: 0009_community_role_audit
Revises: 0008_public_resource_ids
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_community_role_audit"
down_revision: str | None = "0008_public_resource_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_role_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("community_id", sa.Uuid(), nullable=True),
        sa.Column("community_public_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_public_id", sa.Uuid(), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_public_id", sa.Uuid(), nullable=False),
        sa.Column("previous_role", sa.String(length=20), nullable=False),
        sa.Column("new_role", sa.String(length=20), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "previous_role IN ('member', 'moderator')",
            name="ck_community_role_changes_previous_role",
        ),
        sa.CheckConstraint(
            "new_role IN ('member', 'moderator')",
            name="ck_community_role_changes_new_role",
        ),
        sa.CheckConstraint(
            "previous_role <> new_role",
            name="ck_community_role_changes_role_changed",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_community_role_changes_actor_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_role_changes_community_id_communities",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            ["users.id"],
            name="fk_community_role_changes_target_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_community_role_changes"),
    )
    op.create_index(
        "ix_community_role_changes_community_changed_at",
        "community_role_changes",
        ["community_public_id", "changed_at"],
    )
    op.create_index(
        "ix_community_role_changes_target_public_id",
        "community_role_changes",
        ["target_public_id"],
    )


def downgrade() -> None:
    # Downgrading removes the role history. Production rollback must account
    # for that data loss and should normally use a forward fix instead.
    op.drop_index(
        "ix_community_role_changes_target_public_id",
        table_name="community_role_changes",
    )
    op.drop_index(
        "ix_community_role_changes_community_changed_at",
        table_name="community_role_changes",
    )
    op.drop_table("community_role_changes")
