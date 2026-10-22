"""Enforce unique community names after deterministic legacy repair.

Revision ID: 0007_unique_community_names
Revises: 0006_community_invites
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_unique_community_names"
down_revision: str | None = "0006_community_invites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    communities = sa.table(
        "communities",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String(length=120)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    rows = connection.execute(
        sa.select(
            communities.c.id,
            communities.c.name,
            sa.func.lower(sa.func.btrim(communities.c.name)).label("normalized_name"),
        ).order_by(communities.c.created_at.asc(), communities.c.id.asc())
    ).all()

    original_names = {row.normalized_name for row in rows}
    seen_names: set[str] = set()
    for row in rows:
        name_key = row.normalized_name
        if name_key not in seen_names:
            seen_names.add(name_key)
            continue

        base_name = row.name.strip()
        suffix_number = 2
        while True:
            suffix = f" ({suffix_number})"
            candidate = f"{base_name[: 120 - len(suffix)].rstrip()}{suffix}"
            candidate_key = _database_name_key(connection, candidate)
            if candidate_key not in seen_names and candidate_key not in original_names:
                break
            suffix_number += 1

        connection.execute(
            communities.update().where(communities.c.id == row.id).values(name=candidate)
        )
        seen_names.add(candidate_key)

    op.create_index(
        "uq_communities_normalized_name",
        "communities",
        [sa.func.lower(sa.func.btrim(sa.column("name")))],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_communities_normalized_name",
        table_name="communities",
    )


def _database_name_key(connection: sa.Connection, name: str) -> str:
    return connection.scalar(sa.select(sa.func.lower(sa.func.btrim(sa.literal(name)))))
