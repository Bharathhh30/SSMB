"""Separate public identifiers from internal primary keys.

Revision ID: 0008_public_resource_ids
Revises: 0007_unique_community_names
Create Date: 2026-10-22
"""

import re
import unicodedata
from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "0008_public_resource_ids"
down_revision: str | None = "0007_unique_community_names"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PUBLIC_SLUG_MAX_BASE_LENGTH = 107


def upgrade() -> None:
    for table_name in ("users", "communities", "community_invites"):
        op.add_column(
            table_name,
            sa.Column(
                "public_id",
                sa.Uuid(),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
        )
        op.create_unique_constraint(
            f"uq_{table_name}_public_id",
            table_name,
            ["public_id"],
        )

    _replace_internal_id_slug_suffixes()


def downgrade() -> None:
    # Keep the rewritten slugs: reverting them would put internal primary keys
    # back into public URLs.
    for table_name in ("community_invites", "communities", "users"):
        op.drop_constraint(
            f"uq_{table_name}_public_id",
            table_name,
            type_="unique",
        )
        op.drop_column(table_name, "public_id")


def _replace_internal_id_slug_suffixes() -> None:
    connection = op.get_bind()
    communities = sa.table(
        "communities",
        sa.column("id", sa.Uuid()),
        sa.column("public_id", sa.Uuid()),
        sa.column("name", sa.String(length=120)),
        sa.column("slug", sa.String(length=140)),
    )
    rows = connection.execute(
        sa.select(
            communities.c.id,
            communities.c.public_id,
            communities.c.name,
        ).order_by(communities.c.id.asc())
    ).all()

    # The slug index is immediate. Move the old values to a temporary,
    # collision-checked namespace before assigning the new public-ID slugs.
    temporary_prefix = f"__public-id-migration-{uuid4().hex}-"
    while connection.scalar(
        sa.select(
            sa.exists().where(
                sa.func.left(communities.c.slug, len(temporary_prefix)) == temporary_prefix
            )
        )
    ):
        temporary_prefix = f"__public-id-migration-{uuid4().hex}-"

    for row in rows:
        connection.execute(
            communities.update()
            .where(communities.c.id == row.id)
            .values(slug=f"{temporary_prefix}{row.id.hex}")
        )

    for row in rows:
        new_slug = f"{_slugify(row.name)}-{row.public_id.hex}"
        connection.execute(
            communities.update().where(communities.c.id == row.id).values(slug=new_slug)
        )


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug[:PUBLIC_SLUG_MAX_BASE_LENGTH].rstrip("-") or "community"
