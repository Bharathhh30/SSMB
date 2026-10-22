"""Add reversible community archive lifecycle and audit events.

Revision ID: 0011_community_archive
Revises: 0010_ownership_transfer
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_community_archive"
down_revision: str | None = "0010_ownership_transfer"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "communities",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_communities_archived_at", "communities", ["archived_at"])
    op.create_table(
        "community_lifecycle_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("community_id", sa.Uuid(), nullable=True),
        sa.Column("community_public_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_public_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('archived', 'restored')",
            name="ck_community_lifecycle_events_event_type",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_community_lifecycle_events_actor_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.id"],
            name="fk_community_lifecycle_events_community_id_communities",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_community_lifecycle_events"),
    )
    op.create_index(
        "ix_community_lifecycle_events_community_occurred_at",
        "community_lifecycle_events",
        ["community_public_id", "occurred_at"],
    )


def downgrade() -> None:
    # Downgrading removes archive history and the persisted archive state.
    op.drop_index(
        "ix_community_lifecycle_events_community_occurred_at",
        table_name="community_lifecycle_events",
    )
    op.drop_table("community_lifecycle_events")
    op.drop_index("ix_communities_archived_at", table_name="communities")
    op.drop_column("communities", "archived_at")
