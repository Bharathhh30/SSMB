"""Add database-backed authentication rate-limit buckets.

Revision ID: 0003_auth_rate_limits
Revises: 0002_auth_identity_sessions
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_auth_rate_limits"
down_revision: str | None = "0002_auth_identity_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_rate_limit_buckets",
        sa.Column("bucket_key_hash", sa.String(length=64), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "bucket_key_hash ~ '^[0-9a-f]{64}$'",
            name="ck_auth_rate_limit_buckets_key_hash_sha256",
        ),
        sa.CheckConstraint(
            "attempt_count > 0",
            name="ck_auth_rate_limit_buckets_attempt_count",
        ),
        sa.PrimaryKeyConstraint("bucket_key_hash", name="pk_auth_rate_limit_buckets"),
    )
    op.create_index(
        "ix_auth_rate_limit_buckets_window_started_at",
        "auth_rate_limit_buckets",
        ["window_started_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_rate_limit_buckets_window_started_at",
        table_name="auth_rate_limit_buckets",
    )
    op.drop_table("auth_rate_limit_buckets")
