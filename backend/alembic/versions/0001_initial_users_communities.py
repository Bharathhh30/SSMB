"""Create base users and communities tables.

Revision ID: 0001_initial_users_communities
Revises:
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_users_communities"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_table(
        "communities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column(
            "description",
            sa.Text(),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("access_type", sa.String(length=20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "access_type IN ('open', 'invite_only')",
            name="ck_communities_access_type",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_communities_name_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(slug)) > 0",
            name="ck_communities_slug_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(topic)) > 0",
            name="ck_communities_topic_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_communities_owner_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_communities"),
        sa.UniqueConstraint("slug", name="uq_communities_slug"),
    )
    op.create_index("ix_communities_owner_id", "communities", ["owner_id"])
    op.create_index("ix_communities_topic", "communities", ["topic"])


def downgrade() -> None:
    op.drop_index("ix_communities_topic", table_name="communities")
    op.drop_index("ix_communities_owner_id", table_name="communities")
    op.drop_table("communities")
    op.drop_table("users")
