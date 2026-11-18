"""buckets and audit_events

Introduces a real `buckets` table and drops `categories.group` (the
free-text label) in favor of a `categories.bucket_id` FK. Also adds
`audit_events`, an append-only log for the new History page.

Backfill strategy for `bucket_id`:
1. Create `buckets` (unique name index).
2. Seed one bucket per distinct `upper(coalesce(categories."group", 'OTHER'))`
   value currently in use, `ON CONFLICT DO NOTHING`, and separately make
   sure an `OTHER` bucket exists even if nothing currently uses it — it's
   the permanent undeletable fallback bucket.
3. Add a nullable `categories.bucket_id`, populate it by joining on
   `upper(coalesce("group", 'OTHER'))`, then set it NOT NULL + FK.
4. Drop `categories."group"`.
5. Create `audit_events` + an index on `created_at DESC` for the
   newest-first History feed.

Downgrade reverses this: re-adds `categories.group`, backfills it from
`buckets.name` (verbatim, i.e. uppercase — the original mixed-case
labeling, e.g. "Lifestyle", is NOT recovered since it was never stored
anywhere downstream of the forward migration), then drops `bucket_id`
and `buckets`, and drops `audit_events`.

Revision ID: d4f7a1c3e5b9
Revises: c3d8e5f1a9b2
Create Date: 2026-11-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4f7a1c3e5b9"
down_revision: Union[str, None] = "c3d8e5f1a9b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. buckets table
    op.create_table(
        "buckets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 2. backfill buckets from distinct category groups, ensure OTHER exists.
    op.execute(
        """
        INSERT INTO buckets (name, created_at, updated_at)
        SELECT DISTINCT upper(coalesce("group", 'OTHER')), now(), now()
        FROM categories
        ON CONFLICT (name) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO buckets (name, created_at, updated_at)
        VALUES ('OTHER', now(), now())
        ON CONFLICT (name) DO NOTHING
        """
    )

    # 3. categories.bucket_id: add nullable, backfill, then enforce NOT NULL + FK.
    op.add_column("categories", sa.Column("bucket_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE categories c
        SET bucket_id = b.id
        FROM buckets b
        WHERE b.name = upper(coalesce(c."group", 'OTHER'))
        """
    )
    op.alter_column("categories", "bucket_id", nullable=False)
    op.create_foreign_key(
        "fk_categories_bucket_id_buckets",
        "categories",
        "buckets",
        ["bucket_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 4. drop the old free-text group column.
    op.drop_column("categories", "group")

    # 5. audit_events table + newest-first index.
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("affected_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_created_at", "audit_events", [sa.text("created_at DESC")]
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_table("audit_events")

    op.add_column("categories", sa.Column("group", sa.String(length=64), nullable=True))
    op.execute(
        """
        UPDATE categories c
        SET "group" = b.name
        FROM buckets b
        WHERE b.id = c.bucket_id
        """
    )

    op.drop_constraint("fk_categories_bucket_id_buckets", "categories", type_="foreignkey")
    op.drop_column("categories", "bucket_id")

    op.drop_index("ix_buckets_name", table_name="buckets")
    op.drop_table("buckets")
