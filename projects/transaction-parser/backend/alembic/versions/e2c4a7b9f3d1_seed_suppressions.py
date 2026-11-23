"""seed suppressions (tombstones for user-deleted seeded items)

`app.seed` is get-or-create by name and runs on every backend start. It
cannot tell "the user deleted this" from "this was never seeded", so every
restart resurrected deleted categories and keywords. This table records the
user's intent to not have an item; the seeder consults it before creating.

The backfill replays `audit_events` so deletions made *before* this table
existed are honored too. Only the audit log knows about them — the rows
themselves are long gone (category deletes cascade their keywords).

A name is suppressed only if its most recent audit event is a deletion:
delete-then-recreate must not leave a tombstone that would make the
recreated item vanish on the next restart. For categories that means
comparing the last `category.deleted` against the last `category.created`
for that name; for keywords, `keyword.removed` against `keyword.added`.
Items the user never deleted get no tombstone, so a fresh database still
seeds exactly as before.

Revision ID: e2c4a7b9f3d1
Revises: a7b8c9d0e1f2
Create Date: 2026-11-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2c4a7b9f3d1"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seed_suppressions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "name", name="uq_seed_suppressions_kind_name"),
    )

    # --- Backfill: categories whose latest audit event is a deletion -------
    op.execute(
        sa.text(
            """
            INSERT INTO seed_suppressions (kind, name)
            SELECT 'category', d.name
            FROM (
                SELECT payload->>'name' AS name, MAX(created_at) AS deleted_at
                FROM audit_events
                WHERE event_type = 'category.deleted'
                  AND payload->>'name' IS NOT NULL
                GROUP BY payload->>'name'
            ) d
            LEFT JOIN (
                SELECT payload->>'name' AS name, MAX(created_at) AS created_at
                FROM audit_events
                WHERE event_type = 'category.created'
                  AND payload->>'name' IS NOT NULL
                GROUP BY payload->>'name'
            ) c ON c.name = d.name
            WHERE c.created_at IS NULL OR c.created_at < d.deleted_at
            ON CONFLICT (kind, name) DO NOTHING
            """
        )
    )

    # --- Backfill: keywords whose latest audit event is a removal ----------
    op.execute(
        sa.text(
            """
            INSERT INTO seed_suppressions (kind, name)
            SELECT 'keyword', r.keyword
            FROM (
                SELECT UPPER(payload->>'keyword') AS keyword, MAX(created_at) AS removed_at
                FROM audit_events
                WHERE event_type = 'keyword.removed'
                  AND payload->>'keyword' IS NOT NULL
                GROUP BY UPPER(payload->>'keyword')
            ) r
            LEFT JOIN (
                SELECT UPPER(payload->>'keyword') AS keyword, MAX(created_at) AS added_at
                FROM audit_events
                WHERE event_type = 'keyword.added'
                  AND payload->>'keyword' IS NOT NULL
                GROUP BY UPPER(payload->>'keyword')
            ) a ON a.keyword = r.keyword
            WHERE a.added_at IS NULL OR a.added_at < r.removed_at
            ON CONFLICT (kind, name) DO NOTHING
            """
        )
    )

    # A keyword that currently exists must never be suppressed: the user
    # re-added it by some path the audit replay above does not capture
    # (for example the seeder recreating it, then the row being kept).
    # Same for categories. Trust present state over replayed history.
    op.execute(
        sa.text(
            """
            DELETE FROM seed_suppressions s
            WHERE s.kind = 'keyword'
              AND EXISTS (
                  SELECT 1 FROM category_keywords k WHERE UPPER(k.keyword) = s.name
              )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM seed_suppressions s
            WHERE s.kind = 'category'
              AND EXISTS (SELECT 1 FROM categories c WHERE c.name = s.name)
            """
        )
    )


def downgrade() -> None:
    op.drop_table("seed_suppressions")
