"""Add private per-user interest tags for self-service profiles.

Revision ID: 0004_private_user_interests
Revises: 0003_auth_rate_limits
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_private_user_interests"
down_revision: str | None = "0003_auth_rate_limits"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "user_interests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("interest", sa.String(length=80), nullable=False),
        sa.Column("normalized_interest", sa.String(length=240), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(interest)) > 0",
            name="ck_user_interests_interest_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(normalized_interest)) > 0",
            name="ck_user_interests_normalized_not_blank",
        ),
        sa.CheckConstraint(
            "position >= 0",
            name="ck_user_interests_position_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_interests_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_interests"),
        sa.UniqueConstraint(
            "user_id",
            "normalized_interest",
            name="uq_user_interests_user_normalized_interest",
        ),
        sa.UniqueConstraint(
            "user_id",
            "position",
            name="uq_user_interests_user_position",
        ),
    )
    op.create_index("ix_user_interests_user_id", "user_interests", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_interests_user_id", table_name="user_interests")
    op.drop_table("user_interests")
