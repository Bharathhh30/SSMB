"""Support audited community ownership transfer.

Revision ID: 0010_ownership_transfer
Revises: 0009_community_role_audit
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import context, op

revision: str = "0010_ownership_transfer"
down_revision: str | None = "0009_community_role_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        duplicate_owner_memberships = connection.execute(
            sa.text(
                """
                SELECT community_id
                FROM community_memberships
                WHERE role = 'owner'
                GROUP BY community_id
                HAVING COUNT(*) > 1
                """
            )
        ).all()
        if duplicate_owner_memberships:
            raise RuntimeError(
                "Cannot enforce one owner membership per community; "
                "repair duplicate owner roles before applying this migration."
            )

    op.create_index(
        "uq_community_memberships_single_owner",
        "community_memberships",
        ["community_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner'"),
    )
    op.create_table(
        "community_ownership_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("community_id", sa.Uuid(), nullable=True),
        sa.Column("community_public_id", sa.Uuid(), nullable=False),
        sa.Column("previous_owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("previous_owner_public_id", sa.Uuid(), nullable=False),
        sa.Column("new_owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("new_owner_public_id", sa.Uuid(), nullable=False),
        sa.Column(
            "transferred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "previous_owner_public_id <> new_owner_public_id",
            name="ck_community_ownership_changes_distinct_owners",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_ownership_changes_community_id_communities",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["new_owner_user_id"],
            ["users.id"],
            name="fk_community_ownership_changes_new_owner_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["previous_owner_user_id"],
            ["users.id"],
            name="fk_community_ownership_changes_previous_owner_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_community_ownership_changes"),
    )
    op.create_index(
        "ix_community_ownership_changes_community_transferred_at",
        "community_ownership_changes",
        ["community_public_id", "transferred_at"],
    )


def downgrade() -> None:
    # Downgrading removes ownership-transfer history and its invariant.
    op.drop_index(
        "ix_community_ownership_changes_community_transferred_at",
        table_name="community_ownership_changes",
    )
    op.drop_table("community_ownership_changes")
    op.drop_index(
        "uq_community_memberships_single_owner",
        table_name="community_memberships",
    )
