"""Add community membership and founder roles.

Revision ID: 0005_community_memberships
Revises: 0004_private_user_interests
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_community_memberships"
down_revision: str | None = "0004_private_user_interests"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("community_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'moderator', 'member')",
            name="ck_community_memberships_role",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_memberships_community_id_communities",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_community_memberships_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_community_memberships"),
        sa.UniqueConstraint(
            "community_id",
            "user_id",
            name="uq_community_memberships_community_user",
        ),
    )
    op.create_index(
        "ix_community_memberships_user_id",
        "community_memberships",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_memberships_user_id", table_name="community_memberships")
    op.drop_table("community_memberships")
