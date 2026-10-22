"""Audit community metadata updates and invite revocations.

Revision ID: 0012_community_admin_audit
Revises: 0011_community_archive
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_community_admin_audit"
down_revision: str | None = "0011_community_archive"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "community_invites",
        sa.Column("revoked_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_community_invites_revoked_by_user_id_users",
        "community_invites",
        "users",
        ["revoked_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "community_metadata_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("community_id", sa.Uuid(), nullable=True),
        sa.Column("community_public_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_public_id", sa.Uuid(), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_community_metadata_changes_actor_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_metadata_changes_community_id_communities",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_community_metadata_changes"),
    )
    op.create_index(
        "ix_community_metadata_changes_community_changed_at",
        "community_metadata_changes",
        ["community_public_id", "changed_at"],
    )


def downgrade() -> None:
    # Downgrading drops metadata-change history and invite revoker attribution.
    op.drop_index(
        "ix_community_metadata_changes_community_changed_at",
        table_name="community_metadata_changes",
    )
    op.drop_table("community_metadata_changes")
    op.drop_constraint(
        "fk_community_invites_revoked_by_user_id_users",
        "community_invites",
        type_="foreignkey",
    )
    op.drop_column("community_invites", "revoked_by_user_id")
