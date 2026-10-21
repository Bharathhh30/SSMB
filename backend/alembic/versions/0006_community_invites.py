"""Add secure single-use community invitations.

Revision ID: 0006_community_invites
Revises: 0005_community_memberships
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_community_invites"
down_revision: str | None = "0005_community_memberships"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("community_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_community_invites_token_hash_sha256",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_community_invites_expiry_after_creation",
        ),
        sa.CheckConstraint(
            "NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL)",
            name="ck_community_invites_not_consumed_and_revoked",
        ),
        sa.ForeignKeyConstraint(
            ["accepted_by_user_id"],
            ["users.id"],
            name="fk_community_invites_accepted_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_invites_community_id_communities",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_community_invites_created_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_community_invites"),
        sa.UniqueConstraint("token_hash", name="uq_community_invites_token_hash"),
    )
    op.create_index(
        "ix_community_invites_community_id",
        "community_invites",
        ["community_id"],
    )
    op.create_index(
        "ix_community_invites_expires_at",
        "community_invites",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_invites_expires_at", table_name="community_invites")
    op.drop_index("ix_community_invites_community_id", table_name="community_invites")
    op.drop_table("community_invites")
