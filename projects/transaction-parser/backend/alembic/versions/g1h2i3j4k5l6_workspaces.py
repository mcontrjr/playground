"""workspaces: multi-tenancy for every piece of user configuration

Up to now there was exactly one implicit user. This revision makes the
tenant explicit, adopts all existing rows into a workspace named `init`,
and re-scopes every uniqueness rule that used to be global.

Order matters per table: add the column nullable, backfill it to the
adopted workspace, then set NOT NULL. Doing it in one shot would fail on
any non-empty table.

The uniqueness changes are the substantive part. `categories.name`,
`buckets.name` and `category_keywords.keyword` were globally unique, so
two workspaces could not both have a GROCERIES category. Transactions
matter most: `content_hash` is derived purely from statement contents, so
the same CSV uploaded by two workspaces hashes identically — leaving
workspace out of that constraint would make the second workspace's rows
silently dedupe away as already-ingested.

`institutions` is deliberately left global: it is a lookup table of the
six parsers the code ships with, not user configuration.

Revision ID: g1h2i3j4k5l6
Revises: e2c4a7b9f3d1
Create Date: 2026-11-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, None] = "e2c4a7b9f3d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#: Slug of the workspace existing rows are adopted into. Generic on
#: purpose — no personal handle is baked into the schema or the app.
OWNER_SLUG = "init"

#: Tables gaining a plain `workspace_id` FK, in FK-safe creation order.
#: `user_preferences` is handled separately (its primary key changes).
SCOPED_TABLES: list[str] = [
    "buckets",
    "categories",
    "category_keywords",
    "accounts",
    "ingest_batches",
    "parse_failures",
    "transactions",
    "budget_expenses",
    "clash_dismissals",
    "audit_events",
    "seed_suppressions",
]

#: Tables whose `workspace_id` gets its own index. The rest are covered
#: by the composite unique constraints created below.
INDEXED_TABLES: list[str] = [
    "buckets",
    "categories",
    "category_keywords",
    "accounts",
    "ingest_batches",
    "parse_failures",
    "transactions",
    "budget_expenses",
    "clash_dismissals",
    "seed_suppressions",
]


def upgrade() -> None:
    conn = op.get_bind()

    # --- 1. the workspaces table -------------------------------------------
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )

    # --- 2. adopt existing data -------------------------------------------
    # Created unconditionally, even on an empty database: the seeder and
    # the app both expect this workspace to exist.
    workspace_id = conn.execute(
        sa.text(
            """
            INSERT INTO workspaces (slug, name)
            VALUES (:slug, :name)
            RETURNING id
            """
        ),
        {"slug": OWNER_SLUG, "name": OWNER_SLUG},
    ).scalar_one()

    # --- 3. add + backfill + lock down the column --------------------------
    for table in SCOPED_TABLES:
        op.add_column(table, sa.Column("workspace_id", sa.Integer(), nullable=True))
        conn.execute(
            sa.text(f"UPDATE {table} SET workspace_id = :ws"),  # noqa: S608
            {"ws": workspace_id},
        )
        op.alter_column(table, "workspace_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_workspace_id",
            table,
            "workspaces",
            ["workspace_id"],
            ["id"],
            ondelete="CASCADE",
        )

    for table in INDEXED_TABLES:
        op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])

    # --- 4. user_preferences: primary key becomes (workspace_id, key) ------
    op.add_column(
        "user_preferences", sa.Column("workspace_id", sa.Integer(), nullable=True)
    )
    conn.execute(
        sa.text("UPDATE user_preferences SET workspace_id = :ws"),
        {"ws": workspace_id},
    )
    op.alter_column("user_preferences", "workspace_id", nullable=False)
    op.drop_constraint("user_preferences_pkey", "user_preferences", type_="primary")
    op.create_primary_key(
        "user_preferences_pkey", "user_preferences", ["workspace_id", "key"]
    )
    op.create_foreign_key(
        "fk_user_preferences_workspace_id",
        "user_preferences",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # --- 5. re-scope the uniqueness rules ----------------------------------
    # buckets.name / categories.name / category_keywords.keyword were
    # column-level UNIQUEs, which Postgres names <table>_<column>_key.
    op.drop_constraint("buckets_name_key", "buckets", type_="unique")
    op.create_unique_constraint(
        "uq_buckets_workspace_name", "buckets", ["workspace_id", "name"]
    )

    op.drop_constraint("categories_name_key", "categories", type_="unique")
    op.create_unique_constraint(
        "uq_categories_workspace_name", "categories", ["workspace_id", "name"]
    )

    op.drop_constraint(
        "category_keywords_keyword_key", "category_keywords", type_="unique"
    )
    op.create_unique_constraint(
        "uq_category_keywords_workspace_keyword",
        "category_keywords",
        ["workspace_id", "keyword"],
    )

    op.drop_constraint(
        "uq_accounts_institution_hint", "accounts", type_="unique"
    )
    op.create_unique_constraint(
        "uq_accounts_institution_hint",
        "accounts",
        ["workspace_id", "institution_id", "account_hint"],
    )

    op.drop_constraint(
        "uq_transactions_hash_occurrence", "transactions", type_="unique"
    )
    op.create_unique_constraint(
        "uq_transactions_hash_occurrence",
        "transactions",
        ["workspace_id", "content_hash", "occurrence_index"],
    )

    op.drop_constraint(
        "uq_seed_suppressions_kind_name", "seed_suppressions", type_="unique"
    )
    op.create_unique_constraint(
        "uq_seed_suppressions_kind_name",
        "seed_suppressions",
        ["workspace_id", "kind", "name"],
    )

    # Clash dismissals use partial unique indexes (NULL transaction_id
    # means a rule-level dismissal), so they are recreated as indexes.
    op.drop_index("uq_clash_dismissal_rule", table_name="clash_dismissals")
    op.drop_index("uq_clash_dismissal_row", table_name="clash_dismissals")
    op.create_index(
        "uq_clash_dismissal_rule",
        "clash_dismissals",
        ["workspace_id", "winner_category_id", "loser_category_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NULL"),
    )
    op.create_index(
        "uq_clash_dismissal_row",
        "clash_dismissals",
        ["workspace_id", "winner_category_id", "loser_category_id", "transaction_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NOT NULL"),
    )

    # The History page filters by workspace before ordering by recency.
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["workspace_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    # Restoring global uniqueness only succeeds if a single workspace's
    # rows remain; with two or more populated workspaces the constraints
    # below will (correctly) fail rather than discard data.
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        [sa.text("created_at DESC")],
    )

    op.drop_index("uq_clash_dismissal_rule", table_name="clash_dismissals")
    op.drop_index("uq_clash_dismissal_row", table_name="clash_dismissals")
    op.create_index(
        "uq_clash_dismissal_rule",
        "clash_dismissals",
        ["winner_category_id", "loser_category_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NULL"),
    )
    op.create_index(
        "uq_clash_dismissal_row",
        "clash_dismissals",
        ["winner_category_id", "loser_category_id", "transaction_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NOT NULL"),
    )

    op.drop_constraint(
        "uq_seed_suppressions_kind_name", "seed_suppressions", type_="unique"
    )
    op.create_unique_constraint(
        "uq_seed_suppressions_kind_name", "seed_suppressions", ["kind", "name"]
    )

    op.drop_constraint(
        "uq_transactions_hash_occurrence", "transactions", type_="unique"
    )
    op.create_unique_constraint(
        "uq_transactions_hash_occurrence",
        "transactions",
        ["content_hash", "occurrence_index"],
    )

    op.drop_constraint("uq_accounts_institution_hint", "accounts", type_="unique")
    op.create_unique_constraint(
        "uq_accounts_institution_hint", "accounts", ["institution_id", "account_hint"]
    )

    op.drop_constraint(
        "uq_category_keywords_workspace_keyword",
        "category_keywords",
        type_="unique",
    )
    op.create_unique_constraint(
        "category_keywords_keyword_key", "category_keywords", ["keyword"]
    )

    op.drop_constraint("uq_categories_workspace_name", "categories", type_="unique")
    op.create_unique_constraint("categories_name_key", "categories", ["name"])

    op.drop_constraint("uq_buckets_workspace_name", "buckets", type_="unique")
    op.create_unique_constraint("buckets_name_key", "buckets", ["name"])

    op.drop_constraint(
        "fk_user_preferences_workspace_id", "user_preferences", type_="foreignkey"
    )
    op.drop_constraint("user_preferences_pkey", "user_preferences", type_="primary")
    op.create_primary_key("user_preferences_pkey", "user_preferences", ["key"])
    op.drop_column("user_preferences", "workspace_id")

    for table in INDEXED_TABLES:
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)

    for table in reversed(SCOPED_TABLES):
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

    op.drop_table("workspaces")
